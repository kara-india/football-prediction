from typing import Tuple
from .match_state import MatchState

class EventIntensityEstimator:
    # Empirical minute distribution (normalized)
    GOAL_MINUTE_WEIGHTS = {}
    
    # Score state multipliers (empirically derived)
    SCORE_STATE_MULTIPLIERS = {
        'losing_1': {'attack_mult': 1.08, 'requires_calibration': True},
        'losing_2': {'attack_mult': 1.15, 'requires_calibration': True},
        'winning_1': {'attack_mult': 0.95, 'requires_calibration': True},
        'winning_2': {'attack_mult': 0.88, 'requires_calibration': True},
    }

    def estimate_goal_intensities(self,
                                   state: MatchState,
                                   home_attack: float,
                                   home_defense: float, 
                                   away_attack: float,
                                   away_defense: float,
                                   base_home_lambda: float,
                                   base_away_lambda: float) -> Tuple[float, float]:
        home_lambda = base_home_lambda
        away_lambda = base_away_lambda
        
        diff = state.score_home - state.score_away
        
        # Red card effect (immediate 35% reduction in goal intensity for penalized team)
        if state.red_cards_home > 0:
            home_lambda *= (0.65 ** state.red_cards_home)
            away_lambda *= (1.20 ** state.red_cards_home)
        if state.red_cards_away > 0:
            away_lambda *= (0.65 ** state.red_cards_away)
            home_lambda *= (1.20 ** state.red_cards_away)

        # Score state multipliers
        if diff == 1:
            home_lambda *= self.SCORE_STATE_MULTIPLIERS['winning_1']['attack_mult']
            away_lambda *= self.SCORE_STATE_MULTIPLIERS['losing_1']['attack_mult']
        elif diff >= 2:
            home_lambda *= self.SCORE_STATE_MULTIPLIERS['winning_2']['attack_mult']
            away_lambda *= self.SCORE_STATE_MULTIPLIERS['losing_2']['attack_mult']
        elif diff == -1:
            home_lambda *= self.SCORE_STATE_MULTIPLIERS['losing_1']['attack_mult']
            away_lambda *= self.SCORE_STATE_MULTIPLIERS['winning_1']['attack_mult']
        elif diff <= -2:
            home_lambda *= self.SCORE_STATE_MULTIPLIERS['losing_2']['attack_mult']
            away_lambda *= self.SCORE_STATE_MULTIPLIERS['winning_2']['attack_mult']

        return home_lambda, away_lambda

    def estimate_card_intensities(self, state: MatchState, referee_rate: float) -> Tuple[float, float]:
        return referee_rate, referee_rate

    def estimate_corner_intensities(self, state: MatchState) -> Tuple[float, float]:
        return 0.05, 0.05
