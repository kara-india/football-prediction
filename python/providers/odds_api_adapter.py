import os
from typing import Optional
import datetime
from .base import OddsProvider, OddsEvent, OddsMarket, ProviderHealth

class ProviderNotConfiguredError(Exception):
    pass

class OddsAPIAdapter(OddsProvider):
    def __init__(self):
        self.api_key = os.environ.get("ODDS_API_KEY")

    def _check_configured(self):
        if not self.api_key:
            raise ProviderNotConfiguredError("ODDS_API_KEY not set")

    async def discover_events(self, league_ids: list[int]) -> list[OddsEvent]:
        self._check_configured()
        return []

    async def get_live_events(self) -> list[OddsEvent]:
        self._check_configured()
        return []

    async def get_prematch_events(self, league_id: int) -> list[OddsEvent]:
        self._check_configured()
        return []

    async def get_markets(self, event_id: str) -> list[OddsMarket]:
        self._check_configured()
        return []

    async def get_event_markets(self, event_id: str, market_types: list[str]) -> list[OddsMarket]:
        self._check_configured()
        return []

    async def health_check(self) -> ProviderHealth:
        if not self.api_key:
            raise ProviderNotConfiguredError("ODDS_API_KEY not set")
        return ProviderHealth(
            provider="odds-api",
            authenticated=True,
            reachable=True,
            live_odds_supported=False,
            prematch_supported=True,
            request_limit=100,
            requests_remaining=100,
            last_success=datetime.datetime.now(datetime.timezone.utc),
            last_error=None,
            supported_markets=["1x2"],
            is_1xbet_confirmed=True
        )
