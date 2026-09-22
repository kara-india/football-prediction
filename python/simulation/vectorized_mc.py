import numpy as np
from typing import Dict
from .match_state import MatchState

class VectorizedMonteCarloSimulator:
    def simulate_batch(self, state: MatchState,
                       home_lambda_per_min: float,
                       away_lambda_per_min: float,
                       n_simulations: int) -> np.ndarray:
        rem_mins = int(np.ceil(state.remaining_minutes))
        if rem_mins <= 0:
            return np.zeros((n_simulations, 2), dtype=int)
            
        h_events = np.random.poisson(home_lambda_per_min, (n_simulations, rem_mins))
        a_events = np.random.poisson(away_lambda_per_min, (n_simulations, rem_mins))
        
        h_total = np.sum(h_events, axis=1) + state.score_home
        a_total = np.sum(a_events, axis=1) + state.score_away
        
        return np.column_stack((h_total, a_total))
        
    def compute_distributions(self, paths_array: np.ndarray) -> Dict:
        return {}
