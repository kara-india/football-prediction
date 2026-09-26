"""
Learned lineup/player effects for team goal rates.

The model is an offset Poisson regression:
    log(lambda_match) = baseline_log_rate
                       + sum(attacking starter effects)
                       + sum(opponent defensive starter effects)

Player coefficients are estimated jointly with L2 shrinkage. No arbitrary
"missing player = -4%" or fixed XI-strength multiplier is used.
"""

from __future__ import annotations

import ast
import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize


class LearnedLineupEffectModel:
    def __init__(self, l2_attack: float = 8.0, l2_defence: float = 8.0):
        self.l2_attack = float(l2_attack)
        self.l2_defence = float(l2_defence)
        self.attack_effects: Dict[str, float] = {}
        self.defence_effects: Dict[str, float] = {}
        self.player_index: Dict[str, int] = {}
        self.fitted = False
        self.metrics: Dict[str, Any] = {}

    @staticmethod
    def _parse_ids(value: Any) -> List[str]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return []
        if isinstance(value, (list, tuple, set, np.ndarray)):
            return [str(v) for v in value if v is not None]
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            for parser in (json.loads, ast.literal_eval):
                try:
                    parsed = parser(raw)
                    if isinstance(parsed, (list, tuple, set)):
                        return [str(v) for v in parsed if v is not None]
                except Exception:
                    pass
            return [p.strip() for p in raw.split(",") if p.strip()]
        return [str(value)]

    def _prepare(self, observations: pd.DataFrame) -> pd.DataFrame:
        required = {"goals", "baseline_log_rate", "own_starters", "opponent_starters"}
        missing = sorted(required - set(observations.columns))
        if missing:
            raise ValueError(f"Missing required lineup columns: {missing}")
        df = observations.copy()
        df["goals"] = pd.to_numeric(df["goals"], errors="raise").astype(float)
        df["baseline_log_rate"] = pd.to_numeric(
            df["baseline_log_rate"], errors="raise"
        ).astype(float)
        if (df["goals"] < 0).any():
            raise ValueError("Goals must be non-negative.")
        df["_own"] = df["own_starters"].map(self._parse_ids)
        df["_opp"] = df["opponent_starters"].map(self._parse_ids)
        return df

    def fit(self, observations: pd.DataFrame) -> "LearnedLineupEffectModel":
        df = self._prepare(observations)
        players = sorted(
            {
                p
                for row in df.itertuples(index=False)
                for p in (row._own + row._opp)
            }
        )
        if len(players) < 2 or len(df) < 50:
            raise ValueError("At least 50 team-match observations and 2 players are required.")

        self.player_index = {p: i for i, p in enumerate(players)}
        n = len(players)

        own_matrix = np.zeros((len(df), n), dtype=float)
        opp_matrix = np.zeros((len(df), n), dtype=float)
        for i, row in enumerate(df.itertuples(index=False)):
            for p in row._own:
                if p in self.player_index:
                    own_matrix[i, self.player_index[p]] += 1.0
            for p in row._opp:
                if p in self.player_index:
                    opp_matrix[i, self.player_index[p]] += 1.0

        offset = df["baseline_log_rate"].to_numpy(float)
        y = df["goals"].to_numpy(float)

        def objective(beta: np.ndarray) -> float:
            b_attack = beta[:n]
            b_defence = beta[n:]
            eta = offset + own_matrix @ b_attack + opp_matrix @ b_defence
            eta = np.clip(eta, -12.0, 8.0)
            lam = np.exp(eta)
            nll = np.sum(lam - y * eta)
            penalty = 0.5 * self.l2_attack * np.sum(b_attack ** 2)
            penalty += 0.5 * self.l2_defence * np.sum(b_defence ** 2)
            value = nll + penalty
            return float(value) if np.isfinite(value) else 1e20

        def gradient(beta: np.ndarray) -> np.ndarray:
            b_attack = beta[:n]
            b_defence = beta[n:]
            eta = np.clip(offset + own_matrix @ b_attack + opp_matrix @ b_defence, -12.0, 8.0)
            resid = np.exp(eta) - y
            return np.concatenate(
                [
                    own_matrix.T @ resid + self.l2_attack * b_attack,
                    opp_matrix.T @ resid + self.l2_defence * b_defence,
                ]
            )

        res = minimize(
            objective,
            np.zeros(2 * n, dtype=float),
            jac=gradient,
            method="L-BFGS-B",
            options={"maxiter": 300, "ftol": 1e-10},
        )
        if not res.success:
            raise RuntimeError(f"Lineup-effect optimization failed: {res.message}")

        self.attack_effects = {p: float(res.x[i]) for p, i in self.player_index.items()}
        self.defence_effects = {p: float(res.x[n + i]) for p, i in self.player_index.items()}
        self.fitted = True
        self.metrics = {
            "converged": bool(res.success),
            "n_observations": int(len(df)),
            "n_players": int(n),
            "objective": float(res.fun),
            "l2_attack": self.l2_attack,
            "l2_defence": self.l2_defence,
        }
        return self

    def predict_log_rate_delta(
        self,
        own_starters: Sequence[Any],
        opponent_starters: Sequence[Any],
    ) -> float:
        if not self.fitted:
            raise RuntimeError("Lineup-effect model is not fitted.")
        attack = sum(self.attack_effects.get(str(p), 0.0) for p in own_starters)
        defence = sum(self.defence_effects.get(str(p), 0.0) for p in opponent_starters)
        return float(attack + defence)

    def predict_rate(
        self,
        baseline_rate: float,
        own_starters: Sequence[Any],
        opponent_starters: Sequence[Any],
    ) -> float:
        if baseline_rate <= 0:
            raise ValueError("baseline_rate must be positive.")
        return float(np.exp(np.log(baseline_rate) + self.predict_log_rate_delta(
            own_starters, opponent_starters
        )))

    def serialize(self) -> Dict[str, Any]:
        return {
            "model_type": "LearnedLineupEffectModel",
            "version": "1.0.0",
            "l2_attack": self.l2_attack,
            "l2_defence": self.l2_defence,
            "attack_effects": self.attack_effects,
            "defence_effects": self.defence_effects,
            "metrics": self.metrics,
        }


    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "LearnedLineupEffectModel":
        model = cls(
            l2_attack=float(data.get("l2_attack", 8.0)),
            l2_defence=float(data.get("l2_defence", 8.0)),
        )
        model.attack_effects = {
            str(k): float(v) for k, v in data.get("attack_effects", {}).items()
        }
        model.defence_effects = {
            str(k): float(v) for k, v in data.get("defence_effects", {}).items()
        }
        model.player_index = {
            p: i for i, p in enumerate(sorted(model.attack_effects.keys() | model.defence_effects.keys()))
        }
        model.metrics = dict(data.get("metrics", {}))
        model.fitted = bool(model.attack_effects or model.defence_effects)
        return model
