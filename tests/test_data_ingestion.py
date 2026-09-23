"""
Data Ingestion & Normalization Test Suite — Phase 3
Verifies zero-cost historical CSV parsing, team name resolution,
MatchQualityScorer bounds validation, and CanonicalMatch contract conformance.
"""
import pandas as pd
from datetime import datetime, timezone
import pytest

from python.ingestion.football_data_uk import FootballDataUKIngestion, TARGET_LEAGUES
from python.ingestion.quality_scorer import MatchQualityScorer
from python.ingestion.fixture_discovery import FixtureDiscoveryEngine, ALLOWED_LEAGUES
from python.adapters.quota_manager import CentralQuotaManager, QuotaExceededError
from python.data_contracts import CanonicalMatch


class TestHistoricalIngestionAndQuality:
    """Validate CSV parsing, team aliases, and quality scoring."""

    def test_canonical_team_name_resolution(self):
        """Verify common team aliases resolve to canonical standard names."""
        assert FootballDataUKIngestion.resolve_canonical_team("Man United") == "Manchester United"
        assert FootballDataUKIngestion.resolve_canonical_team("Man City") == "Manchester City"
        assert FootballDataUKIngestion.resolve_canonical_team("Spurs") == "Tottenham Hotspur"
        assert FootballDataUKIngestion.resolve_canonical_team("PSG") == "Paris Saint-Germain"
        assert FootballDataUKIngestion.resolve_canonical_team("Ath Madrid") == "Atletico Madrid"
        assert FootballDataUKIngestion.resolve_canonical_team("Arsenal") == "Arsenal"

    def test_quality_scorer_complete_match(self):
        """Complete match with all shots, cards, and odds should achieve quality score >= 0.9."""
        complete_record = {
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "fthg": 2,
            "ftag": 1,
            "hthg": 1,
            "htag": 0,
            "hs": 14,
            "as_shots": 9,
            "hst": 6,
            "ast": 3,
            "hc": 7,
            "ac": 4,
            "hy": 1,
            "ay": 2,
            "hr": 0,
            "ar": 0,
            "b365_h": 1.95,
            "b365_d": 3.60,
            "b365_a": 4.10,
        }
        score, anomalies = MatchQualityScorer.score_match(complete_record)
        assert score == 1.0
        assert len(anomalies) == 0

    def test_quality_scorer_detects_impossible_half_time(self):
        """Half-time score higher than full-time score must be flagged as anomaly."""
        corrupt_record = {
            "home_team": "Liverpool",
            "away_team": "Everton",
            "fthg": 1,
            "ftag": 0,
            "hthg": 2,  # Impossible: 2 at HT but 1 at FT
            "htag": 0,
            "hs": 10,
            "as_shots": 5,
        }
        score, anomalies = MatchQualityScorer.score_match(corrupt_record)
        assert any("HALFTIME_EXCEEDS_FULLTIME_HOME" in a for a in anomalies)
        assert score < 0.8

    def test_quality_scorer_detects_impossible_shots(self):
        """Shots on target exceeding total shots must be flagged."""
        corrupt_record = {
            "home_team": "Milan",
            "away_team": "Inter",
            "fthg": 0,
            "ftag": 0,
            "hs": 4,
            "hst": 7,  # Impossible: 7 SOT out of 4 shots
        }
        score, anomalies = MatchQualityScorer.score_match(corrupt_record)
        assert any("SHOTS_ON_TARGET_EXCEEDS_TOTAL_HOME" in a for a in anomalies)

    def test_csv_parser_to_canonical_matches(self):
        """Verify parsing raw DataFrame generates valid frozen CanonicalMatch objects."""
        raw_data = {
            "Date": ["12/08/2023"],
            "HomeTeam": ["Arsenal"],
            "AwayTeam": ["Nott'm Forest"],
            "FTHG": [2],
            "FTAG": [1],
            "FTR": ["H"],
            "HTHG": [2],
            "HTAG": [0],
            "HS": [15],
            "AS": [6],
            "HST": [7],
            "AST": [2],
            "HC": [8],
            "AC": [3],
            "HY": [2],
            "AY": [2],
            "HR": [0],
            "AR": [0],
            "B365H": [1.18],
            "B365D": [7.50],
            "B365A": [15.00],
        }
        df = pd.DataFrame(raw_data)
        engine = FootballDataUKIngestion()
        parsed = engine.parse_rows(df, league_code="E0", season="2324")
        assert len(parsed) == 1

        canonicals = engine.to_canonical_matches(parsed)
        assert len(canonicals) == 1
        m = canonicals[0]
        assert isinstance(m, CanonicalMatch)
        assert m.home_team_name == "Arsenal"
        assert m.status == "FT"
        assert m.provider_id == "football-data-uk"
        assert m.competition_id == 39


class TestFixtureDiscovery:
    """Validate daily bulk discovery eligibility rules and single-call limit."""

    def test_eligibility_filter_allows_tier1(self):
        """Top-tier league fixtures must pass eligibility gate."""
        fixture = {
            "league": {"id": 39, "name": "Premier League"},
            "teams": {
                "home": {"id": 42, "name": "Arsenal"},
                "away": {"id": 49, "name": "Chelsea"}
            }
        }
        assert FixtureDiscoveryEngine.is_eligible_fixture(fixture) is True

    def test_eligibility_filter_rejects_youth_and_women(self):
        """Youth and women competitions must be rejected."""
        u21_fixture = {
            "league": {"id": 39, "name": "Premier League U21"},
            "teams": {
                "home": {"id": 1, "name": "Arsenal U21"},
                "away": {"id": 2, "name": "Chelsea U21"}
            }
        }
        women_fixture = {
            "league": {"id": 39, "name": "Premier League"},
            "teams": {
                "home": {"id": 1, "name": "Arsenal Women"},
                "away": {"id": 2, "name": "Chelsea Women"}
            }
        }
        unregistered_league = {
            "league": {"id": 9999, "name": "Unknown League"},
            "teams": {
                "home": {"id": 1, "name": "Team A"},
                "away": {"id": 2, "name": "Team B"}
            }
        }

        assert FixtureDiscoveryEngine.is_eligible_fixture(u21_fixture) is False
        assert FixtureDiscoveryEngine.is_eligible_fixture(women_fixture) is False
        assert FixtureDiscoveryEngine.is_eligible_fixture(unregistered_league) is False
