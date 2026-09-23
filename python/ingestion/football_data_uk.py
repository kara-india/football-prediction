"""
Historical Match Ingestion Engine from football-data.co.uk
Downloads, parses, cleans, scores, and ingests 5 years of historical match data
across top European domestic leagues without consuming API credits.
"""
import io
import os
import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from .quality_scorer import MatchQualityScorer
from ..data_contracts import CanonicalMatch

logger = logging.getLogger("FootballDataUKIngestion")

# Standard 10 Target Leagues on football-data.co.uk
TARGET_LEAGUES: Dict[str, Dict[str, Any]] = {
    "E0": {"name": "Premier League", "country": "England", "competition_id": 39},
    "SP1": {"name": "La Liga", "country": "Spain", "competition_id": 140},
    "D1": {"name": "Bundesliga", "country": "Germany", "competition_id": 78},
    "I1": {"name": "Serie A", "country": "Italy", "competition_id": 135},
    "F1": {"name": "Ligue 1", "country": "France", "competition_id": 61},
    "N1": {"name": "Eredivisie", "country": "Netherlands", "competition_id": 88},
    "P1": {"name": "Primeira Liga", "country": "Portugal", "competition_id": 94},
    "B1": {"name": "First Division A", "country": "Belgium", "competition_id": 144},
}

# 5 Seasons: 2019/20 through 2023/24
TARGET_SEASONS = ["1920", "2021", "2122", "2223", "2324"]

# Common team aliases mapping to canonical names
TEAM_CANONICAL_MAP = {
    "Man United": "Manchester United",
    "Man City": "Manchester City",
    "Spurs": "Tottenham Hotspur",
    "Tottenham": "Tottenham Hotspur",
    "Wolves": "Wolverhampton Wanderers",
    "Newcastle": "Newcastle United",
    "Leicester": "Leicester City",
    "Brighton": "Brighton & Hove Albion",
    "West Ham": "West Ham United",
    "Paris SG": "Paris Saint-Germain",
    "PSG": "Paris Saint-Germain",
    "Ath Madrid": "Atletico Madrid",
    "Ath Bilbao": "Athletic Bilbao",
    "Bayern Munich": "FC Bayern Munich",
    "Dortmund": "Borussia Dortmund",
    "Leverkusen": "Bayer 04 Leverkusen",
    "M'gladbach": "Borussia Monchengladbach",
    "Inter": "Internazionale",
    "Milan": "AC Milan",
    "Roma": "AS Roma",
    "Sporting CP": "Sporting Lisbon",
}


class FootballDataUKIngestion:
    """Ingests historical CSV datasets from football-data.co.uk into Supabase."""

    BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.supabase_url = supabase_url or os.environ.get(
            "NEXT_PUBLIC_SUPABASE_URL",
            "https://qqcxjjkgvqknesrtnwal.supabase.co"
        )
        self.supabase_key = supabase_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
        )

    @classmethod
    def resolve_canonical_team(cls, raw_team: str) -> str:
        """Resolve raw team string into canonical platform team name."""
        clean = raw_team.strip()
        return TEAM_CANONICAL_MAP.get(clean, clean)

    def fetch_csv(self, league_code: str, season: str) -> pd.DataFrame:
        """Download and parse CSV for a specific league and season."""
        url = self.BASE_URL.format(season=season, league=league_code)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (FootballAnalyticsTerminal/1.0)"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                content = resp.read()
                df = pd.read_csv(io.BytesIO(content), encoding="latin1", on_bad_lines="skip")
                return df
        except Exception as e:
            logger.warning(f"Could not download CSV for {league_code} {season}: {e}")
            return pd.DataFrame()

    def parse_rows(self, df: pd.DataFrame, league_code: str, season: str) -> List[Dict[str, Any]]:
        """Parse raw dataframe into clean, scored database records."""
        league_info = TARGET_LEAGUES.get(league_code, {"name": league_code, "country": "Unknown", "competition_id": 0})
        season_label = f"20{season[:2]}-20{season[2:]}"
        records: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            date_raw = str(row.get("Date", "")).strip()
            match_date = None
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
                try:
                    match_date = datetime.strptime(date_raw, fmt).strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue

            if not match_date:
                continue

            raw_home = str(row.get("HomeTeam", "")).strip()
            raw_away = str(row.get("AwayTeam", "")).strip()
            if not raw_home or not raw_away or raw_home == "nan" or raw_away == "nan":
                continue

            home_team = self.resolve_canonical_team(raw_home)
            away_team = self.resolve_canonical_team(raw_away)

            def _int(col):
                val = row.get(col)
                if pd.notna(val):
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        pass
                return None

            def _float(col):
                val = row.get(col)
                if pd.notna(val):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
                return None

            record = {
                "league_code": league_code,
                "league_name": f"{league_info['name']} ({league_info['country']})",
                "season": season_label,
                "match_date": match_date,
                "home_team": home_team,
                "away_team": away_team,
                "fthg": _int("FTHG"),
                "ftag": _int("FTAG"),
                "ftr": str(row.get("FTR", "")).strip() or None,
                "hthg": _int("HTHG"),
                "htag": _int("HTAG"),
                "hs": _int("HS"),
                "as_shots": _int("AS"),
                "hst": _int("HST"),
                "ast": _int("AST"),
                "hf": _int("HF"),
                "af": _int("AF"),
                "hc": _int("HC"),
                "ac": _int("AC"),
                "hy": _int("HY"),
                "ay": _int("AY"),
                "hr": _int("HR"),
                "ar": _int("AR"),
                "b365_h": _float("B365H"),
                "b365_d": _float("B365D"),
                "b365_a": _float("B365A"),
            }

            quality_score, anomalies = MatchQualityScorer.score_match(record)
            if quality_score >= 0.5:
                record["quality_score"] = quality_score
                records.append(record)

        return records

    def to_canonical_matches(self, records: List[Dict[str, Any]]) -> List[CanonicalMatch]:
        """Convert parsed records into frozen CanonicalMatch instances."""
        canonicals: List[CanonicalMatch] = []
        now = datetime.now(timezone.utc)

        for r in records:
            league_code = r["league_code"]
            comp_info = TARGET_LEAGUES.get(league_code, {"name": r.get("league_name", "League"), "competition_id": 0})
            kickoff = datetime.strptime(r["match_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)

            match_id = f"hist_{league_code}_{r['season']}_{r['match_date']}_{r['home_team']}_{r['away_team']}".replace(" ", "_")
            canonicals.append(
                CanonicalMatch(
                    match_id=match_id,
                    provider_id="football-data-uk",
                    provider_fixture_id=abs(hash(match_id)) % (10**9),
                    competition_id=comp_info["competition_id"],
                    competition_name=comp_info["name"],
                    season=int(r["season"][:4]),
                    round="Regular Season",
                    kickoff_utc=kickoff,
                    venue_name=None,
                    referee=None,
                    home_team_id=abs(hash(r["home_team"])) % (10**7),
                    home_team_name=r["home_team"],
                    away_team_id=abs(hash(r["away_team"])) % (10**7),
                    away_team_name=r["away_team"],
                    status="FT",
                    is_eligible=True,
                    source_timestamp=kickoff,
                    available_at=now,
                )
            )

        return canonicals
