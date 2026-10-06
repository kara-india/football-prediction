import math
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .match_state import MatchState
from python.models.live_hazard import LearnedLiveHazard


class VectorizedMonteCarloSimulator:
    """
    Vectorized Monte Carlo simulator.

    The simulator itself is a probability propagation mechanism. It does not
    contain hand-written football effects. Optional live corrections must come
    from a fitted LearnedLiveHazard model.
    """

    MIN_SIMULATIONS: int = 10_000
    MAX_SIMULATIONS: int = 50_000
    TARGET_STD_ERROR: float = 0.004
    BATCH_SIZE: int = 5_000

    def __init__(
        self,
        seed: Optional[int] = None,
        live_hazard_model: Optional[LearnedLiveHazard] = None,
    ):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.live_hazard_model = live_hazard_model

    def simulate_batch(
        self,
        state: MatchState,
        home_lambda_per_min: float,
        away_lambda_per_min: float,
        n_simulations: int,
        rng: Optional[np.random.Generator] = None,
        live_hazard_model: Optional[LearnedLiveHazard] = None,
    ) -> np.ndarray:
        active_rng = rng if rng is not None else self.rng
        rem_mins = int(math.ceil(state.remaining_minutes))

        if rem_mins <= 0:
            res = np.empty((n_simulations, 2), dtype=np.int32)
            res[:, 0] = state.score_home
            res[:, 1] = state.score_away
            return res

        scores = np.empty((n_simulations, 2), dtype=np.int32)
        scores[:, 0] = state.score_home
        scores[:, 1] = state.score_away

        hazard = live_hazard_model or self.live_hazard_model
        hazard_ready = bool(hazard is not None and getattr(hazard, "fitted", False))

        start_min = int(state.minute)
        end_min = start_min + rem_mins

        for minute in range(start_min, end_min):
            if hazard_ready:
                diff = scores[:, 0].astype(float) - scores[:, 1].astype(float)
                red_diff = float(state.red_cards_home - state.red_cards_away)
                sot_diff = float(state.shots_on_target_home - state.shots_on_target_away)
                xg_diff = float(state.xg_home - state.xg_away)
                sub_diff = float(state.substitutions_home - state.substitutions_away)
                knockout_context = float(getattr(state, "knockout_context", 0.0))

                home_corr = hazard.correction_multiplier(
                    minute=np.full(n_simulations, float(minute)),
                    score_diff=diff,
                    red_card_diff=np.full(n_simulations, red_diff),
                    shots_on_target_diff=np.full(n_simulations, sot_diff),
                    xg_diff=np.full(n_simulations, xg_diff),
                    substitution_diff=np.full(n_simulations, sub_diff),
                    knockout_context=np.full(n_simulations, knockout_context),
                    home_indicator=np.ones(n_simulations),
                )
                away_corr = hazard.correction_multiplier(
                    minute=np.full(n_simulations, float(minute)),
                    score_diff=-diff,
                    red_card_diff=np.full(n_simulations, -red_diff),
                    shots_on_target_diff=np.full(n_simulations, -sot_diff),
                    xg_diff=np.full(n_simulations, -xg_diff),
                    substitution_diff=np.full(n_simulations, -sub_diff),
                    knockout_context=np.full(n_simulations, knockout_context),
                    home_indicator=np.zeros(n_simulations),
                )

                lam_h = np.maximum(
                    1e-12,
                    float(home_lambda_per_min) * home_corr,
                )
                lam_a = np.maximum(
                    1e-12,
                    float(away_lambda_per_min) * away_corr,
                )
            else:
                # Neutral propagation. No hard-coded red-card, late-game, or
                # score-state assumptions are applied without a trained model.
                lam_h = np.full(n_simulations, float(home_lambda_per_min))
                lam_a = np.full(n_simulations, float(away_lambda_per_min))

            scores[:, 0] += active_rng.poisson(lam_h)
            scores[:, 1] += active_rng.poisson(lam_a)

        return scores

    def compute_distributions(self, paths_array: np.ndarray) -> Dict[str, Any]:
        n_sims = len(paths_array)
        if n_sims == 0:
            return {}

        home_scores = paths_array[:, 0]
        away_scores = paths_array[:, 1]
        total_goals = home_scores + away_scores

        home_wins = np.sum(home_scores > away_scores)
        draws = np.sum(home_scores == away_scores)
        away_wins = np.sum(home_scores < away_scores)

        p_home = float(home_wins / n_sims)
        p_draw = float(draws / n_sims)
        p_away = float(away_wins / n_sims)

        se_home = math.sqrt(p_home * (1.0 - p_home) / n_sims)
        se_draw = math.sqrt(p_draw * (1.0 - p_draw) / n_sims)
        se_away = math.sqrt(p_away * (1.0 - p_away) / n_sims)
        std_error = max(se_home, se_draw, se_away)

        over_25_count = np.sum(total_goals > 2)
        p_over_25 = float(over_25_count / n_sims)
        p_under_25 = 1.0 - p_over_25

        btts_count = np.sum((home_scores > 0) & (away_scores > 0))
        p_btts_yes = float(btts_count / n_sims)
        p_btts_no = 1.0 - p_btts_yes

        unique_scores, counts = np.unique(paths_array, axis=0, return_counts=True)
        score_distribution = {
            (int(row[0]), int(row[1])): float(count / n_sims)
            for row, count in zip(unique_scores, counts)
        }

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
        live_hazard_model: Optional[LearnedLiveHazard] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        min_sims = min_simulations or self.MIN_SIMULATIONS
        max_sims = max_simulations or self.MAX_SIMULATIONS
        target_se = target_std_error or self.TARGET_STD_ERROR
        b_size = batch_size or self.BATCH_SIZE

        accumulated_paths = []
        total_sims = 0

        while total_sims < max_sims:
            chunk_size = min(b_size, max_sims - total_sims)
            batch = self.simulate_batch(
                state,
                home_lambda_per_min,
                away_lambda_per_min,
                chunk_size,
                self.rng,
                live_hazard_model=live_hazard_model,
            )
            accumulated_paths.append(batch)
            total_sims += chunk_size

            if total_sims >= min_sims:
                current_all = np.vstack(accumulated_paths)
                dist = self.compute_distributions(current_all)
                if dist["std_error"] <= target_se:
                    return current_all, dist

        final_paths = np.vstack(accumulated_paths)
        return final_paths, self.compute_distributions(final_paths)
