"""Match-data provider seam for recovery phase A0+.

Runtime code must depend on these types, not on API-Football.
No method on this module performs network I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass(frozen=True)
class Fixture:
    provider: str
    provider_match_id: str
    competition: str
    kickoff_utc: str
    home_name: str
    away_name: str
    status: str


@dataclass(frozen=True)
class Score:
    provider: str
    provider_match_id: str
    status: str
    minute: Optional[int]
    home_goals: Optional[int]
    away_goals: Optional[int]
    observed_at: str


@dataclass(frozen=True)
class LineupPlayer:
    name: str
    position: Optional[str] = None


@dataclass(frozen=True)
class Lineup:
    provider: str
    provider_match_id: str
    home: list[LineupPlayer]
    away: list[LineupPlayer]
    source_url: str
    confirmed_at: str

    def confirmed_eleven(self) -> bool:
        return len(self.home) == 11 and len(self.away) == 11


@dataclass(frozen=True)
class OddsSnapshot:
    provider: str
    provider_match_id: str
    bookmaker: str
    captured_at: str
    prices: dict[str, float] = field(default_factory=dict)


class MatchDataProvider(Protocol):
    name: str

    def list_fixtures(self, date: str) -> list[Fixture]:
        """Return fixtures for a UTC date, or an empty list. Never invent rows."""

    def get_score(self, provider_match_id: str) -> Optional[Score]:
        ...

    def get_lineup(self, provider_match_id: str) -> Optional[Lineup]:
        ...

    def get_odds(self, provider_match_id: str) -> Optional[OddsSnapshot]:
        ...
