from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import nbinom, poisson


class NegativeBinomialModel:
    """
    Standard negative binomial count model with parameterization:
    mean mu, dispersion parameter phi such that Var = mu + phi * mu^2.
    Number of failures r = 1 / phi, probability p = r / (r + mu).
    """

    def __init__(self, market: str):
        self.market = market
        self.mu_base: float = 4.0
        self.phi_base: float = 0.5
        self.fitted: bool = False

    @staticmethod
    def _neg_log_lik(params: Tuple[float, float], counts: np.ndarray) -> float:
        mu, phi = params
        if mu <= 1e-4 or phi <= 1e-4:
            return 1e9
        r = 1.0 / phi
        p = r / (r + mu)
        ll = nbinom.logpmf(counts, r, p)
        if not np.all(np.isfinite(ll)):
            return 1e9
        return -float(np.sum(ll))

    def fit(self, data: Union[pd.DataFrame, np.ndarray]):
        if isinstance(data, pd.DataFrame):
            counts = data[self.market].dropna().to_numpy(dtype=np.float64)
        else:
            counts = np.asarray(data, dtype=np.float64)

        if len(counts) == 0:
            return

        mean_val = float(np.mean(counts))
        var_val = float(np.var(counts))
        init_phi = max(1e-3, (var_val - mean_val) / max(mean_val**2, 1e-4)) if var_val > mean_val else 0.1

        res = minimize(
            self._neg_log_lik,
            [max(mean_val, 0.1), init_phi],
            args=(counts,),
            bounds=[(1e-3, 50.0), (1e-4, 10.0)],
            method="L-BFGS-B",
        )

        if res.success:
            self.mu_base = float(res.x[0])
            self.phi_base = float(res.x[1])
            self.fitted = True
        else:
            self.mu_base = mean_val
            self.phi_base = max(1e-3, init_phi)

    def predict_exact(self, mu: float, phi: float, k: int) -> float:
        if phi <= 1e-6:
            return float(poisson.pmf(k, mu))
        r = 1.0 / phi
        p = r / (r + mu)
        return float(nbinom.pmf(k, r, p))

    def predict_over_under(self, mu: float, phi: float, line: float) -> Tuple[float, float]:
        if phi <= 1e-6:
            prob_under = float(poisson.cdf(int(np.floor(line)), mu))
            return 1.0 - prob_under, prob_under
        r = 1.0 / phi
        p = r / (r + mu)
        prob_under = float(nbinom.cdf(int(np.floor(line)), r, p))
        return 1.0 - prob_under, prob_under

    def get_team_card_rate(self, team_id: int, is_home: bool) -> float:
        return self.mu_base / 2.0

    def get_referee_card_rate(self, referee_name: str) -> float:
        return self.mu_base

    def predict_match_cards(
        self,
        home_id: int,
        away_id: int,
        referee: Optional[str] = None,
        competition_id: Optional[int] = None,
    ) -> Dict[str, float]:
        mu = self.mu_base
        phi = self.phi_base
        over_35, _ = self.predict_over_under(mu, phi, 3.5)
        over_45, _ = self.predict_over_under(mu, phi, 4.5)
        return {
            "mu": float(mu),
            "phi": float(phi),
            "over_35": float(over_35),
            "over_45": float(over_45),
        }


class GoalCountModel:
    """
    Goal-count distribution selector using likelihood-based model comparison.

    Fits both:
      1) Poisson: Var(Y) = mu
      2) Negative Binomial: Var(Y) = mu + phi * mu^2

    The selected family is determined by BIC, not by a hand-set variance-to-mean
    threshold. This lets the data decide whether observed tail dispersion is
    strong enough to justify the extra parameter.
    """

    def __init__(self):
        self.mu: float = 0.0
        self.phi: float = 0.0
        self.is_overdispersed: bool = False
        self.selected_distribution: str = "poisson"
        self.bic_poisson: Optional[float] = None
        self.bic_negative_binomial: Optional[float] = None
        self.fitted: bool = False

    @staticmethod
    def _poisson_nll(mu: float, data: np.ndarray) -> float:
        if mu <= 0:
            return 1e30
        ll = poisson.logpmf(data, mu)
        return float(-np.sum(ll)) if np.all(np.isfinite(ll)) else 1e30

    @staticmethod
    def _nb_nll(params: Tuple[float, float], data: np.ndarray) -> float:
        mu, phi = params
        if mu <= 0 or phi <= 0:
            return 1e30
        r = 1.0 / phi
        p = r / (r + mu)
        ll = nbinom.logpmf(data, r, p)
        return float(-np.sum(ll)) if np.all(np.isfinite(ll)) else 1e30

    def fit(self, goals: Union[pd.Series, np.ndarray, list]) -> "GoalCountModel":
        data = np.asarray(goals, dtype=float)
        data = data[np.isfinite(data)]
        if data.size < 20:
            raise ValueError("At least 20 goal observations are required for distribution selection.")
        if np.any(data < 0) or np.any(np.floor(data) != data):
            raise ValueError("Goal observations must be non-negative integers.")

        self.mu = max(float(np.mean(data)), 1e-8)
        poisson_nll = self._poisson_nll(self.mu, data)
        n = int(data.size)
        self.bic_poisson = 2.0 * poisson_nll + 1.0 * math.log(n)

        variance = float(np.var(data))
        phi0 = max(1e-4, (variance - self.mu) / max(self.mu ** 2, 1e-8))
        nb_res = minimize(
            self._nb_nll,
            [self.mu, phi0],
            args=(data,),
            bounds=[(1e-8, 50.0), (1e-6, 10.0)],
            method="L-BFGS-B",
            options={"maxiter": 250, "ftol": 1e-10},
        )

        if nb_res.success and np.isfinite(nb_res.fun):
            nb_nll = float(nb_res.fun)
            self.bic_negative_binomial = 2.0 * nb_nll + 2.0 * math.log(n)
            nb_mu, nb_phi = float(nb_res.x[0]), float(nb_res.x[1])
        else:
            self.bic_negative_binomial = float("inf")
            nb_mu, nb_phi = self.mu, 0.0

        if self.bic_negative_binomial + 1e-9 < self.bic_poisson:
            self.selected_distribution = "negative_binomial"
            self.mu = nb_mu
            self.phi = nb_phi
            self.is_overdispersed = True
        else:
            self.selected_distribution = "poisson"
            self.phi = 0.0
            self.is_overdispersed = False

        self.fitted = True
        return self

    def predict_exact(self, k: int, custom_mu: Optional[float] = None) -> float:
        mu = float(custom_mu if custom_mu is not None else self.mu)
        if not self.is_overdispersed or self.phi <= 1e-8:
            return float(poisson.pmf(k, mu))
        r = 1.0 / self.phi
        p = r / (r + mu)
        return float(nbinom.pmf(k, r, p))

    def predict_over_under(
        self,
        line: float,
        custom_mu: Optional[float] = None,
        custom_phi: Optional[float] = None,
    ) -> Tuple[float, float]:
        mu = float(custom_mu if custom_mu is not None else self.mu)
        phi = float(self.phi if custom_phi is None else custom_phi)
        if phi <= 1e-8:
            under = float(poisson.cdf(int(np.floor(line)), mu))
        else:
            r = 1.0 / phi
            p = r / (r + mu)
            under = float(nbinom.cdf(int(np.floor(line)), r, p))
        return 1.0 - under, under


class CardCountModel(NegativeBinomialModel):
    """
    Card count model conditioned on referee strictness, team aggression, and match intensity.
    """

    def __init__(self, base_cards: float = 4.2, phi: float = 0.18):
        super().__init__(market="total_cards")
        self.mu_base = base_cards
        self.phi_base = phi

    def predict_cards_conditioned(
        self,
        referee_strictness: float = 1.0,
        team_home_aggression: float = 1.0,
        team_away_aggression: float = 1.0,
        match_intensity: float = 1.0,
    ) -> Dict[str, float]:
        """
        Condition total card expectation:
        mu = mu_base * referee_strictness * ((home_agg + away_agg) / 2) * match_intensity
        """
        agg = (team_home_aggression + team_away_aggression) / 2.0
        adjusted_mu = self.mu_base * referee_strictness * agg * match_intensity
        phi = self.phi_base

        over_25, under_25 = self.predict_over_under(adjusted_mu, phi, 2.5)
        over_35, under_35 = self.predict_over_under(adjusted_mu, phi, 3.5)
        over_45, under_45 = self.predict_over_under(adjusted_mu, phi, 4.5)
        over_55, under_55 = self.predict_over_under(adjusted_mu, phi, 5.5)

        return {
            "expected_cards": float(round(adjusted_mu, 3)),
            "dispersion_phi": float(round(phi, 4)),
            "over_25": float(round(over_25, 4)),
            "over_35": float(round(over_35, 4)),
            "over_45": float(round(over_45, 4)),
            "over_55": float(round(over_55, 4)),
        }


class CornerCountModel(NegativeBinomialModel):
    """
    Corner count model conditioned on team wing cross frequency and shot volume.
    """

    def __init__(self, base_corners: float = 10.1, phi: float = 0.12):
        super().__init__(market="total_corners")
        self.mu_base = base_corners
        self.phi_base = phi

    def predict_corners_conditioned(
        self,
        home_wing_factor: float = 1.0,
        away_wing_factor: float = 1.0,
        total_shot_volume_factor: float = 1.0,
    ) -> Dict[str, float]:
        """
        Condition total corner expectation:
        mu = mu_base * ((home_wing + away_wing) / 2) * total_shot_volume_factor
        """
        wing = (home_wing_factor + away_wing_factor) / 2.0
        adjusted_mu = self.mu_base * wing * total_shot_volume_factor
        phi = self.phi_base

        over_85, under_85 = self.predict_over_under(adjusted_mu, phi, 8.5)
        over_95, under_95 = self.predict_over_under(adjusted_mu, phi, 9.5)
        over_105, under_105 = self.predict_over_under(adjusted_mu, phi, 10.5)

        return {
            "expected_corners": float(round(adjusted_mu, 3)),
            "dispersion_phi": float(round(phi, 4)),
            "over_85": float(round(over_85, 4)),
            "over_95": float(round(over_95, 4)),
            "over_105": float(round(over_105, 4)),
        }
