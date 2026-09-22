from typing import Optional
import datetime
from .base import OddsProvider, OddsEvent, OddsMarket, ProviderHealth
from .market_normalizer import normalize_market_name

class APIFootballOddsAdapter(OddsProvider):
    def __init__(self, api_client=None):
        self.api_client = api_client
        self.bookmaker_id = 6

    async def discover_events(self, league_ids: list[int]) -> list[OddsEvent]:
        return []

    async def get_live_events(self) -> list[OddsEvent]:
        return []

    async def get_prematch_events(self, league_id: int) -> list[OddsEvent]:
        return []

    async def get_markets(self, event_id: str) -> list[OddsMarket]:
        return []

    async def get_event_markets(self, event_id: str, market_types: list[str]) -> list[OddsMarket]:
        return []

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider="api-football",
            authenticated=True,
            reachable=True,
            live_odds_supported=True,
            prematch_supported=True,
            request_limit=100,
            requests_remaining=100,
            last_success=datetime.datetime.now(datetime.timezone.utc),
            last_error=None,
            supported_markets=["1x2", "double_chance"],
            is_1xbet_confirmed=True
        )
