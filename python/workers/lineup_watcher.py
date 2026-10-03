"""
Targeted Quota-Aware Lineup Watcher Worker
Monitors upcoming eligible fixtures approaching kickoff strictly within the [T-75m, T-40m] window.
Enforces zero polling > 75m before kickoff to preserve the 45-call worker budget.
Validates official starting XI (11 vs 11) and dispatches AnalysisWorker for LINEUP_CONFIRMED / LINEUP_V2 checkpoints.

Phase 14: Durable lineup persistence via lineup_snapshots table. In-memory
_confirmed_rosters replaced by DB-backed fingerprint comparison so that worker
restarts never lose previously confirmed lineup state.
"""
import os
import sys
import json
import hashlib
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
    """Monitors upcoming matches approaching kickoff and validates official starting team sheets.

    Phase 14: Lineup state is durably persisted in the lineup_snapshots table.
    The in-memory _confirmed_rosters dict is retained as a session-level write-through
    cache to avoid redundant DB round-trips within a single worker run, but the source
    of truth is always the database.
    """

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
        # Session-level write-through cache: fixture_id -> fingerprint string.
        # Populated from DB on first access; avoids re-querying within one run.
        self._session_fingerprints: Dict[int, str] = {}
        # Backwards compatibility roster tracking: fixture_id -> set of starter player IDs
        self._confirmed_rosters: Dict[int, Set[int]] = {}

    # ------------------------------------------------------------------
    # Phase 14 — fingerprint helpers
    # ------------------------------------------------------------------

    def _compute_lineup_fingerprint(self, starter_ids: List[int]) -> str:
        """Deterministic SHA-256 fingerprint of sorted starter player IDs.

        Order-independent: [10, 20, 30] and [30, 10, 20] produce the same hash.
        """
        sorted_ids = sorted(starter_ids)
        payload = json.dumps(sorted_ids, separators=(',', ':'))
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _get_latest_lineup_snapshot(self, fixture_id: int) -> Optional[Dict[str, Any]]:
        """Fetch the most recent lineup_snapshot for this fixture from the DB.

        Returns the row dict or None when no snapshot exists or DB is unavailable.
        """
        if not self.supabase_url or not self.supabase_key:
            return None
        try:
            url = (
                f"{self.supabase_url}/rest/v1/lineup_snapshots"
                f"?fixture_id=eq.{fixture_id}&order=snapshot_version.desc&limit=1"
            )
            req = urllib.request.Request(url, headers={
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    rows = json.loads(resp.read())
                    return rows[0] if rows else None
        except Exception as e:
            logger.warning(f'Could not fetch lineup snapshot for {fixture_id}: {e}')
        return None

    def _persist_lineup_snapshot(
        self,
        fixture_id: int,
        version: int,
        fingerprint: str,
        stage: str,
        home_starters: List[Dict[str, Any]],
        away_starters: List[Dict[str, Any]],
        home_formation: Optional[str],
        away_formation: Optional[str],
        home_team_id: Optional[int],
        away_team_id: Optional[int],
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Insert a new versioned lineup snapshot row into lineup_snapshots.

        Returns True on success, False on failure (non-fatal — worker continues).
        """
        if not self.supabase_url or not self.supabase_key:
            logger.debug("No Supabase credentials; skipping lineup snapshot persistence.")
            return False
        try:
            url = f"{self.supabase_url}/rest/v1/lineup_snapshots"
            row = {
                "fixture_id": fixture_id,
                "snapshot_version": version,
                "lineup_fingerprint": fingerprint,
                "stage": stage,
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "home_formation": home_formation,
                "away_formation": away_formation,
                "home_starters": home_starters,
                "away_starters": away_starters,
                "provider_name": "api_football",
                "raw_provider_payload": raw_payload,
            }
            payload = json.dumps(row).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status in (200, 201):
                    logger.info(
                        f"Persisted lineup_snapshot fixture={fixture_id} "
                        f"version={version} stage={stage}"
                    )
                    return True
                else:
                    logger.warning(
                        f"Unexpected status {resp.status} persisting lineup_snapshot "
                        f"fixture={fixture_id}"
                    )
        except Exception as e:
            logger.warning(f"Could not persist lineup snapshot for fixture {fixture_id}: {e}")
        return False

    # ------------------------------------------------------------------
    # Phase 14 — DB-backed lineup comparison
    # ------------------------------------------------------------------

    def _resolve_lineup_stage_and_version(
        self,
        fixture_id: int,
        current_fingerprint: str,
    ) -> Tuple[str, int]:
        """Determine the snapshot stage and version number for the current lineup.

        Logic:
        1. Check session cache (fast path — avoids DB round-trip if already seen)
        2. Query DB for latest snapshot
        3. If no snapshot exists → version=1, stage=LINEUP_CONFIRMED
        4. If snapshot exists with same fingerprint → already persisted, no-op (v=existing, stage unchanged)
        5. If fingerprint differs → increment version, stage=LINEUP_V2 (or LINEUP_V3, etc.)

        Returns: (stage, version_to_write)  or  ("ALREADY_PERSISTED", -1) to signal skip.
        """
        # Fast path: session cache
        if fixture_id in self._session_fingerprints:
            prev_fp = self._session_fingerprints[fixture_id]
            if prev_fp == current_fingerprint:
                return "ALREADY_PERSISTED", -1
            # Changed within session — we already know there's at least version 1
            # Determine next version from DB
            db_row = self._get_latest_lineup_snapshot(fixture_id)
            next_version = (db_row["snapshot_version"] + 1) if db_row else 2
            stage = "LINEUP_V2" if next_version == 2 else f"LINEUP_V{next_version}"
            if stage not in ("LINEUP_CONFIRMED", "LINEUP_V2", "LINEUP_V3"):
                stage = "LINEUP_V3"  # cap at LINEUP_V3 per CHECK constraint
            return stage, next_version

        # Slow path: query DB
        db_row = self._get_latest_lineup_snapshot(fixture_id)
        if db_row is None:
            return "LINEUP_CONFIRMED", 1

        if db_row.get("lineup_fingerprint") == current_fingerprint:
            # Already persisted — update session cache and skip
            self._session_fingerprints[fixture_id] = current_fingerprint
            return "ALREADY_PERSISTED", -1

        # Fingerprint changed → revision
        next_version = db_row["snapshot_version"] + 1
        stage = "LINEUP_V2" if next_version == 2 else "LINEUP_V3"
        return stage, next_version

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
            fixture_id = f.get("id") or f.get("api_football_id")
            # Skip if already confirmed this session with no change
            if (
                f.get("lineup_confirmed")
                and fixture_id in self._session_fingerprints
            ):
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
        """Poll and verify official team sheets for fixtures within kickoff window.

        Phase 14 changes:
        - Lineup fingerprints are compared against lineup_snapshots DB table.
        - Worker restarts are idempotent: DB state is re-read on each run.
        - dry_run uses realistic-looking starters but does NOT hit DB.
        """
        logger.info(f"Starting LineupWatcherWorker (dry_run={dry_run})...")
        now = datetime.now(timezone.utc)

        # 1. Gather candidates
        match_list = fixtures or []
        if not match_list and not dry_run and self.supabase_url and self.supabase_key:
            try:
                # Query upcoming eligible unconfirmed matches from Supabase
                url = (
                    f"{self.supabase_url}/rest/v1/matches"
                    f"?is_eligible=eq.true&status=in.(NS,TBD)&lineup_confirmed=eq.false"
                    f"&select=*&limit=30"
                )
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

            parsed_lineup: Optional[Dict[str, Any]] = None
            if dry_run:
                # Synthetic lineup for dry-run verification — uses distinct player ID
                # ranges so they cannot be confused with live data
                parsed_lineup = {
                    "home": {
                        "team_id": 40,
                        "team_name": match.get("home_team_name", "Home Team"),
                        "formation": "4-3-3",
                        "starters": [
                            {"player": {"id": 9000 + i, "name": f"H_DryRun_{i}"}}
                            for i in range(11)
                        ],
                    },
                    "away": {
                        "team_id": 50,
                        "team_name": match.get("away_team_name", "Away Team"),
                        "formation": "4-2-3-1",
                        "starters": [
                            {"player": {"id": 9100 + i, "name": f"A_DryRun_{i}"}}
                            for i in range(11)
                        ],
                    },
                }
            else:
                api_requests += 1
                parsed_lineup = self.gatekeeper.fetch_match_lineup(fix_id)

            if parsed_lineup:
                # --- Phase 14: fingerprint-based durable comparison ---
                home_lineup = parsed_lineup.get("home", {})
                away_lineup = parsed_lineup.get("away", {})
                home_starters_raw = home_lineup.get("starters", [])
                away_starters_raw = away_lineup.get("starters", [])

                all_starter_ids: List[int] = []
                for p in home_starters_raw:
                    pid = p.get("player", {}).get("id")
                    if pid:
                        all_starter_ids.append(pid)
                for p in away_starters_raw:
                    pid = p.get("player", {}).get("id")
                    if pid:
                        all_starter_ids.append(pid)

                current_fp = self._compute_lineup_fingerprint(all_starter_ids)

                current_roster = set(all_starter_ids)

                if dry_run:
                    # In dry_run, check both session fingerprints and legacy _confirmed_rosters
                    prev_roster = self._confirmed_rosters.get(fix_id)
                    if prev_roster is not None and prev_roster != current_roster:
                        stage = "LINEUP_V2"
                    elif fix_id in self._session_fingerprints:
                        if self._session_fingerprints[fix_id] == current_fp:
                            stage = "ALREADY_PERSISTED"
                        else:
                            stage = "LINEUP_V2"
                    else:
                        stage = "LINEUP_CONFIRMED"
                    self._session_fingerprints[fix_id] = current_fp
                    self._confirmed_rosters[fix_id] = current_roster
                else:
                    stage, snap_version = self._resolve_lineup_stage_and_version(
                        fix_id, current_fp
                    )
                    self._confirmed_rosters[fix_id] = current_roster

                    if stage == "ALREADY_PERSISTED":
                        logger.debug(
                            f"Fixture {fix_id}: lineup unchanged (fingerprint match). Skipping."
                        )
                        continue

                    # Persist the new snapshot
                    _persisted = self._persist_lineup_snapshot(
                        fixture_id=fix_id,
                        version=snap_version,
                        fingerprint=current_fp,
                        stage=stage,
                        home_starters=home_starters_raw,
                        away_starters=away_starters_raw,
                        home_formation=home_lineup.get("formation"),
                        away_formation=away_lineup.get("formation"),
                        home_team_id=home_lineup.get("team_id"),
                        away_team_id=away_lineup.get("team_id"),
                    )

                    # Update session cache after successful persistence
                    self._session_fingerprints[fix_id] = current_fp

                    # Update matches table
                    self._mark_lineup_confirmed_in_db(fix_id, now)

                if stage == "ALREADY_PERSISTED":
                    continue

                if stage == "LINEUP_V2":
                    logger.info(
                        f"Fixture {fix_id}: Detected late change in official starters -> LINEUP_V2 snapshot."
                    )

                # Trigger AnalysisWorker for LINEUP_CONFIRMED / LINEUP_V2
                preds = self.analysis_worker.run_match_prediction(
                    match=match,
                    stage=stage,
                    lineup_data=parsed_lineup,
                    dry_run=dry_run,
                )
                predictions_generated += len(preds)
                confirmed_count += 1
                logger.info(
                    f"Fixture {fix_id}: Verified official starting XI ({stage}). "
                    f"Generated {len(preds)} predictions."
                )

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
