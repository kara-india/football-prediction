import time
import math
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import numpy as np

from .match_state import MatchState
from .event_intensities import EventIntensityEstimator

@dataclass
class PathResult:
    final_score_home: int
    final_score_away: int
    total_cards: int
    total_corners: int
    home_scored: bool
    away_scored: bool
    btts: bool
    total_goals: int

@dataclass
class SimulationResult:
    simulation_count: int
    seed: int
    simulation_version: str
    paths: List[PathResult]
    
    score_distribution: Dict[Tuple[int, int], float]
    goal_distribution: Dict[int, float]
    
    @property
    def std_error(self) -> float:
        return 0.0

class MonteCarloSimulator:
    MIN_SIMULATIONS = 10_000
    MAX_SIMULATIONS = 500_000
    TARGET_STD_ERROR = 0.005
    BATCH_SIZE = 5_000
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or int(time.time())
        self.rng = np.random.default_rng(self.seed)
        self.simulation_count = 0

    def simulate_match_from_state(self,
                                   state: MatchState,
                                   home_lambda: float,
                                   away_lambda: float,
                                   intensity_estimator: EventIntensityEstimator,
                                   n_simulations: Optional[int] = None) -> SimulationResult:
        n_sims = n_simulations or self.MIN_SIMULATIONS
        paths = []
        for _ in range(n_sims):
            paths.append(self._simulate_single_path(state, home_lambda, away_lambda, intensity_estimator))
            
        score_dist = {}
        goal_dist = {}
        for p in paths:
            score = (p.final_score_home, p.final_score_away)
            score_dist[score] = score_dist.get(score, 0) + 1
            goal_dist[p.total_goals] = goal_dist.get(p.total_goals, 0) + 1
            
        for k in score_dist:
            score_dist[k] /= n_sims
        for k in goal_dist:
            goal_dist[k] /= n_sims
            
        return SimulationResult(
            simulation_count=n_sims,
            seed=self.seed,
            simulation_version="1.0",
            paths=paths,
            score_distribution=score_dist,
            goal_distribution=goal_dist
        )

    def _simulate_single_path(self, state: MatchState, home_lambda: float, away_lambda: float, intensity_estimator: EventIntensityEstimator) -> PathResult:
        rem_mins = int(math.ceil(state.remaining_minutes))
        
        home_goals = state.score_home
        away_goals = state.score_away
        
        current_state = MatchState(**state.__dict__)
        
        for _ in range(rem_mins):
            h_int, a_int = intensity_estimator.estimate_goal_intensities(
                current_state, 1.0, 1.0, 1.0, 1.0, home_lambda, away_lambda
            )
            
            h_g = self.rng.poisson(h_int)
            a_g = self.rng.poisson(a_int)
            
            home_goals += h_g
            away_goals += a_g
            
            current_state.score_home = home_goals
            current_state.score_away = away_goals
            
        return PathResult(
            final_score_home=home_goals,
            final_score_away=away_goals,
            total_cards=state.yellow_cards_home + state.red_cards_home + state.yellow_cards_away + state.red_cards_away,
            total_corners=state.corners_home + state.corners_away,
            home_scored=home_goals > 0,
            away_scored=away_goals > 0,
            btts=(home_goals > 0 and away_goals > 0),
            total_goals=home_goals + away_goals
        )

    def _check_convergence(self, results: List[PathResult], metric: str) -> Tuple[bool, float]:
        return False, 1.0

    def extract_market_probabilities(self, result: SimulationResult) -> Dict[str, Dict[str, float]]:
        p_1 = sum(prob for (h, a), prob in result.score_distribution.items() if h > a)
        p_x = sum(prob for (h, a), prob in result.score_distribution.items() if h == a)
        p_2 = sum(prob for (h, a), prob in result.score_distribution.items() if h < a)
        
        p_btts_yes = sum(prob for (h, a), prob in result.score_distribution.items() if h > 0 and a > 0)
        p_btts_no = 1.0 - p_btts_yes
        
        p_over_25 = sum(prob for tg, prob in result.goal_distribution.items() if tg > 2.5)
        p_under_25 = 1.0 - p_over_25
        
        return {
            '1x2': {'1': p_1, 'X': p_x, '2': p_2},
            'btts': {'yes': p_btts_yes, 'no': p_btts_no},
            'over_under_25': {'over': p_over_25, 'under': p_under_25}
        }
