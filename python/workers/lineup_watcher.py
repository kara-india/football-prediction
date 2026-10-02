"""
Targeted Quota-Aware Lineup Watcher Worker
Monitors upcoming eligible fixtures approaching kickoff strictly within the [T-75m, T-40m] window.
Enforces zero polling > 75m before kickoff to preserve the 45-call worker budget.
Validates official starting XI (11 vs 11) and dispatches AnalysisWorker for LINEUP_CONFIRMED / LINEUP_V2 checkpoints.
"""
import os
import sys
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set

from ..adapters.quota_manager import CentralQuotaManager, QuotaExceededError
from ..adapters.api_football import APIFootballAdapter
from .lineup_gatekeeper import LineupGatekeeperWorker
from .analysis_worker import AnalysisWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("LineupWatcher")


class LineupWatcherWorker:
    """Monitors upcoming matches approaching kickoff and validates official starting team sheets."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        api_adapter: Optional[APIFootballAdapter] = None,
        quota_manager: Optional[CentralQuotaManager] = None,
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
        self.quota_manager = quota_manager or CentralQuotaManager()
        self.api = api_adapter or APIFootballAdapter(quota_manager=self.quota_manager)
        self.gatekeeper = LineupGatekeeperWorker(
            supabase_url=self.supabase_url,
            supabase_key=self.supabase_key,
            api_adapter=self.api,
            quota_manager=self.quota_manager,
        )
        self.analysis_worker = analysis_worker or AnalysisWorker(
            supabase_url=self.supabase_url,
            supabase_key=self.supabase_key,
        )
        # In-memory tracking of confirmed rosters: fixture_id -> set of starter player IDs
        self._confirmed_rosters: Dict[int, Set[int]] = {}

    def filter_target_window_matches(
        self,
        fixtures: List[Dict[str, Any]],
        now_utc: Optional[datetime] = None,
        min_window_minutes: int = 40,
        max_window_minutes: int = 75,
    ) -> List[Dict[str, Any]]:
        """Filter matches strictly within [T-75m, T-40m] relative to current time.
        
        Zero polling > 75m before kickoff is strictly enforced.
        """
        now = now_utc or datetime.now(timezone.utc)
        earliest_kickoff = now + timedelta(minutes=min_window_minutes)
        latest_kickoff = now + timedelta(minutes=max_window_minutes)

        candidates = []
        for f in fixtures:
            # Skip if already confirmed and no recheck needed
            fixture_id = f.get("id") or f.get("api_football_id")
            if f.get("lineup_confirmed") and fixture_id in self._confirmed_rosters:
                continue

            kickoff_raw = f.get("kickoff_utc")
            if not kickoff_raw:
                continue

            if isinstance(kickoff_raw, str):
                try:
                    kickoff = datetime.fromisoformat(kickoff_raw.replace("Z", "+00:00"))
                except ValueError:
                    continue
            elif isinstance(kickoff_raw, datetime):
                kickoff = kickoff_raw
            else:
                continue

            # Strict window enforcement: T-75m to T-40m
            if earliest_kickoff <= kickoff <= latest_kickoff:
                candidates.append(f)
            elif kickoff > latest_kickoff:
                logger.debug(f"Fixture {fixture_id} is > 75m to kickoff. Zero polling enforced.")

        return candidates

    def _mark_lineup_confirmed_in_db(self, fixture_id: int, confirmed_at: datetime) -> None:
        """Update matches table setting lineup_confirmed=True and lineup_confirmed_at."""
        if not self.supabase_url or not self.supabase_key:
            return

        try:
            url = f"{self.supabase_url}/rest/v1/matches?api_football_id=eq.{fixture_id}"
            payload = json.dumps({
                "lineup_confirmed": True,
                "lineup_confirmed_at": confirmed_at.isoformat(),
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                method="PATCH",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 204):
                    logger.debug(f"Updated DB lineup status for fixture {fixture_id}.")
        except Exception as e:
            logger.warning(f"Failed to update lineup confirmation in DB: {e}")

    def run(
        self,
        fixtures: Optional[List[Dict[str, Any]]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Poll and verify official team sheets for fixtures within kickoff window."""
        logger.info(f"Starting LineupWatcherWorker (dry_run={dry_run})...")
        now = datetime.now(timezone.utc)

        # 1. Gather candidates
        match_list = fixtures or []
        if not match_list and not dry_run and self.supabase_url and self.supabase_key:
            try:
                # Query upcoming eligible unconfirmed matches from Supabase
                url = f"{self.supabase_url}/rest/v1/matches?is_eligible=eq.true&status=in.(NS,TBD)&lineup_confirmed=eq.false&select=*&limit=30"
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
                        match_list = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                logger.warning(f"Could not load upcoming matches for lineup monitoring: {e}")

        # In dry run mode, provide a synthetic match in window for verification
        if not match_list and dry_run:
            match_list = [{
                "id": 501,
                "api_football_id": 501,
                "competition_name": "Premier League (England)",
                "home_team_name": "Liverpool",
                "away_team_name": "Everton",
                "kickoff_utc": (now + timedelta(minutes=60)).isoformat(),
                "lineup_confirmed": False,
            }]

        target_matches = self.filter_target_window_matches(match_list, now_utc=now)
        logger.info(f"Found {len(target_matches)} candidate fixtures within [T-75m, T-40m] window.")

        confirmed_count = 0
        predictions_generated = 0
        api_requests = 0

        for match in target_matches:
            fix_id = match.get("api_football_id") or match.get("id")
            if not fix_id:
                continue

            parsed_lineup = None
            if dry_run:
                # Synthetic 11 vs 11 lineup for dry-run verification
                parsed_lineup = {
                    "home": {
                        "team_id": 40,
                        "team_name": match.get("home_team_name", "Home Team"),
                        "formation": "4-3-3",
                        "starters": [{"player": {"id": 100 + i, "name": f"H_Player_{i}"}} for i in range(11)],
                    },
                    "away": {
                        "team_id": 50,
                        "team_name": match.get("away_team_name", "Away Team"),
                        "formation": "4-2-3-1",
                        "starters": [{"player": {"id": 200 + i, "name": f"A_Player_{i}"}} for i in range(11)],
                    },
                }
            else:
                api_requests += 1
                parsed_lineup = self.gatekeeper.fetch_match_lineup(fix_id)

            if parsed_lineup:
                # Extract set of starter IDs
                current_starters = set()
                for p in parsed_lineup.get("home", {}).get("starters", []):
                    pid = p.get("player", {}).get("id")
                    if pid:
                        current_starters.add(pid)
                for p in parsed_lineup.get("away", {}).get("starters", []):
                    pid = p.get("player", {}).get("id")
                    if pid:
                        current_starters.add(pid)

                # Determine if this is LINEUP_CONFIRMED or late change LINEUP_V2
                is_revision = False
                if fix_id in self._confirmed_rosters:
                    prev_starters = self._confirmed_rosters[fix_id]
                    if prev_starters != current_starters:
                        is_revision = True
                        logger.info(f"Fixture {fix_id}: Detected late change in official starters -> LINEUP_V2 snapshot.")

                stage = "LINEUP_V2" if is_revision else "LINEUP_CONFIRMED"
                self._confirmed_rosters[fix_id] = current_starters

                # Update database
                if not dry_run:
                    self._mark_lineup_confirmed_in_db(fix_id, now)

                # Trigger AnalysisWorker for LINEUP_CONFIRMED / LINEUP_V2
                preds = self.analysis_worker.run_match_prediction(
                    match=match,
                    stage=stage,
                    lineup_data=parsed_lineup,
                    dry_run=dry_run,
                )
                predictions_generated += len(preds)
                confirmed_count += 1
                logger.info(f"Fixture {fix_id}: Verified official starting XI ({stage}). Generated {len(preds)} predictions.")

        return {
            "status": "success",
            "matches_seen": len(match_list),
            "matches_in_window": len(target_matches),
            "lineups_confirmed": confirmed_count,
            "predictions_count": predictions_generated,
            "api_requests": api_requests,
            "errors": [],
        }


def run_lineup_watcher(dry_run: bool = False) -> Dict[str, Any]:
    """CLI / runner entrypoint for lineup watcher."""
    worker = LineupWatcherWorker()
    return worker.run(dry_run=dry_run)


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    res = run_lineup_watcher(dry_run=is_dry)
    logger.info(f"Lineup watcher finished: {res}")
    sys.exit(0)
