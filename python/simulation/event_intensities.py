from typing import Optional, Tuple

from .match_state import MatchState


class EventIntensityEstimator:
    """
    Goal/event intensity adapter.

    Production goal-state effects come only from a fitted LearnedLiveHazard
    model. Without a fitted model, the estimator returns the supplied baseline
    intensities unchanged instead of applying hand-written multipliers.
    """

    def __init__(self, live_hazard_model: Optional[object] = None):
        self.live_hazard_model = live_hazard_model

    @property
    def trained(self) -> bool:
        return bool(
            self.live_hazard_model is not None
            and getattr(self.live_hazard_model, "fitted", False)
        )

    def estimate_goal_intensities(
        self,
        state: MatchState,
        home_attack: float,
        home_defense: float,
        away_attack: float,
        away_defense: float,
        base_home_lambda: float,
        base_away_lambda: float,
    ) -> Tuple[float, float]:
        home_lambda = float(base_home_lambda)
        away_lambda = float(base_away_lambda)

        if not self.trained:
            return home_lambda, away_lambda

        diff = float(state.score_home - state.score_away)
        red_diff = float(state.red_cards_home - state.red_cards_away)
        sot_diff = float(state.shots_on_target_home - state.shots_on_target_away)
        xg_diff = float(state.xg_home - state.xg_away)
        sub_diff = float(state.substitutions_home - state.substitutions_away)
        knockout_context = float(getattr(state, "knockout_context", 0.0))

        home_multiplier = float(self.live_hazard_model.correction_multiplier(
            minute=float(state.minute),
            score_diff=diff,
            red_card_diff=red_diff,
            shots_on_target_diff=sot_diff,
            xg_diff=xg_diff,
            substitution_diff=sub_diff,
            knockout_context=knockout_context,
            home_indicator=1.0,
        )[0])

        away_multiplier = float(self.live_hazard_model.correction_multiplier(
            minute=float(state.minute),
            score_diff=-diff,
            red_card_diff=-red_diff,
            shots_on_target_diff=-sot_diff,
            xg_diff=-xg_diff,
            substitution_diff=-sub_diff,
            knockout_context=knockout_context,
            home_indicator=0.0,
        )[0])

        return home_lambda * home_multiplier, away_lambda * away_multiplier

    def estimate_card_intensities(
        self,
        state: MatchState,
        referee_rate: float,
    ) -> Tuple[float, float]:
        return float(referee_rate), float(referee_rate)

    def estimate_corner_intensities(
        self,
        state: MatchState,
    ) -> Tuple[float, float]:
        # Corners require their own fitted count process; never fabricate a rate.
        raise RuntimeError(
            "Corner intensity model is not fitted. Refusing to use a hard-coded rate."
        )
