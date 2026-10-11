"""football-data.org v4 client. Credentials are sent only in X-Auth-Token."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from .. import config as _app_config
from .match_protocol import Fixture, Score


BASE_URL = "https://api.football-data.org/v4"


class FootballDataOrgError(RuntimeError):
    def __init__(self, reason: str, status_code: int | None = None):
        self.reason = reason
        self.status_code = status_code
        super().__init__(reason)


class FootballDataOrgProvider:
    name = "football_data_org"

    def __init__(self, token: str | None = None, *, session: requests.Session | None = None):
        self.token = token if token is not None else _app_config.config.football_data_org_token
        self.session = session or requests.Session()

    def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        if not self.token:
            raise FootballDataOrgError("FOOTBALL_DATA_ORG_NOT_CONFIGURED")
        try:
            response = self.session.get(
                f"{BASE_URL}{path}",
                params=params,
                headers={"X-Auth-Token": self.token, "Accept": "application/json"},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise FootballDataOrgError("FOOTBALL_DATA_ORG_UNREACHABLE") from exc

        if response.status_code == 401:
            raise FootballDataOrgError("FOOTBALL_DATA_ORG_AUTH_FAILED", 401)
        if response.status_code == 403 or response.status_code == 404:
            raise FootballDataOrgError("FOOTBALL_DATA_ORG_COVERAGE_UNAVAILABLE", response.status_code)
        if response.status_code == 429:
            raise FootballDataOrgError("FOOTBALL_DATA_ORG_RATE_LIMITED", 429)
        if not response.ok:
            raise FootballDataOrgError("FOOTBALL_DATA_ORG_REQUEST_FAILED", response.status_code)
        try:
            return response.json()
        except ValueError as exc:
            raise FootballDataOrgError("FOOTBALL_DATA_ORG_INVALID_RESPONSE", response.status_code) from exc

    def list_fixtures(self, date: str) -> list[Fixture]:
        payload = self._get("/matches", {"dateFrom": date, "dateTo": date})
        fixtures: list[Fixture] = []
        for match in payload.get("matches", []):
            competition = match.get("competition") or {}
            home = match.get("homeTeam") or {}
            away = match.get("awayTeam") or {}
            kickoff = match.get("utcDate")
            if not (kickoff and home.get("name") and away.get("name")):
                continue
            fixtures.append(Fixture(
                provider=self.name,
                provider_match_id=str(match["id"]),
                competition=str(competition.get("code") or competition.get("name") or ""),
                kickoff_utc=kickoff,
                home_name=home["name"],
                away_name=away["name"],
                status=str(match.get("status") or "UNKNOWN"),
            ))
        return fixtures

    def get_score(self, provider_match_id: str) -> Score | None:
        if not provider_match_id.isdigit():
            return None
        match = self._get(f"/matches/{provider_match_id}")
        score = match.get("score") or {}
        current = score.get("fullTime") or score.get("regularTime") or score.get("halfTime") or {}
        home, away = current.get("home"), current.get("away")
        return Score(
            provider=self.name,
            provider_match_id=provider_match_id,
            status=str(match.get("status") or "UNKNOWN"),
            minute=match.get("minute"),
            home_goals=home if isinstance(home, int) else None,
            away_goals=away if isinstance(away, int) else None,
            observed_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_lineup(self, _provider_match_id: str):
        # This subscription does not establish a confirmed-XI source. A3 uses
        # the auditable manual lineup snapshot until an entitled feed is proven.
        return None

    def get_odds(self, _provider_match_id: str):
        return None
