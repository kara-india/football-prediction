import numpy as np

class EVCalculator:
    def compute_ev_binary(self, calibrated_prob: float, decimal_odds: float) -> float:
        return calibrated_prob * decimal_odds - 1.0
    
    def compute_ev_full_distribution(self, outcome_probs: dict[str, float],
                                      outcome_payouts: dict[str, float]) -> float:
        ev = 0.0
        for outcome, prob in outcome_probs.items():
            if outcome in outcome_payouts:
                ev += prob * outcome_payouts[outcome]
        return ev - 1.0  # assuming 1 unit stake
    
    def compute_implied_probability(self, decimal_odds: float) -> float:
        return 1.0 / decimal_odds
    
    def compute_margin(self, all_odds: list[float]) -> float:
        return sum(1.0 / odds for odds in all_odds) - 1.0
    
    def de_vig_multiplicative(self, odds: list[float]) -> list[float]:
        implied_probs = [1.0 / o for o in odds]
        total_implied = sum(implied_probs)
        return [p / total_implied for p in implied_probs]
    
    def compute_probability_interval(self, 
                                      simulation_results: list[float],
                                      confidence: float = 0.95) -> tuple[float, float]:
        alpha = 1.0 - confidence
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        lower = float(np.percentile(simulation_results, lower_percentile))
        upper = float(np.percentile(simulation_results, upper_percentile))
        return (lower, upper)
    
    def compute_kelly_fraction(self, calibrated_prob: float, 
                                decimal_odds: float,
                                fraction: float = 0.25) -> float:
        # Kelly = (p*odds - 1) / (odds - 1)
        b = decimal_odds - 1.0
        if b <= 0:
            return 0.0
        p = calibrated_prob
        q = 1.0 - p
        kelly = (b * p - q) / b
        return max(0.0, fraction * kelly)
