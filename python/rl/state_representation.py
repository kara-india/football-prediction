from dataclasses import dataclass
import numpy as np

@dataclass
class RLState:
    # Match state
    minute: float  # normalized 0-1
    score_difference: int  # home - away
    total_goals: int
    red_cards_home: int
    red_cards_away: int
    
    # Market state  
    market: str
    selection: str
    decimal_odds: float  # normalized log scale
    implied_probability: float
    
    # Model output
    calibrated_probability: float
    raw_probability: float
    expected_value: float
    probability_lower: float
    probability_upper: float
    uncertainty: float
    
    # Quality signals
    data_freshness_score: float  # 1.0=fresh, 0.0=stale
    odds_freshness_score: float
    model_confidence: float
    simulation_count_log: float  # log10(simulation_count)
    
    # Context
    is_live: bool
    competition_tier: int  # 1=top, 2=second, etc.
    market_history_n: int  # # of historical predictions for this market
    
    def to_array(self) -> np.ndarray:
        # Convert to flat numpy array for model input
        # All values normalized to [0,1] or [-1,1]
        norm_score_diff = max(min(self.score_difference / 5.0, 1.0), -1.0)
        norm_total_goals = min(self.total_goals / 10.0, 1.0)
        
        return np.array([
            self.minute,
            norm_score_diff,
            norm_total_goals,
            min(self.red_cards_home / 3.0, 1.0),
            min(self.red_cards_away / 3.0, 1.0),
            min(np.log10(max(self.decimal_odds, 1.01)) / 3.0, 1.0), 
            self.implied_probability,
            self.calibrated_probability,
            self.raw_probability,
            max(min(self.expected_value / 2.0, 1.0), -1.0),
            self.probability_lower,
            self.probability_upper,
            self.uncertainty,
            self.data_freshness_score,
            self.odds_freshness_score,
            self.model_confidence,
            min(self.simulation_count_log / 6.0, 1.0),
            1.0 if self.is_live else 0.0,
            1.0 / self.competition_tier if self.competition_tier > 0 else 0.0,
            min(self.market_history_n / 1000.0, 1.0)
        ], dtype=np.float32)
    
    @classmethod
    def from_candidate(cls, candidate, match_state) -> 'RLState':
        return cls(
            minute=match_state.minute if hasattr(match_state, 'minute') else 0.0,
            score_difference=match_state.score_difference if hasattr(match_state, 'score_difference') else 0,
            total_goals=match_state.total_goals if hasattr(match_state, 'total_goals') else 0,
            red_cards_home=match_state.red_cards_home if hasattr(match_state, 'red_cards_home') else 0,
            red_cards_away=match_state.red_cards_away if hasattr(match_state, 'red_cards_away') else 0,
            market=candidate.market if hasattr(candidate, 'market') else '',
            selection=candidate.selection if hasattr(candidate, 'selection') else '',
            decimal_odds=candidate.decimal_odds if hasattr(candidate, 'decimal_odds') else 1.0,
            implied_probability=candidate.implied_probability if hasattr(candidate, 'implied_probability') else 0.0,
            calibrated_probability=candidate.calibrated_probability if hasattr(candidate, 'calibrated_probability') else 0.0,
            raw_probability=candidate.raw_probability if hasattr(candidate, 'raw_probability') else 0.0,
            expected_value=candidate.expected_value if hasattr(candidate, 'expected_value') else 0.0,
            probability_lower=candidate.probability_lower if hasattr(candidate, 'probability_lower') else 0.0,
            probability_upper=candidate.probability_upper if hasattr(candidate, 'probability_upper') else 0.0,
            uncertainty=candidate.uncertainty if hasattr(candidate, 'uncertainty') else 0.0,
            data_freshness_score=candidate.data_freshness_score if hasattr(candidate, 'data_freshness_score') else 1.0,
            odds_freshness_score=candidate.odds_freshness_score if hasattr(candidate, 'odds_freshness_score') else 1.0,
            model_confidence=candidate.model_confidence if hasattr(candidate, 'model_confidence') else 1.0,
            simulation_count_log=candidate.simulation_count_log if hasattr(candidate, 'simulation_count_log') else 0.0,
            is_live=match_state.is_live if hasattr(match_state, 'is_live') else False,
            competition_tier=match_state.competition_tier if hasattr(match_state, 'competition_tier') else 1,
            market_history_n=candidate.market_history_n if hasattr(candidate, 'market_history_n') else 0
        )
