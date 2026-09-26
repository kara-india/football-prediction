"""
Statistical model training / registry worker.

Workflow:
  1. Load real historical matches from Supabase.
  2. Run chronological advanced benchmark.
  3. Fit final static and dynamic Dixon-Coles challengers on the complete
     historical training set.
  4. Persist them as status='challenger' with benchmark metrics and serialized
     parameters.
  5. Never promote automatically.

This worker is intentionally separate from live inference.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

import pandas as pd
from supabase import Client, create_client

from python.backtesting.advanced_historical_benchmark import AdvancedHistoricalBenchmark
from python.data.historical_repository import HistoricalMatchRepository
from python.models.dixon_coles import DixonColesModel
from python.models.dynamic_dixon_coles import ScoreDrivenDixonColes


class StatisticalTrainingWorker:
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        repository: Optional[HistoricalMatchRepository] = None,
    ):
        self.supabase_url = supabase_url or os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not self.supabase_url or not self.supabase_key:
            raise RuntimeError("Supabase URL and SUPABASE_SERVICE_ROLE_KEY are required.")

        self.repository = repository or HistoricalMatchRepository(
            url=self.supabase_url,
            key=self.supabase_key,
        )
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    @staticmethod
    def _dataset_version(df: pd.DataFrame) -> str:
        cols = ["date", "home_id", "away_id", "home_goals", "away_goals"]
        ordered = df.loc[:, cols].copy()
        ordered["date"] = pd.to_datetime(ordered["date"], utc=True).astype(str)
        payload = "\n".join(
            "|".join(str(v) for v in row)
            for row in ordered.itertuples(index=False, name=None)
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]

    def _persist_candidate(
        self,
        model_name: str,
        version: str,
        model_type: str,
        model: Any,
        benchmark_summary: Dict[str, Any],
        train_df: pd.DataFrame,
    ) -> None:
        candidate = benchmark_summary["candidate_summaries"].get(model_name, {})
        row = {
            "model_name": model_name,
            "version": version,
            "model_type": model_type,
            "status": "challenger",
            "training_start": train_df["date"].min().date().isoformat(),
            "training_end": train_df["date"].max().date().isoformat(),
            "validation_start": train_df["date"].min().date().isoformat(),
            "validation_end": train_df["date"].max().date().isoformat(),
            "dataset_version": benchmark_summary["data_window"]["dataset_version"],
            "hyperparameters": model.serialize(),
            "features_used": {
                "type": "historical_goal_process",
                "candidate": model_type,
                "benchmark_markets": ["1X2_HOME", "OVER_2_5"],
            },
            "sample_size": int(candidate.get("sample_size", 0)),
            "brier_score": float(candidate.get("home_win_brier", 0.0)),
            "log_loss": float(candidate.get("home_win_log_loss", 0.0)),
            "ece": float(candidate.get("home_win_ece", 0.0)),
            "notes": (
                "Phase 15 challenger. Metrics are chronological out-of-sample "
                "benchmark metrics. No automatic promotion."
            ),
        }
        self.client.table("model_versions").upsert(
            row,
            on_conflict="model_name,version",
        ).execute()

    def run(
        self,
        leagues: Optional[Sequence[str]] = ("E0",),
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        persist: bool = True,
    ) -> Dict[str, Any]:
        df = self.repository.fetch(
            leagues=leagues,
            start_date=start_date,
            end_date=end_date,
        )
        if df.empty:
            raise RuntimeError("No historical training data returned.")

        benchmark = AdvancedHistoricalBenchmark()
        summary = benchmark.run(df)
        summary["data_window"]["dataset_version"] = self._dataset_version(df)

        if persist:
            static_model = DixonColesModel()
            static_model.estimate_xi_profile_likelihood(
                df[["home_id", "away_id", "home_goals", "away_goals", "date"]].copy(),
                xi_grid=[
                    0.0 if d >= 999999 else __import__("numpy").log(2.0) / d
                    for d in (90.0, 180.0, 365.0, 730.0, 1460.0, 1_000_000.0)
                ],
            )
            dynamic_model = ScoreDrivenDixonColes().fit(
                df[["home_id", "away_id", "home_goals", "away_goals", "date"]].copy()
            )

            version_suffix = summary["data_window"]["dataset_version"]
            self._persist_candidate(
                "static_dixon_coles",
                f"15.0.0-{version_suffix}",
                "dixon_coles",
                static_model,
                summary,
                df,
            )
            self._persist_candidate(
                "dynamic_dixon_coles",
                f"15.0.0-{version_suffix}",
                "score_driven_dixon_coles",
                dynamic_model,
                summary,
                df,
            )

            summary["registry"] = {
                "status": "challengers_persisted",
                "automatic_promotion": False,
                "dataset_version": version_suffix,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            summary["registry"] = {
                "status": "dry_run",
                "automatic_promotion": False,
            }

        return summary


def run_statistical_training(
    leagues: Optional[Sequence[str]] = ("E0",),
    persist: bool = True,
) -> Dict[str, Any]:
    worker = StatisticalTrainingWorker()
    return worker.run(leagues=leagues, persist=persist)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 15 statistical model training worker")
    parser.add_argument("--league", action="append", default=["E0"])
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args()

    result = run_statistical_training(
        leagues=args.league or None,
        persist=not args.no_persist,
    )
    print(json.dumps(result, indent=2, default=str))
