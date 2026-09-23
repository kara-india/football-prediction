"""
In-Play Match Live State Worker
Tracks active matches (periods '1H', 'HT', '2H', 'ET', 'LIVE'), processes state transitions,
elapsed minutes, red cards, and updates live probability snapshots using Vectorized Monte Carlo
while strictly adhering to the temporal no-lookahead invariant.
"""
import os
import sys
import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from python.simulation.match_state import MatchState
from python.simulation.vectorized_mc import VectorizedMonteCarloSimulator
from .analysis_worker import AnalysisWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("LiveStateWorker")


class LiveStateWorker:
    """Processes in-play matches and updates live probability distributions."""

    ACTIVE_STATUSES = ("1H", "HT", "2H", "ET", "BT", "P", "LIVE", "IN_PLAY")

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        simulator: Optional[VectorizedMonteCarloSimulator] = None,
        analysis_worker: Optional[AnalysisWorker] = None,
    ):
        self.supabase_url = supabase_url or os.environ.get(
            "NEXT_PUBLIC_SUPABASE_URL",
            os.environ.get("SUPABASE_URL", "https://qqcxjjkgvqknesrtnwal.supabase.co")
        )
        self.supabase_key = supabase_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
        )
        self.simulator = simulator or VectorizedMonteCarloSimulator(seed=42)
        self.analysis_worker = analysis_worker or AnalysisWorker(
            supabase_url=self.supabase_url,
            supabase_key=self.supabase_key,
        )

    def simulate_inplay_state(
        self,
        match_id: str,
        current_minute: int,
        score_home: int,
        score_away: int,
        period: str = "2H",
        red_cards_home: int = 0,
        red_cards_away: int = 0,
        added_time: int = 0,
        base_home_lambda: float = 1.45,
        base_away_lambda: float = 1.15,
    ) -> Dict[str, Any]:
        """Run vectorized Monte Carlo simulation strictly from the current in-play minute state.
        
        Strict no-lookahead invariant: future events beyond minute T are strictly unknown.
        """
        state = MatchState(
            minute=current_minute,
            added_time=added_time,
            score_home=score_home,
            score_away=score_away,
            period="second_half" if period in ("2H", "second_half") else "first_half",
            possession_home=50.0,
            shots_home=0,
            shots_away=0,
            shots_on_target_home=0,
            shots_on_target_away=0,
            xg_home=0.0,
            xg_away=0.0,
            corners_home=0,
            corners_away=0,
            fouls_home=0,
            fouls_away=0,
            yellow_cards_home=0,
            yellow_cards_away=0,
            red_cards_home=red_cards_home,
            red_cards_away=red_cards_away,
            offsides_home=0,
            offsides_away=0,
            substitutions_home=0,
            substitutions_away=0,
            is_live=True,
            lineup_confirmed=True,
        )

        _, dist = self.simulator.simulate_with_convergence(
            state=state,
            home_lambda_per_min=base_home_lambda / 90.0,
            away_lambda_per_min=base_away_lambda / 90.0,
            min_simulations=10_000,
        )

        return {
            "match_id": match_id,
            "minute": current_minute,
            "period": period,
            "score_home": score_home,
            "score_away": score_away,
            "red_cards_home": red_cards_home,
            "red_cards_away": red_cards_away,
            "probabilities_1x2": dist.get("1x2", {}),
            "probabilities_ou25": dist.get("over_under_25", {}),
            "probabilities_btts": dist.get("btts", {}),
            "std_error": dist.get("std_error", 0.0),
        }

    def run(
        self,
        active_matches: Optional[List[Dict[str, Any]]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Poll and re-simulate active in-play matches."""
        logger.info(f"Starting LiveStateWorker execution (dry_run={dry_run})...")

        matches_to_process = active_matches or []

        # If no active matches provided and not dry_run, query Supabase
        if not matches_to_process and not dry_run and self.supabase_url and self.supabase_key:
            try:
                url = f"{self.supabase_url}/rest/v1/matches?status=in.('1H','HT','2H','ET','LIVE')&select=*&limit=20"
                req = urllib.request.Request(
                    url,
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                    },
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        matches_to_process = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                logger.warning(f"Could not load live matches from DB: {e}")

        # In dry run mode, synthesize an active match if none provided
        if not matches_to_process and dry_run:
            matches_to_process = [{
                "id": "dry_run_live_1",
                "minute": 65,
                "score_home": 1,
                "score_away": 1,
                "period": "2H",
                "red_cards_home": 0,
                "red_cards_away": 1,
            }]

        live_snapshots: List[Dict[str, Any]] = []
        for m in matches_to_process:
            m_id = str(m.get("id", m.get("match_id", "live_0")))
            minute = int(m.get("minute", 0))
            score_h = int(m.get("score_home", 0))
            score_a = int(m.get("score_away", 0))
            period = str(m.get("period", "2H"))
            red_h = int(m.get("red_cards_home", 0))
            red_a = int(m.get("red_cards_away", 0))

            snapshot = self.simulate_inplay_state(
                match_id=m_id,
                current_minute=minute,
                score_home=score_h,
                score_away=score_a,
                period=period,
                red_cards_home=red_h,
                red_cards_away=red_a,
            )
            live_snapshots.append(snapshot)

            # Persist live checkpoint snapshot through AnalysisWorker if needed
            if not dry_run:
                self.analysis_worker.generate_forecasts(
                    match_id=m_id,
                    competition="In-Play Competition",
                    stage="LIVE",
                    home_rate=1.45,
                    away_rate=1.15,
                    lineup_confirmed=True,
                    dry_run=False,
                )

        logger.info(f"LiveStateWorker completed: updated {len(live_snapshots)} in-play match snapshots.")
        return {
            "status": "success",
            "matches_processed": len(matches_to_process),
            "snapshots_generated": len(live_snapshots),
            "errors": [],
        }


def run_live_worker(dry_run: bool = False) -> Dict[str, Any]:
    """CLI / runner entrypoint for live state worker."""
    worker = LiveStateWorker()
    return worker.run(dry_run=dry_run)


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    res = run_live_worker(dry_run=is_dry)
    logger.info(f"Live worker finished: {res}")
    sys.exit(0)
