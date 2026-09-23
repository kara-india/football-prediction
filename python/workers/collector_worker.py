"""
Background Collector Worker
Discovers upcoming fixtures for allowed competitions within the quota boundary (strictly 1 credit/day),
inserts them into Supabase matches, and triggers INITIAL (T-48h) checkpoint forecasts.
"""
import os
import sys
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from ..adapters.quota_manager import CentralQuotaManager, QuotaExceededError
from ..adapters.api_football import APIFootballAdapter
from ..ingestion.fixture_discovery import FixtureDiscoveryEngine
from ..data_contracts import CanonicalMatch
from .analysis_worker import AnalysisWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CollectorWorker")


class CollectorWorker:
    """Discovers upcoming matches and initializes baseline forecasts."""

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
        self.discovery_engine = FixtureDiscoveryEngine(api_adapter=self.api, quota_manager=self.quota_manager)
        self.analysis_worker = analysis_worker or AnalysisWorker(
            supabase_url=self.supabase_url,
            supabase_key=self.supabase_key
        )

    def _persist_matches_to_supabase(self, matches: List[CanonicalMatch]) -> int:
        """Insert or update discovered fixtures in Supabase matches table."""
        if not self.supabase_url or not self.supabase_key or not matches:
            return 0

        try:
            url = f"{self.supabase_url}/rest/v1/matches"
            rows = []
            for m in matches:
                rows.append({
                    "api_football_id": m.provider_fixture_id,
                    "competition_id": m.competition_id,
                    "season": m.season,
                    "round": m.round,
                    "kickoff_utc": m.kickoff_utc.isoformat(),
                    "status": m.status,
                    "status_short": m.status,
                    "is_eligible": m.is_eligible,
                    "lineup_confirmed": False,
                })

            payload = json.dumps(rows).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates,return=minimal",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 201):
                    logger.info(f"Upserted {len(rows)} fixtures into Supabase matches.")
                    return len(rows)
        except Exception as e:
            logger.warning(f"Could not persist fixtures to Supabase: {e}")

        return 0

    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """Execute daily fixture discovery under quota governance."""
        logger.info(f"Starting CollectorWorker execution (dry_run={dry_run})...")

        if dry_run:
            logger.info("Dry-run mode active. Simulating discovery without consuming external quota or writing DB.")
            # Synthesize 1 mock fixture for dry-run verification
            now = datetime.now(timezone.utc)
            mock_match = CanonicalMatch(
                match_id="dry_run_match_1001",
                provider_id="api-football",
                provider_fixture_id=1001,
                competition_id=39,
                competition_name="Premier League (England)",
                season=2024,
                round="Regular Season - 10",
                kickoff_utc=now + timedelta(hours=24),
                venue_name="Emirates Stadium",
                referee="Michael Oliver",
                home_team_id=42,
                home_team_name="Arsenal",
                away_team_id=49,
                away_team_name="Chelsea",
                status="NS",
                is_eligible=True,
                source_timestamp=now,
                available_at=now,
            )
            preds = self.analysis_worker.run_match_prediction(mock_match, stage="INITIAL", dry_run=True)
            return {
                "status": "success",
                "matches_seen": 1,
                "matches_inserted": 1,
                "quota_used": 0,
                "predictions_count": len(preds),
                "errors": [],
            }

        # Live discovery strictly using 1 quota credit
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        try:
            matches = self.discovery_engine.discover_fixtures_for_date(today_utc)
            logger.info(f"Discovered {len(matches)} eligible fixtures for {today_utc}.")
        except QuotaExceededError as qe:
            logger.warning(f"Quota exceeded during fixture discovery: {qe}")
            return {
                "status": "failed",
                "matches_seen": 0,
                "matches_inserted": 0,
                "quota_used": 0,
                "predictions_count": 0,
                "errors": [str(qe)],
            }
        except Exception as e:
            logger.error(f"Collector worker discovery failed: {e}")
            return {
                "status": "failed",
                "matches_seen": 0,
                "matches_inserted": 0,
                "quota_used": 0,
                "predictions_count": 0,
                "errors": [str(e)],
            }

        inserted_count = self._persist_matches_to_supabase(matches)

        # Generate INITIAL forecast checkpoint (T-48h) for each fixture
        total_predictions = 0
        for match in matches:
            preds = self.analysis_worker.run_match_prediction(match, stage="INITIAL", dry_run=False)
            total_predictions += len(preds)

        return {
            "status": "success",
            "matches_seen": len(matches),
            "matches_inserted": inserted_count,
            "quota_used": 1,
            "predictions_count": total_predictions,
            "errors": [],
        }


def run_collector_worker(dry_run: bool = False) -> Dict[str, Any]:
    """CLI / runner entrypoint for collector worker."""
    worker = CollectorWorker()
    return worker.run(dry_run=dry_run)


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    result = run_collector_worker(dry_run=is_dry)
    logger.info(f"Collector worker completed with result: {result}")
    sys.exit(0 if result.get("status") == "success" else 1)
