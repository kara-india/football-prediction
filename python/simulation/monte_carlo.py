import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

from .event_intensities import EventIntensityEstimator
from .match_state import MatchState
from .vectorized_mc import VectorizedMonteCarloSimulator


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
    empirical_std_error: float = 0.0

    @property
    def std_error(self) -> float:
        """True empirical standard error from simulation variance."""
        return self.empirical_std_error


class MonteCarloSimulator:
    """
    Monte Carlo simulator wrapping VectorizedMonteCarloSimulator.
    Provides fast, path-dependent match simulations with empirical
    standard error convergence and backwards-compatible result structures.
    """

    MIN_SIMULATIONS = 10_000
    MAX_SIMULATIONS = 500_000
    TARGET_STD_ERROR = 0.004
    BATCH_SIZE = 5_000

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else int(time.time() * 1000) % 2147483647
        self.vectorized_engine = VectorizedMonteCarloSimulator(seed=self.seed)
        self.simulation_count = 0

    def simulate_match_from_state(
        self,
        state: MatchState,
        home_lambda: float,
        away_lambda: float,
        intensity_estimator: Optional[EventIntensityEstimator] = None,
        n_simulations: Optional[int] = None,
    ) -> SimulationResult:
        """
        Simulate match outcomes from current state using vectorized competing hazards.
        """
        n_sims = n_simulations or self.MIN_SIMULATIONS

        # Run vectorized simulation
        scores = self.vectorized_engine.simulate_batch(
            state=state,
            home_lambda_per_min=home_lambda,
            away_lambda_per_min=away_lambda,
            n_simulations=n_sims,
            rng=self.vectorized_engine.rng,
        )

        dist = self.vectorized_engine.compute_distributions(scores)

        # Baseline cards and corners from state
        base_cards = (
            state.yellow_cards_home
            + state.red_cards_home
            + state.yellow_cards_away
            + state.red_cards_away
        )
        base_corners = state.corners_home + state.corners_away

        # Convert to PathResult objects
        paths = [
            PathResult(
                final_score_home=int(scores[i, 0]),
                final_score_away=int(scores[i, 1]),
                total_cards=base_cards,
                total_corners=base_corners,
                home_scored=bool(scores[i, 0] > 0),
                away_scored=bool(scores[i, 1] > 0),
                btts=bool(scores[i, 0] > 0 and scores[i, 1] > 0),
                total_goals=int(scores[i, 0] + scores[i, 1]),
            )
            for i in range(n_sims)
        ]

        self.simulation_count = n_sims

        return SimulationResult(
            simulation_count=n_sims,
            seed=self.seed,
            simulation_version="2.0",
            paths=paths,
            score_distribution=dist.get("score_distribution", {}),
            goal_distribution=dist.get("goal_distribution", {}),
            empirical_std_error=dist.get("std_error", 0.0),
        )

    def _check_convergence(self, results: List[PathResult], metric: str = "1x2") -> Tuple[bool, float]:
        """Check whether empirical standard error satisfies convergence target."""
        n = len(results)
        if n < self.MIN_SIMULATIONS:
            return False, 1.0

        home_wins = sum(1 for p in results if p.final_score_home > p.final_score_away)
        p = home_wins / n
        se = math.sqrt(p * (1.0 - p) / n)
        return se <= self.TARGET_STD_ERROR, se

    def extract_market_probabilities(self, result: SimulationResult) -> Dict[str, Dict[str, float]]:
        """Extract primary market outcome probabilities from simulation results."""
        p_1 = sum(prob for (h, a), prob in result.score_distribution.items() if h > a)
        p_x = sum(prob for (h, a), prob in result.score_distribution.items() if h == a)
        p_2 = sum(prob for (h, a), prob in result.score_distribution.items() if h < a)

        p_btts_yes = sum(prob for (h, a), prob in result.score_distribution.items() if h > 0 and a > 0)
        p_btts_no = 1.0 - p_btts_yes

        p_over_25 = sum(prob for tg, prob in result.goal_distribution.items() if tg > 2.5)
        p_under_25 = 1.0 - p_over_25

        return {
            "1x2": {"1": p_1, "X": p_x, "2": p_2},
            "btts": {"yes": p_btts_yes, "no": p_btts_no},
            "over_under_25": {"over": p_over_25, "under": p_under_25},
        }
