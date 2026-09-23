"""
Mathematical Odds De-Vigging & Fair Probability Engine
Provides exact margin calculation, proportional (multiplicative) normalization,
and Shin's method for adjusting for the favorite-longshot bias in multi-way markets.
"""
import math
from typing import List, Tuple, Dict, Optional


class DeVIgEngine:
    """Calculates bookmaker overround and strips margins to derive true probabilities."""

    @staticmethod
    def calculate_margin(decimal_odds: List[float]) -> float:
        """Calculate market overround / vig margin: M = sum(1 / o_i) - 1.0.

        Args:
            decimal_odds: List of decimal odds prices (e.g., [1.95, 3.40, 4.20]).

        Returns:
            Margin as a float (e.g., 0.045 for 4.5% margin).
        """
        if not decimal_odds or any(o <= 1.0 for o in decimal_odds):
            raise ValueError(f"Invalid decimal odds: {decimal_odds}")
        return sum(1.0 / o for o in decimal_odds) - 1.0

    @staticmethod
    def multiplicative_devig(decimal_odds: List[float]) -> List[float]:
        """Proportional (Multiplicative) margin removal.

        p_i = (1 / o_i) / sum(1 / o_j)

        Guarantees that fair probabilities sum to exactly 1.0.
        """
        if not decimal_odds or any(o <= 1.0 for o in decimal_odds):
            raise ValueError(f"Invalid decimal odds: {decimal_odds}")

        implied = [1.0 / o for o in decimal_odds]
        total_implied = sum(implied)
        return [p / total_implied for p in implied]

    @staticmethod
    def shin_devig(decimal_odds: List[float], max_iter: int = 100, tol: float = 1e-7) -> Tuple[List[float], float]:
        """Shin's method for margin removal in 3-way markets (MATCH_1X2).

        Accounts for the favorite-longshot bias by modeling a proportion `z` of
        better-informed bettors with private information.

        Solves for z such that sum(p_i) == 1.0 where:
            p_i = (sqrt(z^2 + 4 * (1 - z) * (pi_i^2 / sum_pi)) - z) / (2 * (1 - z))

        Returns:
            Tuple of (fair_probabilities: List[float], insider_parameter_z: float)
        """
        if len(decimal_odds) < 2:
            return DeVIgEngine.multiplicative_devig(decimal_odds), 0.0

        n = len(decimal_odds)
        implied = [1.0 / o for o in decimal_odds]
        sum_implied = sum(implied)

        # If zero or negative margin, return proportional
        if sum_implied <= 1.0:
            return DeVIgEngine.multiplicative_devig(decimal_odds), 0.0

        # Bisection search for insider parameter z in [0.0, 0.4]
        z_low = 0.0
        z_high = 0.4
        best_z = 0.0
        probs = []

        for _ in range(max_iter):
            z_mid = (z_low + z_high) / 2.0
            candidate_probs = []

            for p_raw in implied:
                # Shin quadratic formulation
                term1 = z_mid ** 2
                term2 = 4.0 * (1.0 - z_mid) * (p_raw ** 2) / sum_implied
                prob_i = (math.sqrt(term1 + term2) - z_mid) / (2.0 * (1.0 - z_mid))
                candidate_probs.append(prob_i)

            sum_p = sum(candidate_probs)
            if abs(sum_p - 1.0) < tol:
                best_z = z_mid
                probs = candidate_probs
                break

            if sum_p > 1.0:
                z_low = z_mid
            else:
                z_high = z_mid
            best_z = z_mid
            probs = candidate_probs

        # Final normalization to ensure sum == 1.00000000 exactly
        total = sum(probs)
        normalized_probs = [p / total for p in probs]
        return normalized_probs, round(best_z, 5)

    @classmethod
    def devig_market(cls, decimal_odds: List[float], method: str = "shin") -> List[float]:
        """Devig odds using specified method ("shin" for 3-way, "multiplicative" for 2-way)."""
        if method == "shin" and len(decimal_odds) >= 3:
            probs, _ = cls.shin_devig(decimal_odds)
            return probs
        return cls.multiplicative_devig(decimal_odds)
