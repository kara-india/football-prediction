"""
Data Retention Pruner & Storage Governor
Enforces free-tier storage limits (< 500 MB) by safely pruning transient logs
while strictly defending inviolable analytical tables.
"""
import os
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Set, List

logger = logging.getLogger("RetentionPruner")

# Tables strictly protected by inviolable retention guarantee
PROTECTED_TABLES: Set[str] = frozenset({
    "matches",
    "lineups",
    "odds_snapshots",
    "model_predictions",
    "prediction_results",
    "prediction_errors",
    "paper_bets",
    "paper_bet_settlements",
    "model_metrics",
    "competitions",
    "teams",
    "players",
    "market_definitions",
    "market_outcomes",
    "model_versions",
    "calibration_versions",
    "calibration_bins",
    "feature_snapshots",
})

# Transient pruning configuration defaults
DEFAULT_RETENTION_POLICIES = [
    {
        "table": "match_event_ticks",
        "timestamp_col": "created_at",
        "days_to_keep": 14,
    },
    {
        "table": "raw_provider_payloads",
        "timestamp_col": "created_at",
        "days_to_keep": 7,
    },
    {
        "table": "worker_runs",
        "timestamp_col": "started_at",
        "days_to_keep": 30,
    },
]


class RetentionPruner:
    """
    Automated data retention pruner enforcing Supabase storage quotas.
    Safely purges transient event ticks, raw API payloads, and old worker telemetry
    while strictly protecting analytical forecasts, odds, and paper bets.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ):
        self.supabase_url = supabase_url or os.environ.get(
            "NEXT_PUBLIC_SUPABASE_URL",
            os.environ.get("SUPABASE_URL", "https://qqcxjjkgvqknesrtnwal.supabase.co"),
        )
        self.supabase_key = supabase_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", ""),
        )

    def validate_table_safety(self, table_name: str) -> None:
        """
        Verify table is safe to prune.
        Raises ValueError if attempting to prune any inviolable/protected table.
        """
        norm_name = table_name.lower().strip()
        if norm_name in PROTECTED_TABLES:
            raise ValueError(
                f"Attempted to prune protected table '{table_name}'. "
                "INVIOLABLE RETENTION POLICY VIOLATION: matches, predictions, odds, "
                "settlements, and core model records cannot be deleted."
            )

    def prune_table(
        self,
        table_name: str,
        timestamp_col: str,
        days_to_keep: int,
        dry_run: bool = False,
    ) -> int:
        """
        Prune rows older than days_to_keep from a single table.
        In dry_run mode, returns count of eligible rows without deleting.
        """
        # Safety gate check
        self.validate_table_safety(table_name)

        cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        cutoff_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

        if not self.supabase_url or not self.supabase_key:
            logger.info(
                f"[{'DRY-RUN' if dry_run else 'EXECUTE'}] Mock prune on {table_name}: "
                f"older than {days_to_keep}d (cutoff: {cutoff_iso})"
            )
            return 0

        # Query Supabase via PostgREST
        try:
            if dry_run:
                # SELECT count only
                url = (
                    f"{self.supabase_url}/rest/v1/{table_name}"
                    f"?{timestamp_col}=lt.{cutoff_iso}&select=id"
                )
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Range-Unit": "items",
                    "Range": "0-0",
                    "Prefer": "count=exact",
                }
                req = urllib.request.Request(url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content_range = resp.headers.get("Content-Range")
                    if content_range and "/" in content_range:
                        total_str = content_range.split("/")[1]
                        return int(total_str) if total_str.isdigit() else 0
                    return 0
            else:
                # DELETE execution
                url = (
                    f"{self.supabase_url}/rest/v1/{table_name}"
                    f"?{timestamp_col}=lt.{cutoff_iso}"
                )
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Prefer": "count=exact",
                }
                req = urllib.request.Request(url, headers=headers, method="DELETE")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content_range = resp.headers.get("Content-Range")
                    if content_range and "/" in content_range:
                        total_str = content_range.split("/")[1]
                        deleted_count = int(total_str) if total_str.isdigit() else 0
                        logger.info(f"Pruned {deleted_count} rows from {table_name} (< {cutoff_iso})")
                        return deleted_count
                    return 0

        except urllib.error.HTTPError as err:
            if err.code in (404, 400):
                # Table might not exist or schema differs; log and continue safely
                logger.debug(f"Table {table_name} skipped during pruning: HTTP {err.code}")
                return 0
            logger.warning(f"Error querying/pruning table {table_name}: {err}")
            return 0
        except Exception as e:
            logger.warning(f"Unexpected error pruning {table_name}: {e}")
            return 0

    def run(
        self,
        dry_run: bool = False,
        policies: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute full retention pruning cycle across all transient tables.
        """
        policies = policies or DEFAULT_RETENTION_POLICIES
        started_at = datetime.now(timezone.utc)
        pruned_counts: Dict[str, int] = {}
        total_pruned = 0

        logger.info(
            f"Starting Data Retention Pruning cycle ({'DRY-RUN' if dry_run else 'ACTIVE PRUNE'})..."
        )

        for pol in policies:
            tbl = pol["table"]
            col = pol.get("timestamp_col", "created_at")
            days = pol.get("days_to_keep", 14)

            # Defensive safety check before dispatching
            self.validate_table_safety(tbl)

            count = self.prune_table(
                table_name=tbl,
                timestamp_col=col,
                days_to_keep=days,
                dry_run=dry_run,
            )
            pruned_counts[tbl] = count
            total_pruned += count

        duration = (datetime.now(timezone.utc) - started_at).total_seconds()
        logger.info(
            f"Retention Pruning finished in {duration:.2f}s. "
            f"Eligible/Deleted rows: {pruned_counts} (total: {total_pruned})"
        )

        return {
            "status": "success",
            "worker_name": "prune",
            "dry_run": dry_run,
            "pruned_counts": pruned_counts,
            "total_pruned": total_pruned,
            "duration_seconds": round(duration, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def run_retention_pruner(dry_run: bool = False) -> Dict[str, Any]:
    """Convenience entrypoint for executing retention pruner."""
    pruner = RetentionPruner()
    return pruner.run(dry_run=dry_run)
