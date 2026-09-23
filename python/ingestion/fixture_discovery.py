"""
Bulk Daily Fixture Discovery Engine
Consumes exactly 1 API-Football request per day to discover upcoming fixtures
across allowed competitions, strictly respecting the ₹0.00 cost governance.
"""
import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .quality_scorer import MatchQualityScorer
from ..data_contracts import CanonicalMatch
from ..adapters.quota_manager import CentralQuotaManager, QuotaExceededError
from ..adapters.api_football import APIFootballAdapter

logger = logging.getLogger("FixtureDiscovery")

# Allowed Competitions Registry (Top European & International Tier 1)
ALLOWED_LEAGUES = {
    39: "Premier League (England)",
    71: "Serie A (Brazil)",
    135: "Serie A (Italy)",
    140: "La Liga (Spain)",
    78: "Bundesliga (Germany)",
    61: "Ligue 1 (France)",
    94: "Primeira Liga (Portugal)",
    88: "Eredivisie (Netherlands)",
    128: "Liga Profesional (Argentina)",
    144: "First Division A (Belgium)",
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    1: "FIFA World Cup",
    4: "UEFA European Championship",
    5: "UEFA Nations League",
    9: "Copa America",
    6: "Africa Cup of Nations",
    7: "AFC Asian Cup",
    10: "Friendlies (Senior Men)",
}

EXCLUDED_KEYWORDS = re.compile(
    r"\b(U17|U18|U19|U20|U21|U23|Youth|Women|Fem|W|Reserves|Cup|Trophy)\b",
    re.IGNORECASE
)


class FixtureDiscoveryEngine:
    """Discovers upcoming matches using strictly 1 API call per 24-hour cycle."""

    def __init__(
        self,
        api_adapter: Optional[APIFootballAdapter] = None,
        quota_manager: Optional[CentralQuotaManager] = None
    ):
        self.quota_manager = quota_manager or CentralQuotaManager()
        self.api = api_adapter or APIFootballAdapter(quota_manager=self.quota_manager)

    @classmethod
    def is_eligible_fixture(cls, fixture_data: Dict[str, Any]) -> bool:
        """Check if fixture belongs to allowed competitions and is senior men's."""
        league_id = fixture_data.get("league", {}).get("id")
        if league_id not in ALLOWED_LEAGUES:
            return False

        home_name = fixture_data.get("teams", {}).get("home", {}).get("name", "")
        away_name = fixture_data.get("teams", {}).get("away", {}).get("name", "")
        league_name = fixture_data.get("league", {}).get("name", "")

        # Exclude youth, women, and reserve teams
        if (
            EXCLUDED_KEYWORDS.search(home_name) or
            EXCLUDED_KEYWORDS.search(away_name) or
            EXCLUDED_KEYWORDS.search(league_name)
        ):
            return False

        return True

    def discover_fixtures_for_date(self, target_date: str) -> List[CanonicalMatch]:
        """Fetch fixtures for a specific date (YYYY-MM-DD), consuming exactly 1 credit.

        Args:
            target_date: Date string formatted as YYYY-MM-DD.

        Returns:
            List of normalized CanonicalMatch objects capped at top 50 matches.
        """
        # Execute exactly 1 automated request through the quota governor
        try:
            # Note: _make_request will call quota_manager.reserve(is_user=False, cost=1)
            raw_fixtures = self.api._make_request("fixtures", {"date": target_date}, ttl=1800, is_user=False)
        except QuotaExceededError as qe:
            logger.warning(f"Fixture discovery aborted due to quota limit: {qe}")
            return []

        if not isinstance(raw_fixtures, list):
            return []

        # Filter by eligibility and status
        eligible_raw = [
            f for f in raw_fixtures
            if self.is_eligible_fixture(f) and f.get("fixture", {}).get("status", {}).get("short") in ("NS", "TBD")
        ]

        # Cap to top 50 matches max per user constraint
        selected = eligible_raw[:50]
        now = datetime.now(timezone.utc)
        canonical_matches: List[CanonicalMatch] = []

        for f in selected:
            fix = f.get("fixture", {})
            league = f.get("league", {})
            teams = f.get("teams", {})

            fixture_id = fix.get("id")
            kickoff_str = fix.get("date")
            try:
                kickoff_utc = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                kickoff_utc = now

            home_id = teams.get("home", {}).get("id", 0)
            home_name = teams.get("home", {}).get("name", "Unknown Home")
            away_id = teams.get("away", {}).get("id", 0)
            away_name = teams.get("away", {}).get("name", "Unknown Away")

            match_id = f"api_football_{fixture_id}"

            canonical_matches.append(
                CanonicalMatch(
                    match_id=match_id,
                    provider_id="api-football",
                    provider_fixture_id=fixture_id,
                    competition_id=league.get("id", 0),
                    competition_name=league.get("name", "Unknown"),
                    season=league.get("season", kickoff_utc.year),
                    round=league.get("round", "Regular Season"),
                    kickoff_utc=kickoff_utc,
                    venue_name=fix.get("venue", {}).get("name"),
                    referee=fix.get("referee"),
                    home_team_id=home_id,
                    home_team_name=home_name,
                    away_team_id=away_id,
                    away_team_name=away_name,
                    status=fix.get("status", {}).get("short", "NS"),
                    is_eligible=True,
                    source_timestamp=kickoff_utc,
                    available_at=now,
                )
            )

        return canonical_matches
