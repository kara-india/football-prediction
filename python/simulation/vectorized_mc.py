import math
from typing import Any, Dict, Optional, Tuple
import numpy as np

from .match_state import MatchState


class VectorizedMonteCarloSimulator:
    """
    High-performance vectorized Monte Carlo match simulator.
    Simulates thousands of concurrent match trajectories in milliseconds
    using NumPy matrix operations with in-play competing hazards:
    - Path-dependent scoreline chasing/leading feedback
    - Red card penalty (35% goal hazard reduction)
    - Non-linear minute-by-minute hazard decay
    - Empirical standard error calculation with early convergence stopping
    """

    MIN_SIMULATIONS: int = 10_000
    MAX_SIMULATIONS: int = 50_000
    TARGET_STD_ERROR: float = 0.004
    BATCH_SIZE: int = 5_000

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def simulate_batch(
        self,
        state: MatchState,
        home_lambda_per_min: float,
        away_lambda_per_min: float,
        n_simulations: int,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """
        Simulate n_simulations trajectories from the given MatchState simultaneously.
        Returns ndarray of shape (n_simulations, 2) containing [final_home_goals, final_away_goals].
        """
        active_rng = rng if rng is not None else self.rng
        rem_mins = int(math.ceil(state.remaining_minutes))

        if rem_mins <= 0:
            res = np.empty((n_simulations, 2), dtype=np.int32)
            res[:, 0] = state.score_home
            res[:, 1] = state.score_away
            return res

        # Starting scores
        scores = np.empty((n_simulations, 2), dtype=np.int32)
        scores[:, 0] = state.score_home
        scores[:, 1] = state.score_away

        # Precompute red card multipliers (35% reduction in goal intensity for penalized team)
        h_card_mult = (0.65 ** state.red_cards_home) * (1.20 ** state.red_cards_away)
        a_card_mult = (0.65 ** state.red_cards_away) * (1.20 ** state.red_cards_home)

        start_min = state.minute
        end_min = start_min + rem_mins

        # Step through remaining minutes vectorially across all n_simulations paths
        for m in range(start_min, end_min):
            # Empirical minute weight: goals are ~25% more frequent in late stages (75-90')
            clamped_m = min(m, 90)
            time_weight = 0.85 + 0.30 * (clamped_m / 90.0)

            # Score difference: home - away
            diff = scores[:, 0] - scores[:, 1]

            # Vectorized score-state adjustments
            # Home multiplier: cautious when leading (0.95 / 0.88), urgent when trailing (1.08 / 1.15)
            h_state_mult = np.ones(n_simulations, dtype=np.float64)
            h_state_mult[diff == 1] = 0.95
            h_state_mult[diff >= 2] = 0.88
            h_state_mult[diff == -1] = 1.08
            h_state_mult[diff <= -2] = 1.15

            # Away multiplier: urgent when trailing (diff > 0), cautious when leading (diff < 0)
            a_state_mult = np.ones(n_simulations, dtype=np.float64)
            a_state_mult[diff == 1] = 1.08
            a_state_mult[diff >= 2] = 1.15
            a_state_mult[diff == -1] = 0.95
            a_state_mult[diff <= -2] = 0.88

            # Competing hazard intensity
            lam_h = home_lambda_per_min * time_weight * h_card_mult * h_state_mult
            lam_a = away_lambda_per_min * time_weight * a_card_mult * a_state_mult

            # Draw goal occurrences
            scores[:, 0] += active_rng.poisson(lam_h)
            scores[:, 1] += active_rng.poisson(lam_a)

        return scores

    def compute_distributions(self, paths_array: np.ndarray) -> Dict[str, Any]:
        """
        Compute empirical score distributions, marginals, market probabilities,
        and standard error from simulation paths array.
        """
        n_sims = len(paths_array)
        if n_sims == 0:
            return {}

        home_scores = paths_array[:, 0]
        away_scores = paths_array[:, 1]
        total_goals = home_scores + away_scores

        # 1X2 Probabilities
        home_wins = np.sum(home_scores > away_scores)
        draws = np.sum(home_scores == away_scores)
        away_wins = np.sum(home_scores < away_scores)

        p_home = float(home_wins / n_sims)
        p_draw = float(draws / n_sims)
        p_away = float(away_wins / n_sims)

        # Standard error strictly from empirical variance SE = sqrt(p * (1 - p) / N)
        # Using maximum across 1, X, 2 outcomes
        se_home = math.sqrt(p_home * (1.0 - p_home) / n_sims)
        se_draw = math.sqrt(p_draw * (1.0 - p_draw) / n_sims)
        se_away = math.sqrt(p_away * (1.0 - p_away) / n_sims)
        std_error = max(se_home, se_draw, se_away)

        # Over / Under 2.5
        over_25_count = np.sum(total_goals > 2)
        p_over_25 = float(over_25_count / n_sims)
        p_under_25 = 1.0 - p_over_25

        # Both Teams to Score (BTTS)
        btts_count = np.sum((home_scores > 0) & (away_scores > 0))
        p_btts_yes = float(btts_count / n_sims)
        p_btts_no = 1.0 - p_btts_yes

        # Score distribution
        unique_scores, counts = np.unique(paths_array, axis=0, return_counts=True)
        score_distribution = {
            (int(row[0]), int(row[1])): float(count / n_sims)
            for row, count in zip(unique_scores, counts)
        }

        # Total goal distribution
        unique_goals, g_counts = np.unique(total_goals, return_counts=True)
        goal_distribution = {
            int(g): float(c / n_sims)
            for g, c in zip(unique_goals, g_counts)
        }

        return {
            "simulation_count": n_sims,
            "std_error": std_error,
            "score_distribution": score_distribution,
            "goal_distribution": goal_distribution,
            "1x2": {"1": p_home, "X": p_draw, "2": p_away},
            "btts": {"yes": p_btts_yes, "no": p_btts_no},
            "over_under_25": {"over": p_over_25, "under": p_under_25},
        }

    def simulate_with_convergence(
        self,
        state: MatchState,
        home_lambda_per_min: float,
        away_lambda_per_min: float,
        min_simulations: Optional[int] = None,
        max_simulations: Optional[int] = None,
        target_std_error: Optional[float] = None,
        batch_size: Optional[int] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Run vectorized simulation in batches until standard error convergence
        SE <= target_std_error or max_simulations is reached.
        """
        min_sims = min_simulations or self.MIN_SIMULATIONS
        max_sims = max_simulations or self.MAX_SIMULATIONS
        target_se = target_std_error or self.TARGET_STD_ERROR
        b_size = batch_size or self.BATCH_SIZE

        accumulated_paths = []
        total_sims = 0

        while total_sims < max_sims:
            chunk_size = min(b_size, max_sims - total_sims)
            batch = self.simulate_batch(
                state, home_lambda_per_min, away_lambda_per_min, chunk_size, self.rng
            )
            accumulated_paths.append(batch)
            total_sims += chunk_size

            # Check convergence once minimum simulation count is satisfied
            if total_sims >= min_sims:
                current_all = np.vstack(accumulated_paths)
                dist = self.compute_distributions(current_all)
                if dist["std_error"] <= target_se:
                    return current_all, dist

        final_paths = np.vstack(accumulated_paths)
        dist = self.compute_distributions(final_paths)
        return final_paths, dist
