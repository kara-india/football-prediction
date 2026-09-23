"""
Competition Allowlist & Eligibility Gatekeeper
Strictly enforces the 10-tier domestic leagues and senior men's international tournament gate.
Rejects youth, women, reserves, and unapproved lower-tier leagues.
"""
import re
from typing import Dict, Any, Tuple, Optional, List

ALLOWED_COMPETITIONS: Dict[int, str] = {
    # Top 10 Domestic Leagues
    39: "Premier League (England)",
    140: "La Liga (Spain)",
    78: "Bundesliga (Germany)",
    135: "Serie A (Italy)",
    61: "Ligue 1 (France)",
    88: "Eredivisie (Netherlands)",
    94: "Primeira Liga (Portugal)",
    144: "First Division A (Belgium)",
    128: "Liga Profesional (Argentina)",
    71: "Serie A (Brazil)",
    # Major European & Global Tournaments
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

# Regex to catch youth, women's, reserve, and junior competitions
EXCLUSION_PATTERN = re.compile(
    r"\b(U17|U18|U19|U20|U21|U23|Youth|Primavera|Sub[- ]?(17|18|19|20|21|23)|"
    r"Women|Woman|Fem\w*|Fémin\w*|Reserves?|Reserve|II|Cup|Trophy)\b",
    re.IGNORECASE
)


class CompetitionGatekeeper:
    """Evaluates fixture eligibility against approved competitions and senior men's criteria."""

    @classmethod
    def evaluate_eligibility(
        cls,
        league_id: int,
        home_team: str,
        away_team: str,
        league_name: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """Evaluate whether a match is eligible for model processing.

        Returns:
            Tuple of (is_eligible: bool, rejection_reason: Optional[str])
        """
        # 1. League Allowlist Check
        if league_id not in ALLOWED_COMPETITIONS:
            return False, f"UNAPPROVED_COMPETITION: League ID {league_id} not in approved tier-1 universe."

        # 2. Youth / Women / Reserve Check in Team Names
        for team, role in [(home_team, "Home"), (away_team, "Away")]:
            match = EXCLUSION_PATTERN.search(team)
            if match:
                return False, f"EXCLUDED_CATEGORY: {role} team '{team}' matches exclusion '{match.group(0)}'."

        # 3. League Name Sanity Check
        if league_name:
            match = EXCLUSION_PATTERN.search(league_name)
            if match:
                return False, f"EXCLUDED_COMPETITION: League '{league_name}' matches exclusion '{match.group(0)}'."

        return True, None

    @classmethod
    def filter_fixtures(cls, fixtures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter a list of raw provider fixture dictionaries down to eligible senior men's matches."""
        eligible = []
        for f in fixtures:
            lid = f.get("league", {}).get("id", 0)
            lname = f.get("league", {}).get("name", "")
            hname = f.get("teams", {}).get("home", {}).get("name", "")
            aname = f.get("teams", {}).get("away", {}).get("name", "")

            is_ok, _ = cls.evaluate_eligibility(lid, hname, aname, lname)
            if is_ok:
                eligible.append(f)
        return eligible
