import pandas as pd
from scipy.stats import nbinom
import numpy as np
from scipy.optimize import minimize

class NegativeBinomialModel:
    def __init__(self, market: str):
        self.market = market
        self.params = {} 
        self.mu_base = 4.0
        self.phi_base = 0.5
        
    def _neg_log_lik(self, params, counts):
        mu, phi = params
        if mu <= 0 or phi <= 0:
            return 1e9
        r = 1.0 / phi
        p = r / (r + mu)
        ll = nbinom.logpmf(counts, r, p)
        return -np.sum(ll)

    def fit(self, data: pd.DataFrame):
        counts = data[self.market].values
        res = minimize(
            self._neg_log_lik,
            [np.mean(counts), 0.1],
            args=(counts,),
            bounds=[(1e-3, None), (1e-3, None)]
        )
        self.mu_base = res.x[0]
        self.phi_base = res.x[1]
        
    def predict_over_under(self, mu: float, phi: float, line: float) -> tuple[float, float]:
        r = 1.0 / phi
        p = r / (r + mu)
        prob_under = nbinom.cdf(np.floor(line), r, p)
        return 1.0 - prob_under, prob_under
        
    def predict_exact(self, mu: float, phi: float, k: int) -> float:
        r = 1.0 / phi
        p = r / (r + mu)
        return nbinom.pmf(k, r, p)
        
    def get_team_card_rate(self, team_id: int, is_home: bool) -> float:
        return self.mu_base / 2.0
        
    def get_referee_card_rate(self, referee_name: str) -> float:
        return self.mu_base
        
    def predict_match_cards(self, home_id: int, away_id: int, 
                            referee: str = None, competition_id: int = None) -> dict:
        mu = self.mu_base
        phi = self.phi_base
        over_35, _ = self.predict_over_under(mu, phi, 3.5)
        over_45, _ = self.predict_over_under(mu, phi, 4.5)
        return {
            'mu': float(mu),
            'phi': float(phi),
            'over_35': float(over_35),
            'over_45': float(over_45)
        }
