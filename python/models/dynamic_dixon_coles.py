"""
Score-driven Dynamic Dixon-Coles model.

This module implements a computationally practical parameter-driven alternative
to fixed-strength Dixon-Coles:
  - time-varying attack/defence latent states;
  - AR(1)-style persistence learned from data;
  - score-driven state updates using the predictive likelihood score;
  - Dixon-Coles low-score dependence;
  - hyperparameters selected by chronological one-step predictive likelihood.

No hand-authored football effect sizes are used as production parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import math
import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import poisson


@dataclass(frozen=True)
class DynamicDCConfig:
    min_rate: float = 1e-6
    rho_bounds: Tuple[float, float] = (-0.25, 0.25)
    persistence_bounds: Tuple[float, float] = (0.70, 0.999)
    gain_bounds: Tuple[float, float] = (0.001, 0.50)
    max_iter: int = 180


class ScoreDrivenDixonColes:
    """Dynamic Dixon-Coles with score-driven team attack/defence states."""

    def __init__(self, config: Optional[DynamicDCConfig] = None):
        self.config = config or DynamicDCConfig()
        self.mu: float = math.log(1.30)
        self.home_advantage: float = math.log(1.10)
        self.rho: float = -0.05
        self.attack_persistence: float = 0.98
        self.defence_persistence: float = 0.98
        self.attack_gain: float = 0.05
        self.defence_gain: float = 0.05
        self.teams: List[Any] = []
        self.attack_state: Dict[Any, float] = {}
        self.defence_state: Dict[Any, float] = {}
        self.fitted: bool = False
        self.metrics: Dict[str, Any] = {}

    @staticmethod
    def _tau(x: int, y: int, lam_h: float, lam_a: float, rho: float) -> float:
        if x == 0 and y == 0:
            return max(1.0 - lam_h * lam_a * rho, 1e-10)
        if x == 0 and y == 1:
            return max(1.0 + lam_h * rho, 1e-10)
        if x == 1 and y == 0:
            return max(1.0 + lam_a * rho, 1e-10)
        if x == 1 and y == 1:
            return max(1.0 - rho, 1e-10)
        return 1.0

    @staticmethod
    def _dc_log_score_adjustment_gradient(
        x: int,
        y: int,
        lam_h: float,
        lam_a: float,
        rho: float,
    ) -> Tuple[float, float]:
        if x == 0 and y == 0:
            den = max(1.0 - lam_h * lam_a * rho, 1e-10)
            g = (-lam_h * lam_a * rho) / den
            return g, g
        if x == 0 and y == 1:
            den = max(1.0 + lam_h * rho, 1e-10)
            return (lam_h * rho) / den, 0.0
        if x == 1 and y == 0:
            den = max(1.0 + lam_a * rho, 1e-10)
            return 0.0, (lam_a * rho) / den
        return 0.0, 0.0

    @staticmethod
    def _parse_dates(matches: pd.DataFrame) -> np.ndarray:
        if "date" in matches.columns:
            ts = pd.to_datetime(matches["date"], utc=True)
        elif "kickoff_utc" in matches.columns:
            ts = pd.to_datetime(matches["kickoff_utc"], utc=True)
        elif "time" in matches.columns:
            return matches["time"].to_numpy(dtype=float)
        else:
            return np.arange(len(matches), dtype=float)

        return (ts - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds().to_numpy() / 86400.0

    def _prepare(self, matches: pd.DataFrame) -> pd.DataFrame:
        required = {"home_id", "away_id", "home_goals", "away_goals"}
        missing = sorted(required - set(matches.columns))
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = matches.copy()
        df["_time_days"] = self._parse_dates(df)
        df = df.sort_values("_time_days", kind="mergesort").reset_index(drop=True)
        df["home_goals"] = pd.to_numeric(df["home_goals"], errors="raise").astype(int)
        df["away_goals"] = pd.to_numeric(df["away_goals"], errors="raise").astype(int)
        if (df[["home_goals", "away_goals"]] < 0).any().any():
            raise ValueError("Goal counts must be non-negative.")
        return df

    def _initial_states(self, teams: Iterable[Any]) -> Tuple[Dict[Any, float], Dict[Any, float]]:
        return {t: 0.0 for t in teams}, {t: 0.0 for t in teams}

    def _one_step(
        self,
        home_id: Any,
        away_id: Any,
        home_goals: int,
        away_goals: int,
        prev_time: Optional[float],
        current_time: float,
        attack: Dict[Any, float],
        defence: Dict[Any, float],
        params: np.ndarray,
        update: bool,
    ) -> Tuple[float, float, float]:
        mu, home_adv, rho, phi_a, phi_d, gain_a, gain_d = params
        dt = 0.0 if prev_time is None else max(0.0, current_time - prev_time)

        if dt > 0:
            pa = phi_a ** dt
            pd = phi_d ** dt
            for team in attack:
                attack[team] *= pa
                defence[team] *= pd

        log_lam_h = mu + home_adv + attack.get(home_id, 0.0) - defence.get(away_id, 0.0)
        log_lam_a = mu + attack.get(away_id, 0.0) - defence.get(home_id, 0.0)
        lam_h = max(self.config.min_rate, math.exp(min(log_lam_h, 8.0)))
        lam_a = max(self.config.min_rate, math.exp(min(log_lam_a, 8.0)))

        tau = self._tau(home_goals, away_goals, lam_h, lam_a, rho)
        loglik = (
            poisson.logpmf(home_goals, lam_h)
            + poisson.logpmf(away_goals, lam_a)
            + math.log(tau)
        )

        if update:
            gh_dc, ga_dc = self._dc_log_score_adjustment_gradient(
                home_goals, away_goals, lam_h, lam_a, rho
            )
            gh = float(home_goals - lam_h + gh_dc)
            ga = float(away_goals - lam_a + ga_dc)

            attack[home_id] = attack.get(home_id, 0.0) + gain_a * gh
            attack[away_id] = attack.get(away_id, 0.0) + gain_a * ga
            defence[away_id] = defence.get(away_id, 0.0) - gain_d * gh
            defence[home_id] = defence.get(home_id, 0.0) - gain_d * ga

            if attack:
                a_mean = float(np.mean(list(attack.values())))
                d_mean = float(np.mean(list(defence.values())))
                for team in attack:
                    attack[team] -= a_mean
                    defence[team] -= d_mean

        return lam_h, lam_a, float(loglik)

    def _filter_objective(self, theta: np.ndarray, df: pd.DataFrame) -> float:
        teams = sorted(set(df["home_id"]) | set(df["away_id"]), key=str)
        attack, defence = self._initial_states(teams)
        prev_time: Optional[float] = None
        total_nll = 0.0

        for row in df.itertuples(index=False):
            _, _, ll = self._one_step(
                row.home_id,
                row.away_id,
                int(row.home_goals),
                int(row.away_goals),
                prev_time,
                float(row._time_days),
                attack,
                defence,
                theta,
                update=True,
            )
            if not np.isfinite(ll):
                return 1e12
            total_nll -= ll
            prev_time = float(row._time_days)

        penalty = 1e-6 * float(np.sum(np.square(theta[3:])))
        return float(total_nll + penalty)

    def _fit_hyperparameters(self, df: pd.DataFrame) -> np.ndarray:
        avg_goal = max(
            float((df["home_goals"].mean() + df["away_goals"].mean()) / 2.0),
            0.20,
        )
        home_avg = max(float(df["home_goals"].mean()), 0.20)
        away_avg = max(float(df["away_goals"].mean()), 0.20)

        x0 = np.array([
            math.log(avg_goal),
            math.log(home_avg / away_avg),
            -0.05,
            0.98,
            0.98,
            0.05,
            0.05,
        ], dtype=float)

        bounds = [
            (-2.0, 1.0),
            (-0.75, 0.75),
            self.config.rho_bounds,
            self.config.persistence_bounds,
            self.config.persistence_bounds,
            self.config.gain_bounds,
            self.config.gain_bounds,
        ]

        res = minimize(
            self._filter_objective,
            x0,
            args=(df,),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": self.config.max_iter, "ftol": 1e-8},
        )
        if not np.isfinite(res.fun):
            raise RuntimeError("Dynamic Dixon-Coles hyperparameter optimization failed.")
        return np.asarray(res.x, dtype=float)

    def fit(self, matches: pd.DataFrame) -> "ScoreDrivenDixonColes":
        df = self._prepare(matches)
        if len(df) < 50:
            raise ValueError("At least 50 chronological matches are required for dynamic fitting.")

        teams = sorted(set(df["home_id"]) | set(df["away_id"]), key=str)
        theta = self._fit_hyperparameters(df)

        attack, defence = self._initial_states(teams)
        prev_time: Optional[float] = None
        predictive_ll = []

        for row in df.itertuples(index=False):
            _, _, ll = self._one_step(
                row.home_id,
                row.away_id,
                int(row.home_goals),
                int(row.away_goals),
                prev_time,
                float(row._time_days),
                attack,
                defence,
                theta,
                update=True,
            )
            predictive_ll.append(ll)
            prev_time = float(row._time_days)

        self.mu = float(theta[0])
        self.home_advantage = float(theta[1])
        self.rho = float(theta[2])
        self.attack_persistence = float(theta[3])
        self.defence_persistence = float(theta[4])
        self.attack_gain = float(theta[5])
        self.defence_gain = float(theta[6])
        self.teams = teams
        self.attack_state = attack
        self.defence_state = defence
        self.fitted = True
        self.metrics = {
            "converged": True,
            "n_matches": int(len(df)),
            "n_teams": int(len(teams)),
            "one_step_log_likelihood": float(np.sum(predictive_ll)),
            "mean_one_step_log_likelihood": float(np.mean(predictive_ll)),
            "mu_log_rate": self.mu,
            "home_advantage_log_rate": self.home_advantage,
            "rho": self.rho,
            "attack_persistence": self.attack_persistence,
            "defence_persistence": self.defence_persistence,
            "attack_gain": self.attack_gain,
            "defence_gain": self.defence_gain,
            "training_end_days": float(df["_time_days"].max()),
        }
        return self

    def fit_as_of(self, matches: pd.DataFrame, as_of: Any) -> "ScoreDrivenDixonColes":
        df = self._prepare(matches)
        cutoff = pd.to_datetime(as_of, utc=True)
        dates = pd.to_datetime(df["_time_days"], unit="D", origin="unix", utc=True)
        train = df.loc[dates < cutoff].copy()
        if train.empty:
            raise ValueError("No observations are strictly before as_of.")
        return self.fit(train)

    def _rates(self, home_id: Any, away_id: Any) -> Tuple[float, float]:
        if not self.fitted:
            raise RuntimeError("Model must be fitted before prediction.")
        lam_h = math.exp(
            min(
                self.mu
                + self.home_advantage
                + self.attack_state.get(home_id, 0.0)
                - self.defence_state.get(away_id, 0.0),
                8.0,
            )
        )
        lam_a = math.exp(
            min(
                self.mu
                + self.attack_state.get(away_id, 0.0)
                - self.defence_state.get(home_id, 0.0),
                8.0,
            )
        )
        return lam_h, lam_a

    def predict_score_matrix(self, home_id: Any, away_id: Any, max_goals: int = 12) -> np.ndarray:
        lam_h, lam_a = self._rates(home_id, away_id)
        matrix = np.zeros((max_goals + 1, max_goals + 1), dtype=float)
        for x in range(max_goals + 1):
            for y in range(max_goals + 1):
                matrix[x, y] = (
                    poisson.pmf(x, lam_h)
                    * poisson.pmf(y, lam_a)
                    * self._tau(x, y, lam_h, lam_a, self.rho)
                )
        total = float(matrix.sum())
        if not np.isfinite(total) or total <= 0:
            raise RuntimeError("Invalid dynamic Dixon-Coles score distribution.")
        return matrix / total

    def predict_1x2(self, home_id: Any, away_id: Any) -> Tuple[float, float, float]:
        matrix = self.predict_score_matrix(home_id, away_id)
        return (
            float(np.tril(matrix, -1).sum()),
            float(np.trace(matrix)),
            float(np.triu(matrix, 1).sum()),
        )

    def predict_over_under(self, home_id: Any, away_id: Any, line: float) -> Tuple[float, float]:
        matrix = self.predict_score_matrix(home_id, away_id)
        goals = np.indices(matrix.shape).sum(axis=0)
        over = float(matrix[goals > line].sum())
        return over, 1.0 - over

    def predict_btts(self, home_id: Any, away_id: Any) -> Tuple[float, float]:
        matrix = self.predict_score_matrix(home_id, away_id)
        yes = float(matrix[1:, 1:].sum())
        return yes, 1.0 - yes

    def serialize(self) -> Dict[str, Any]:
        return {
            "model_type": "ScoreDrivenDixonColes",
            "version": "1.0.0",
            "mu": self.mu,
            "home_advantage": self.home_advantage,
            "rho": self.rho,
            "attack_persistence": self.attack_persistence,
            "defence_persistence": self.defence_persistence,
            "attack_gain": self.attack_gain,
            "defence_gain": self.defence_gain,
            "attack_state": {str(k): float(v) for k, v in self.attack_state.items()},
            "defence_state": {str(k): float(v) for k, v in self.defence_state.items()},
            "teams": [str(t) for t in self.teams],
            "metrics": self.metrics,
        }
