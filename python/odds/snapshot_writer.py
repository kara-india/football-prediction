"""
Odds Snapshot Persistence Writer
Batches and serializes verified odds snapshots into Supabase `odds_snapshots`
with deduplication and composite identity preservation.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.error

from ..data_contracts import CanonicalOddsMarket

logger = logging.getLogger("OddsSnapshotWriter")


class OddsSnapshotWriter:
    """Manages persistent logging of odds snapshots into Supabase."""

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.supabase_url = supabase_url or os.environ.get(
            "NEXT_PUBLIC_SUPABASE_URL",
            "https://qqcxjjkgvqknesrtnwal.supabase.co"
        )
        self.supabase_key = supabase_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
        )
        self._last_written_cache: Dict[str, Tuple[float, datetime]] = {}

    def serialize_market(self, market: CanonicalOddsMarket) -> List[Dict[str, Any]]:
        """Serialize a CanonicalOddsMarket into individual database row payloads."""
        rows = []
        now_iso = datetime.now(timezone.utc).isoformat()
        src_iso = market.source_timestamp.isoformat()

        # Parse numeric match_id if applicable
        raw_mid = market.match_id
        if raw_mid.startswith("api_football_"):
            try:
                numeric_match_id = int(raw_mid.replace("api_football_", ""))
            except ValueError:
                numeric_match_id = abs(hash(raw_mid)) % (10**8)
        else:
            try:
                numeric_match_id = int(raw_mid)
            except ValueError:
                numeric_match_id = abs(hash(raw_mid)) % (10**8)

        for sel in market.selections:
            cache_key = f"{market.match_id}_{market.bookmaker}_{market.canonical_market}_{sel.selection}_{sel.line}"

            # Deduplication: if exact odds price was logged in past 60s, skip duplicate insertion
            if cache_key in self._last_written_cache:
                last_price, last_time = self._last_written_cache[cache_key]
                if last_price == sel.decimal_odds and (datetime.now(timezone.utc) - last_time).total_seconds() < 60:
                    continue

            row = {
                "match_id": numeric_match_id,
                "provider": market.bookmaker,
                "canonical_market": market.canonical_market,
                "period": market.period,
                "selection": sel.selection,
                "line": sel.line,
                "decimal_odds": sel.decimal_odds,
                "implied_prob": round(sel.implied_prob, 5),
                "devigged_prob": round(sel.devigged_prob, 5) if sel.devigged_prob is not None else None,
                "market_margin": round(market.market_margin, 5),
                "is_live": market.is_live,
                "is_suspended": sel.is_suspended,
                "source_timestamp": src_iso,
                "fetched_at": now_iso,
            }
            rows.append(row)
            self._last_written_cache[cache_key] = (sel.decimal_odds, datetime.now(timezone.utc))

        return rows

    def write_snapshots(self, markets: List[CanonicalOddsMarket]) -> int:
        """Serialize and insert odds market snapshots into Supabase."""
        all_rows = []
        for m in markets:
            all_rows.extend(self.serialize_market(m))

        if not all_rows:
            return 0

        if not self.supabase_url or not self.supabase_key:
            logger.debug("Supabase not configured for snapshot writing; dry-run complete.")
            return len(all_rows)

        try:
            url = f"{self.supabase_url}/rest/v1/odds_snapshots"
            payload = json.dumps(all_rows).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201):
                    logger.info(f"Successfully recorded {len(all_rows)} odds snapshots.")
                    return len(all_rows)
        except Exception as e:
            logger.warning(f"Could not persist odds snapshots to Supabase: {e}")

        return len(all_rows)
