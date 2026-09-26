"""
Historical match repository for the statistical engine.

The repository reads the project-owned public.historical_matches table using
supabase-py and paginates deterministically. No fixture/synthetic fallback is
allowed in production benchmark execution.
"""

from __future__ import annotations

import os
from typing import Iterable, List, Optional

import pandas as pd
from supabase import Client, create_client


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
        self.url = url or os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
        self.key = key or os.environ.get("SUPABASE_SECRET_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.page_size = int(page_size)

        if not self.url:
            raise RuntimeError("Supabase URL is not configured.")
        if not self.key:
            raise RuntimeError("SUPABASE_SECRET_KEY is required for historical benchmark access.")
        if self.page_size < 1 or self.page_size > 1000:
            raise ValueError("page_size must be between 1 and 1000.")

        self.client: Client = create_client(self.url, self.key)

    def fetch(
        self,
        leagues: Optional[Iterable[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        league_values = [str(v) for v in leagues] if leagues else None
        rows: List[dict] = []
        offset = 0

        while True:
            query = (
                self.client
                .table("historical_matches")
                .select(",".join(HISTORICAL_COLUMNS))
                .order("match_date", desc=False)
                .order("id", desc=False)
                .range(offset, offset + self.page_size - 1)
            )

            if league_values:
                query = query.in_("league_code", league_values)
            if start_date:
                query = query.gte("match_date", start_date)
            if end_date:
                query = query.lte("match_date", end_date)

            response = query.execute()
            batch = response.data or []
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
