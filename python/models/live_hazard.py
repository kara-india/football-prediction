"""
Learned in-play goal hazard model.

The model estimates a discrete-time Poisson intensity:
    lambda_minute = exp(log_baseline_rate + X beta)

and therefore
    P(goal in minute | state) = 1 - exp(-lambda_minute).

Time dependence is represented with learned cubic-spline basis terms rather than
a fixed "late goal multiplier". State effects are learned from historical
minute-level observations with L2 shrinkage.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize


class LearnedLiveHazard:
    FEATURE_COLUMNS = (
        "minute",
        "score_diff",
        "red_card_diff",
        "shots_on_target_diff",
        "xg_diff",
        "substitution_diff",
        "knockout_context",
        "home_indicator",
    )

    def __init__(
        self,
        l2: float = 4.0,
        spline_knots: Tuple[float, ...] = (15.0, 30.0, 45.0, 60.0, 75.0),
    ):
        self.l2 = float(l2)
        self.spline_knots = tuple(float(k) for k in spline_knots)
        self.feature_mean: Optional[np.ndarray] = None
        self.feature_scale: Optional[np.ndarray] = None
        self.coef_: Optional[np.ndarray] = None
        self.fitted = False
        self.metrics: Dict[str, Any] = {}

    @staticmethod
    def _basis(minute: np.ndarray, knots: Tuple[float, ...]) -> np.ndarray:
        t = np.clip(np.asarray(minute, dtype=float) / 90.0, 0.0, 1.0)
        columns = [t, t * t, t * t * t]
        for knot in knots:
            k = np.clip(knot / 90.0, 0.0, 1.0)
            d = np.maximum(0.0, t - k)
            columns.append(d ** 3)
        return np.column_stack(columns)

    def _raw_features(self, df: pd.DataFrame) -> np.ndarray:
        base = df.loc[:, self.FEATURE_COLUMNS].apply(pd.to_numeric, errors="raise").to_numpy(float)
        time_basis = self._basis(base[:, 0], self.spline_knots)
        # minute is represented by the spline basis; exclude raw minute from
        # the remaining state vector.
        return np.column_stack([time_basis, base[:, 1:]])

    def fit(self, minute_panel: pd.DataFrame) -> "LearnedLiveHazard":
        required = set(self.FEATURE_COLUMNS) | {"goal"}
        missing = sorted(required - set(minute_panel.columns))
        if missing:
            raise ValueError(f"Missing live-hazard columns: {missing}")

        df = minute_panel.copy()
        y = pd.to_numeric(df["goal"], errors="raise").to_numpy(float)
        if (y < 0).any():
            raise ValueError("goal must be non-negative.")
        if len(df) < 500:
            raise ValueError("At least 500 team-minute observations are required.")

        X = self._raw_features(df)
        mean = X.mean(axis=0)
        scale = X.std(axis=0)
        scale[scale < 1e-8] = 1.0
        Xs = (X - mean) / scale

        def objective(beta: np.ndarray) -> float:
            eta = np.clip(Xs @ beta, -12.0, 5.0)
            lam = np.exp(eta)
            nll = np.sum(lam - y * eta)
            penalty = 0.5 * self.l2 * np.sum(beta ** 2)
            value = nll + penalty
            return float(value) if np.isfinite(value) else 1e20

        def gradient(beta: np.ndarray) -> np.ndarray:
            eta = np.clip(Xs @ beta, -12.0, 5.0)
            resid = np.exp(eta) - y
            return Xs.T @ resid + self.l2 * beta

        res = minimize(
            objective,
            np.zeros(Xs.shape[1], dtype=float),
            jac=gradient,
            method="L-BFGS-B",
            options={"maxiter": 250, "ftol": 1e-10},
        )
        if not res.success:
            raise RuntimeError(f"Live hazard optimization failed: {res.message}")

        self.feature_mean = mean
        self.feature_scale = scale
        self.coef_ = res.x
        self.fitted = True
        self.metrics = {
            "converged": bool(res.success),
            "n_observations": int(len(df)),
            "n_features": int(Xs.shape[1]),
            "objective": float(res.fun),
            "l2": self.l2,
            "spline_knots": list(self.spline_knots),
        }
        return self

    def _state_frame(
        self,
        minute: np.ndarray,
        score_diff: np.ndarray,
        red_card_diff: np.ndarray,
        shots_on_target_diff: np.ndarray,
        xg_diff: np.ndarray,
        substitution_diff: np.ndarray,
        knockout_context: np.ndarray,
        home_indicator: np.ndarray,
    ) -> np.ndarray:
        data = pd.DataFrame({
            "minute": minute,
            "score_diff": score_diff,
            "red_card_diff": red_card_diff,
            "shots_on_target_diff": shots_on_target_diff,
            "xg_diff": xg_diff,
            "substitution_diff": substitution_diff,
            "knockout_context": knockout_context,
            "home_indicator": home_indicator,
        })
        return self._raw_features(data)

    def correction_multiplier(
        self,
        minute: Any,
        score_diff: Any,
        red_card_diff: Any,
        shots_on_target_diff: Any = 0.0,
        xg_diff: Any = 0.0,
        substitution_diff: Any = 0.0,
        knockout_context: Any = 0.0,
        home_indicator: Any = 1.0,
    ) -> np.ndarray:
        if not self.fitted or self.coef_ is None or self.feature_mean is None or self.feature_scale is None:
            raise RuntimeError("Live hazard model is not fitted.")

        arrays = [
            np.asarray(v, dtype=float)
            for v in (
                minute,
                score_diff,
                red_card_diff,
                shots_on_target_diff,
                xg_diff,
                substitution_diff,
                knockout_context,
                home_indicator,
            )
        ]
        n = max(a.size for a in arrays)
        arrays = [
            np.full(n, a.item()) if a.size == 1 else a.reshape(-1)
            for a in arrays
        ]
        X = self._state_frame(*arrays)
        Xs = (X - self.feature_mean) / self.feature_scale
        log_correction = np.clip(Xs @ self.coef_, -4.0, 4.0)
        return np.exp(log_correction)

    def predict_minute_rate(
        self,
        baseline_rate_per_minute: Any,
        **state_kwargs: Any,
    ) -> np.ndarray:
        base = np.asarray(baseline_rate_per_minute, dtype=float)
        if np.any(base <= 0):
            raise ValueError("baseline_rate_per_minute must be positive.")
        mult = self.correction_multiplier(**state_kwargs)
        return base.reshape(-1) * mult

    def serialize(self) -> Dict[str, Any]:
        return {
            "model_type": "LearnedLiveHazard",
            "version": "1.0.0",
            "l2": self.l2,
            "spline_knots": list(self.spline_knots),
            "feature_mean": self.feature_mean.tolist() if self.feature_mean is not None else None,
            "feature_scale": self.feature_scale.tolist() if self.feature_scale is not None else None,
            "coef": self.coef_.tolist() if self.coef_ is not None else None,
            "metrics": self.metrics,
        }
