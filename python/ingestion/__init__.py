"""
Zero-Cost Ingestion Package
Provides data ingestion from open datasets (football-data.co.uk) and
budget-governed fixture discovery via API-Football.
"""
from .football_data_uk import FootballDataUKIngestion
from .fixture_discovery import FixtureDiscoveryEngine
from .quality_scorer import MatchQualityScorer

__all__ = [
    "FootballDataUKIngestion",
    "FixtureDiscoveryEngine",
    "MatchQualityScorer",
]
