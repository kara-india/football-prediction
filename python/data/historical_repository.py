"""
Historical match repository for the statistical engine.

Uses Supabase PostgREST directly so modern sb_secret_* API keys work with the
benchmark even when the wider Python application still contains older client
library pins. Results are paginated deterministically; no synthetic fallback.
"""

from __future__ import annotations

import os
from typing import Iterable, List, Optional
from urllib.parse import quote

import httpx
import pandas as pd


HISTORICAL_COLUMNS = [
    "id",
    "league_code",
    "league_name",
    "season",
    "match_date",
    "home_team",
    "away_team",
    "fthg",
    "ftag",
    "ftr",
    "hs",
    "as_shots",
    "hst",
    "ast",
    "hf",
    "af",
    "hc",
    "ac",
    "hy",
    "ay",
    "hr",
    "ar",
    "b365_h",
    "b365_d",
    "b365_a",
]


class HistoricalMatchRepository:
    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        page_size: int = 1000,
    ):
        self.url = (
            url
            or os.environ.get("SUPABASE_URL")
            or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        )
        self.key = (
            key
            or os.environ.get("SUPABASE_SECRET_KEY")
            or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        )
        self.page_size = int(page_size)

        if not self.url:
            raise RuntimeError("SUPABASE_URL is not configured.")
        if not self.key:
            raise RuntimeError("SUPABASE_SECRET_KEY is required for historical benchmark access.")
        if self.page_size < 1 or self.page_size > 1000:
            raise ValueError("page_size must be between 1 and 1000.")

    def _build_query(
        self,
        offset: int,
        leagues: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> str:
        params = [
            ("select", ",".join(HISTORICAL_COLUMNS)),
            ("order", "match_date.asc,id.asc"),
            ("limit", str(self.page_size)),
            ("offset", str(offset)),
        ]

        if leagues:
            encoded = ",".join(quote(value, safe="") for value in leagues)
            params.append(("league_code", f"in.({encoded})"))
        if start_date:
            params.append(("match_date", f"gte.{start_date}"))
        if end_date:
            params.append(("match_date", f"lte.{end_date}"))

        return "&".join(f"{quote(k, safe='')}={quote(v, safe='(),.')}" for k, v in params)

    def fetch(
        self,
        leagues: Optional[Iterable[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        league_values = [str(value) for value in leagues] if leagues else None
        rows: List[dict] = []
        offset = 0
        endpoint = f"{self.url.rstrip('/')}/rest/v1/historical_matches"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
        }

        with httpx.Client(timeout=30.0) as client:
            while True:
                response = client.get(
                    f"{endpoint}?{self._build_query(offset, league_values, start_date, end_date)}",
                    headers=headers,
                )
                if response.status_code >= 400:
                    raise RuntimeError(
                        f"Supabase historical_matches request failed with HTTP {response.status_code}."
                    )

                batch = response.json() or []
                if not isinstance(batch, list):
                    raise RuntimeError("Supabase historical_matches response is not a list.")

                rows.extend(batch)
                if len(batch) < self.page_size:
                    break
                offset += self.page_size

        if not rows:
            return pd.DataFrame(columns=HISTORICAL_COLUMNS)

        frame = pd.DataFrame(rows, columns=HISTORICAL_COLUMNS)
        return self.to_model_frame(frame)

    @staticmethod
    def to_model_frame(frame: pd.DataFrame) -> pd.DataFrame:
        required = {"home_team", "away_team", "match_date", "fthg", "ftag"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"Historical dataset is missing required fields: {missing}")

        out = frame.copy()
        out["home_id"] = out["home_team"].astype(str)
        out["away_id"] = out["away_team"].astype(str)
        out["home_goals"] = pd.to_numeric(out["fthg"], errors="raise").astype(int)
        out["away_goals"] = pd.to_numeric(out["ftag"], errors="raise").astype(int)
        out["date"] = pd.to_datetime(out["match_date"], utc=True, errors="raise")

        if (out[["home_goals", "away_goals"]] < 0).any().any():
            raise ValueError("Historical goal counts cannot be negative.")

        out = out.sort_values(["date", "id"], kind="mergesort").reset_index(drop=True)
        return out
