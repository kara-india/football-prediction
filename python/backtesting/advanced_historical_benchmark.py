"""
Advanced historical benchmark for Phase 15.

Consumes project-owned public.historical_matches through HistoricalMatchRepository
and performs chronological Train -> Calibration -> Test evaluation.

Candidate families:
  - static Dixon-Coles with likelihood-profiled time decay;
  - score-driven dynamic Dixon-Coles;
  - total-goal Poisson / Negative-Binomial distribution selected by BIC.

No synthetic historical rows are created by this module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from python.backtesting.metrics_engine import MetricsEngine
from python.calibration.calibrator import ProbabilityCalibrator
from python.models.count_models import GoalCountModel
from python.models.dixon_coles import DixonColesModel
from python.models.dynamic_dixon_coles import ScoreDrivenDixonColes
from python.data.historical_repository import HistoricalMatchRepository


@dataclass
class FoldResult:
    fold_index: int
    train_start: str
    train_end: str
    calibration_start: str
    calibration_end: str
    test_start: str
    test_end: str
    train_samples: int
    calibration_samples: int
    test_samples: int
    metrics: Dict[str, float]
    selected_total_distribution: str


class AdvancedHistoricalBenchmark:
    def __init__(
        self,
        initial_train_months: int = 24,
        calibration_months: int = 3,
        test_months: int = 3,
        step_months: int = 3,
        min_calibration_samples: int = 20,
    ):
        self.initial_train_months = initial_train_months
        self.calibration_months = calibration_months
        self.test_months = test_months
        self.step_months = step_months
        self.min_calibration_samples = min_calibration_samples
        self.metrics = MetricsEngine()

    @staticmethod
    def _rps(y_true: np.ndarray, probs: np.ndarray) -> float:
        if probs.ndim != 2 or probs.shape[1] != 3:
            raise ValueError("RPS expects an N x 3 probability matrix.")
        outcomes = np.asarray(y_true, dtype=int)
        cumulative_pred = np.cumsum(probs[:, :2], axis=1)
        cumulative_true = np.column_stack([
            (outcomes == 0).astype(float),
            (outcomes <= 1).astype(float),
        ])
        return float(np.mean(np.sum((cumulative_pred - cumulative_true) ** 2, axis=1)))

    @staticmethod
    def _build_folds(
        df: pd.DataFrame,
        initial_train_months: int,
        calibration_months: int,
        test_months: int,
        step_months: int,
    ) -> List[Dict[str, pd.Timestamp]]:
        dates = pd.to_datetime(df["date"], utc=True).sort_values()
        start = dates.min().normalize()
        end = dates.max().normalize()
        folds: List[Dict[str, pd.Timestamp]] = []

        cursor = start + pd.DateOffset(months=initial_train_months)
        while True:
            train_start = cursor - pd.DateOffset(months=initial_train_months)
            train_end = cursor
            cal_start = train_end
            cal_end = cal_start + pd.DateOffset(months=calibration_months)
            test_start = cal_end
            test_end = test_start + pd.DateOffset(months=test_months)
            if test_end > end:
                break

            folds.append({
                "train_start": train_start,
                "train_end": train_end,
                "cal_start": cal_start,
                "cal_end": cal_end,
                "test_start": test_start,
                "test_end": test_end,
            })
            cursor = cursor + pd.DateOffset(months=step_months)

        return folds

    @staticmethod
    def _prepare(df: pd.DataFrame) -> pd.DataFrame:
        required = {"home_id", "away_id", "home_goals", "away_goals", "date"}
        missing = sorted(required - set(df.columns))
        if missing:
            raise ValueError(f"Benchmark input missing required columns: {missing}")
        out = df.copy()
        out["date"] = pd.to_datetime(out["date"], utc=True)
        out["home_goals"] = pd.to_numeric(out["home_goals"], errors="raise").astype(int)
        out["away_goals"] = pd.to_numeric(out["away_goals"], errors="raise").astype(int)
        out["total_goals"] = out["home_goals"] + out["away_goals"]
        out = out.sort_values(["date", "id"], kind="mergesort" if "id" in out.columns else "quicksort")
        return out.reset_index(drop=True)

    @staticmethod
    def _dc_rates(model: Any, home_id: str, away_id: str) -> Tuple[float, float]:
        if not hasattr(model, "get_expected_goals"):
            raise TypeError("Model must expose get_expected_goals().")
        h, a = model.get_expected_goals(home_id, away_id)
        return float(h), float(a)

    def _fit_static_dc(self, train: pd.DataFrame) -> DixonColesModel:
        model = DixonColesModel(xi=0.0019)
        # Learn the time-decay scale by profile likelihood rather than treating
        # one half-life as a universal football constant.
        model.estimate_xi_profile_likelihood(
            train[["home_id", "away_id", "home_goals", "away_goals", "date"]].copy(),
            xi_grid=[np.log(2.0) / d for d in (90.0, 180.0, 365.0, 730.0, 1460.0, 1000000.0)],
        )
        return model

    def _fit_dynamic_dc(self, train: pd.DataFrame) -> ScoreDrivenDixonColes:
        model = ScoreDrivenDixonColes()
        model.fit(train[["home_id", "away_id", "home_goals", "away_goals", "date"]].copy())
        return model

    def _predict_1x2(
        self,
        model: Any,
        frame: pd.DataFrame,
    ) -> Tuple[np.ndarray, np.ndarray]:
        probs: List[Tuple[float, float, float]] = []
        xg: List[Tuple[float, float]] = []
        for row in frame.itertuples(index=False):
            p = tuple(float(v) for v in model.predict_1x2(row.home_id, row.away_id))
            h, a = self._dc_rates(model, row.home_id, row.away_id)
            probs.append(p)
            xg.append((h, a))
        return np.asarray(probs, dtype=float), np.asarray(xg, dtype=float)

    def run(
        self,
        data: pd.DataFrame,
        include_static_dc: bool = True,
        include_dynamic_dc: bool = True,
    ) -> Dict[str, Any]:
        df = self._prepare(data)
        if len(df) < 500:
            raise ValueError("At least 500 completed historical matches are required.")

        folds = self._build_folds(
            df,
            self.initial_train_months,
            self.calibration_months,
            self.test_months,
            self.step_months,
        )
        if not folds:
            raise ValueError("Historical dataset is too short for configured walk-forward windows.")

        fold_rows: List[FoldResult] = []
        paired_records: Dict[str, List[Dict[str, Any]]] = {
            "static_dc": [],
            "dynamic_dc": [],
        }

        for idx, fold in enumerate(folds):
            train = df[(df["date"] >= fold["train_start"]) & (df["date"] < fold["train_end"])]
            cal = df[(df["date"] >= fold["cal_start"]) & (df["date"] < fold["cal_end"])]
            test = df[(df["date"] >= fold["test_start"]) & (df["date"] < fold["test_end"])]

            if len(train) < 100 or len(cal) < self.min_calibration_samples or len(test) == 0:
                continue

            candidates: Dict[str, Any] = {}
            if include_static_dc:
                candidates["static_dc"] = self._fit_static_dc(train)
            if include_dynamic_dc:
                candidates["dynamic_dc"] = self._fit_dynamic_dc(train)

            distributions = GoalCountModel().fit(train["total_goals"].to_numpy())
            fold_metric: Dict[str, float] = {
                "train_samples": float(len(train)),
                "calibration_samples": float(len(cal)),
                "test_samples": float(len(test)),
            }

            market_outcomes = np.select(
                [
                    test["home_goals"] > test["away_goals"],
                    test["home_goals"] == test["away_goals"],
                ],
                [0, 1],
                default=2,
            ).astype(int)

            for name, model in candidates.items():
                cal_probs_1x2, cal_xg = self._predict_1x2(model, cal)
                test_probs_1x2, test_xg = self._predict_1x2(model, test)

                if self.calibration_months > 0:
                    cal_outcome = np.select(
                        [
                            cal["home_goals"].to_numpy() > cal["away_goals"].to_numpy(),
                            cal["home_goals"].to_numpy() == cal["away_goals"].to_numpy(),
                        ],
                        [0, 1],
                        default=2,
                    ).astype(int)
                    cal_o25 = (cal["total_goals"].to_numpy() > 2).astype(int)

                    class_calibrators = []
                    for class_idx, market_name in enumerate(("HOME_WIN", "DRAW", "AWAY_WIN")):
                        binary_target = (cal_outcome == class_idx).astype(int)
                        cal_model = ProbabilityCalibrator(method="isotonic")
                        if len(np.unique(binary_target)) < 2:
                            raise RuntimeError(
                                f"Calibration window lacks both classes for {market_name}."
                            )
                        cal_model.fit(
                            binary_target,
                            cal_probs_1x2[:, class_idx],
                            market=market_name,
                        )
                        class_calibrators.append(cal_model)

                    ou_calibrator = ProbabilityCalibrator(method="isotonic")
                    ou_raw_cal = np.asarray([
                        distributions.predict_over_under(
                            2.5,
                            custom_mu=float(h + a),
                            custom_phi=distributions.phi,
                        )[0]
                        for h, a in cal_xg
                    ])
                    if len(np.unique(cal_o25)) < 2:
                        raise RuntimeError("Calibration window lacks both O/U 2.5 classes.")
                    ou_calibrator.fit(cal_o25, ou_raw_cal, market="OVER_2_5")

                    calibrated_1x2_raw = np.column_stack([
                        np.asarray(
                            class_calibrators[i].calibrate(
                                test_probs_1x2[:, i],
                                market=("HOME_WIN", "DRAW", "AWAY_WIN")[i],
                            ),
                            dtype=float,
                        )
                        for i in range(3)
                    ])
                    row_sums = np.maximum(calibrated_1x2_raw.sum(axis=1, keepdims=True), 1e-12)
                    calibrated_1x2 = calibrated_1x2_raw / row_sums

                    raw_over_test = np.asarray([
                        distributions.predict_over_under(
                            2.5,
                            custom_mu=float(h + a),
                            custom_phi=distributions.phi,
                        )[0]
                        for h, a in test_xg
                    ])
                    calibrated_over = np.asarray(
                        ou_calibrator.calibrate(raw_over_test, market="OVER_2_5"),
                        dtype=float,
                    )
                else:
                    raise RuntimeError("Phase 15 benchmark requires a calibration window.")

                y_home = (test["home_goals"].to_numpy() > test["away_goals"].to_numpy()).astype(int)
                y_over = (test["total_goals"].to_numpy() > 2).astype(int)
                calibrated_home = calibrated_1x2[:, 0]

                fold_metric[f"{name}_home_brier"] = self.metrics.brier_score(y_home, calibrated_home)
                fold_metric[f"{name}_home_log_loss"] = self.metrics.log_loss(y_home, calibrated_home)
                fold_metric[f"{name}_1x2_rps"] = self._rps(market_outcomes, calibrated_1x2)
                fold_metric[f"{name}_over25_brier"] = self.metrics.brier_score(y_over, calibrated_over)
                fold_metric[f"{name}_over25_log_loss"] = self.metrics.log_loss(y_over, calibrated_over)
                fold_metric[f"{name}_over25_ece"] = self.metrics.expected_calibration_error(y_over, calibrated_over)

                paired_records[name].extend([
                    {
                        "fold": idx,
                        "match_id": row_id,
                        "home_win": int(yh),
                        "home_prob": float(ph),
                        "over25": int(yo),
                        "over25_prob": float(po),
                    }
                    for row_id, yh, ph, yo, po in zip(
                        test["id"] if "id" in test.columns else test.index,
                        y_home,
                        calibrated_home,
                        y_over,
                        calibrated_over,
                    )
                ])

            fold_rows.append(FoldResult(
                fold_index=idx,
                train_start=fold["train_start"].isoformat(),
                train_end=fold["train_end"].isoformat(),
                calibration_start=fold["cal_start"].isoformat(),
                calibration_end=fold["cal_end"].isoformat(),
                test_start=fold["test_start"].isoformat(),
                test_end=fold["test_end"].isoformat(),
                train_samples=len(train),
                calibration_samples=len(cal),
                test_samples=len(test),
                metrics=fold_metric,
                selected_total_distribution=distributions.selected_distribution,
            ))

        if not fold_rows:
            raise ValueError("No valid walk-forward folds were produced.")

        summary: Dict[str, Any] = {
            "status": "success",
            "folds": [r.__dict__ for r in fold_rows],
            "candidate_summaries": {},
        }

        for name, records in paired_records.items():
            if not records:
                continue
            frame = pd.DataFrame(records)
            candidate_summary = {
                "sample_size": int(len(frame)),
                "home_win_brier": float(self.metrics.brier_score(frame["home_win"], frame["home_prob"])),
                "home_win_log_loss": float(self.metrics.log_loss(frame["home_win"], frame["home_prob"])),
                "over25_brier": float(self.metrics.brier_score(frame["over25"], frame["over25_prob"])),
                "over25_log_loss": float(self.metrics.log_loss(frame["over25"], frame["over25_prob"])),
                "home_win_ece": float(self.metrics.expected_calibration_error(frame["home_win"], frame["home_prob"])),
                "over25_ece": float(self.metrics.expected_calibration_error(frame["over25"], frame["over25_prob"])),
                "paired_predictions": records,
            }
            summary["candidate_summaries"][name] = candidate_summary

        # The total-goal distribution family is a separate empirical output.
        selection_counts = pd.Series([r.selected_total_distribution for r in fold_rows]).value_counts().to_dict()
        summary["total_goal_distribution_selections"] = {
            str(k): int(v) for k, v in selection_counts.items()
        }
        summary["data_window"] = {
            "first_match": df["date"].min().isoformat(),
            "last_match": df["date"].max().isoformat(),
            "matches": int(len(df)),
        }
        return summary


def run_supabase_benchmark(
    leagues: Optional[Sequence[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    repo = HistoricalMatchRepository()
    df = repo.fetch(leagues=leagues, start_date=start_date, end_date=end_date)
    benchmark = AdvancedHistoricalBenchmark()
    return benchmark.run(df)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 15 advanced historical benchmark")
    parser.add_argument("--league", action="append", default=None, help="Historical league code; repeatable. Defaults to E0.")
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    args = parser.parse_args()

    result = run_supabase_benchmark(
        leagues=args.league or None,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    print(json.dumps(result, indent=2, default=str))
