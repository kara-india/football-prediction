"""The Odds API v4 adapter, restricted to the named 1xBet book and EPL."""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

import httpx

from .. import config as _app_config
from .base import OddsEvent, OddsMarket, OddsProvider, ProviderHealth


BASE_URL = "https://api.the-odds-api.com/v4"
SPORT_KEY = "soccer_epl"
BOOKMAKER_KEY = "onexbet"
MARKET_KEYS = {"h2h", "totals"}


class ProviderNotConfiguredError(RuntimeError):
    pass


class OddsAPIError(RuntimeError):
    def __init__(self, reason: str, status_code: int | None = None):
        self.reason = reason
        self.status_code = status_code
        super().__init__(reason)


def _parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


class OddsAPIAdapter(OddsProvider):
    def __init__(self, api_key: str | None = None, *, timeout_seconds: float = 10):
        self.api_key = api_key if api_key is not None else _app_config.config.odds_api_key
        self.timeout_seconds = timeout_seconds

    def _check_configured(self) -> None:
        if not self.api_key:
            raise ProviderNotConfiguredError("ODDS_API_KEY not set")

    async def _get(self, path: str, params: dict[str, str] | None = None) -> tuple[Any, httpx.Headers]:
        self._check_configured()
        query = {"apiKey": self.api_key, **(params or {})}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(f"{BASE_URL}{path}", params=query)
        except httpx.HTTPError as exc:
            raise OddsAPIError("ODDS_API_UNREACHABLE") from exc

        if response.status_code == 401 or response.status_code == 403:
            raise OddsAPIError("ODDS_API_AUTH_FAILED", response.status_code)
        if response.status_code == 429:
            raise OddsAPIError("ODDS_API_RATE_LIMITED", 429)
        if response.status_code == 422:
            raise OddsAPIError("ODDS_API_MARKET_UNAVAILABLE", 422)
        if not response.is_success:
            raise OddsAPIError("ODDS_API_REQUEST_FAILED", response.status_code)
        try:
            return response.json(), response.headers
        except ValueError as exc:
            raise OddsAPIError("ODDS_API_INVALID_RESPONSE", response.status_code) from exc

    @staticmethod
    def _event(raw: dict[str, Any]) -> OddsEvent | None:
        kickoff = _parse_time(raw.get("commence_time"))
        if not kickoff or not raw.get("id") or not raw.get("home_team") or not raw.get("away_team"):
            return None
        live = kickoff <= dt.datetime.now(dt.timezone.utc)
        return OddsEvent(
            provider_event_id=str(raw["id"]),
            home_team=str(raw["home_team"]),
            away_team=str(raw["away_team"]),
            kickoff_utc=kickoff,
            competition_name="Premier League",
            competition_id=SPORT_KEY,
            is_live=live,
            status="LIVE" if live else "SCHEDULED",
        )

    async def _list_odds(self) -> tuple[list[dict[str, Any]], httpx.Headers]:
        payload, headers = await self._get(
            f"/sports/{SPORT_KEY}/odds",
            {
                "regions": "eu",
                "bookmakers": BOOKMAKER_KEY,
                "markets": "h2h,totals",
                "oddsFormat": "decimal",
                "dateFormat": "iso",
            },
        )
        if not isinstance(payload, list):
            raise OddsAPIError("ODDS_API_INVALID_RESPONSE")
        return payload, headers

    async def discover_events(self, league_ids: list[int]) -> list[OddsEvent]:
        # Legacy internal IDs: 39 is the former EPL identifier; 2021 is
        # football-data.org's Premier League competition ID. No other league
        # is silently redirected to soccer_epl.
        if not any(league_id in (39, 2021) for league_id in league_ids):
            return []
        return await self.get_prematch_events(2021)

    async def get_live_events(self) -> list[OddsEvent]:
        payload, _ = await self._list_odds()
        now = dt.datetime.now(dt.timezone.utc)
        events = (self._event(raw) for raw in payload)
        return [event for event in events if event and event.kickoff_utc <= now]

    async def get_prematch_events(self, league_id: int) -> list[OddsEvent]:
        if league_id not in (39, 2021):
            return []
        payload, _ = await self._list_odds()
        now = dt.datetime.now(dt.timezone.utc)
        events = (self._event(raw) for raw in payload)
        return [event for event in events if event and event.kickoff_utc > now]

    async def get_markets(self, event_id: str) -> list[OddsMarket]:
        return await self.get_event_markets(event_id, ["h2h", "totals"])

    async def get_event_markets(self, event_id: str, market_types: list[str]) -> list[OddsMarket]:
        requested = {market.lower() for market in market_types}
        api_markets = set()
        if requested & {"h2h", "1x2", "full_time_1x2"}:
            api_markets.add("h2h")
        if requested & {"totals", "ou25", "over_under_2_5"}:
            api_markets.add("totals")
        if not api_markets:
            return []

        payload, _headers = await self._get(
            f"/sports/{SPORT_KEY}/events/{event_id}/odds",
            {
                "regions": "eu",
                "bookmakers": BOOKMAKER_KEY,
                "markets": ",".join(sorted(api_markets)),
                "oddsFormat": "decimal",
                "dateFormat": "iso",
            },
        )
        if not isinstance(payload, dict):
            raise OddsAPIError("ODDS_API_INVALID_RESPONSE")

        captured_at = dt.datetime.now(dt.timezone.utc)
        event = self._event(payload)
        if event is None:
            return []
        output: list[OddsMarket] = []

        # A named book is mandatory. No best-price or other-book fallback.
        bookmaker = next(
            (book for book in payload.get("bookmakers", []) if book.get("key") == BOOKMAKER_KEY),
            None,
        )
        if not bookmaker:
            return []

        for market in bookmaker.get("markets", []):
            key = market.get("key")
            source_timestamp = _parse_time(market.get("last_update")) or captured_at
            if key == "h2h" and "h2h" in api_markets:
                for outcome in market.get("outcomes", []):
                    name = str(outcome.get("name", ""))
                    if name == event.home_team:
                        selection = "HOME"
                    elif name == event.away_team:
                        selection = "AWAY"
                    elif name.casefold() == "draw":
                        selection = "DRAW"
                    else:
                        continue
                    price = outcome.get("price")
                    if isinstance(price, (int, float)) and math.isfinite(price) and price > 1:
                        output.append(OddsMarket(
                            bookmaker=BOOKMAKER_KEY,
                            fixture_id=event.provider_event_id,
                            timestamp=captured_at,
                            market_id="h2h",
                            canonical_market="1X2",
                            period="full_match",
                            selection=selection,
                            line=None,
                            decimal_odds=float(price),
                            is_live=event.is_live,
                            suspended=False,
                            source_timestamp=source_timestamp,
                        ))
            elif key == "totals" and "totals" in api_markets:
                for outcome in market.get("outcomes", []):
                    point = outcome.get("point")
                    name = str(outcome.get("name", "")).casefold()
                    if point != 2.5 or name not in {"over", "under"}:
                        continue
                    price = outcome.get("price")
                    if isinstance(price, (int, float)) and math.isfinite(price) and price > 1:
                        output.append(OddsMarket(
                            bookmaker=BOOKMAKER_KEY,
                            fixture_id=event.provider_event_id,
                            timestamp=captured_at,
                            market_id="totals",
                            canonical_market="OU25",
                            period="full_match",
                            selection=name.upper(),
                            line=2.5,
                            decimal_odds=float(price),
                            is_live=event.is_live,
                            suspended=False,
                            source_timestamp=source_timestamp,
                        ))
        return output

    async def health_check(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(
                provider="the-odds-api",
                authenticated=False,
                reachable=False,
                live_odds_supported=False,
                prematch_supported=False,
                request_limit=None,
                requests_remaining=None,
                last_success=None,
                last_error="ODDS_API_NOT_CONFIGURED",
                supported_markets=["1X2", "OU25"],
                is_1xbet_confirmed=False,
            )
        try:
            payload, _headers = await self._get("/sports", {"all": "true"})
            available = isinstance(payload, list) and any(
                sport.get("key") == SPORT_KEY for sport in payload if isinstance(sport, dict)
            )
            return ProviderHealth(
                provider="the-odds-api",
                authenticated=True,
                reachable=True,
                live_odds_supported=True,
                prematch_supported=True,
                request_limit=None,
                requests_remaining=None,
                last_success=dt.datetime.now(dt.timezone.utc),
                last_error=None if available else "EPL_ODDS_UNAVAILABLE",
                supported_markets=["1X2", "OU25"],
                # A sports list does not prove there is an EPL 1xBet quote.
                is_1xbet_confirmed=False,
            )
        except OddsAPIError as exc:
            return ProviderHealth(
                provider="the-odds-api",
                authenticated=exc.reason != "ODDS_API_AUTH_FAILED",
                reachable=exc.reason != "ODDS_API_UNREACHABLE",
                live_odds_supported=False,
                prematch_supported=False,
                request_limit=None,
                requests_remaining=None,
                last_success=None,
                last_error=exc.reason,
                supported_markets=["1X2", "OU25"],
                is_1xbet_confirmed=False,
            )
