from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import datetime

@dataclass
class OddsEvent:
    provider_event_id: str
    home_team: str
    away_team: str
    kickoff_utc: datetime.datetime
    competition_name: str
    competition_id: Optional[str]
    is_live: bool
    status: str

@dataclass  
class OddsMarket:
    bookmaker: str  # always '1xbet'
    fixture_id: str
    timestamp: datetime.datetime
    market_id: str
    canonical_market: str
    period: str  # 'full_match', 'first_half', 'second_half'
    selection: str
    line: Optional[float]
    decimal_odds: float
    is_live: bool
    suspended: bool
    source_timestamp: datetime.datetime

@dataclass
class ProviderHealth:
    provider: str
    authenticated: bool
    reachable: bool
    live_odds_supported: bool
    prematch_supported: bool
    request_limit: Optional[int]
    requests_remaining: Optional[int]
    last_success: Optional[datetime.datetime]
    last_error: Optional[str]
    supported_markets: list[str]
    is_1xbet_confirmed: bool

class OddsProvider(ABC):
    @abstractmethod
    async def discover_events(self, league_ids: list[int]) -> list[OddsEvent]: ...
    @abstractmethod
    async def get_live_events(self) -> list[OddsEvent]: ...
    @abstractmethod
    async def get_prematch_events(self, league_id: int) -> list[OddsEvent]: ...
    @abstractmethod
    async def get_markets(self, event_id: str) -> list[OddsMarket]: ...
    @abstractmethod
    async def get_event_markets(self, event_id: str, market_types: list[str]) -> list[OddsMarket]: ...
    @abstractmethod
    async def health_check(self) -> ProviderHealth: ...
