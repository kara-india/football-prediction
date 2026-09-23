"""
Edge & Expected Value Calculation Engine
Authoritative valuation layer for deriving Expected Value (EV), fair market edge,
and informational Fractional Kelly stake allocations.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
import numpy as np

from python.odds.devig import DeVIgEngine


@dataclass(frozen=True)
class CandidateSelection:
    """Structured bet candidate selection with mathematical edge attributes."""
    match_id: str
    market: str
    selection: str
    odds_1xbet: float
    p_calibrated: float
    p_fair_devigged: float
    expected_value: float              # EV = p_calibrated * odds_1xbet - 1.0
    value_edge: float                  # edge = p_calibrated - p_fair_devigged
    fractional_kelly: float            # f* = ((p * o - 1) / (o - 1)) * 0.25 bounded in [0.0, 0.05]
    flat_stake: float = 1.0            # Strict flat 1.0 unit stake for paper evaluation
    line: Optional[float] = None
    raw_model_prob: Optional[float] = None
    prob_lower_bound: Optional[float] = None
    prob_upper_bound: Optional[float] = None
    simulation_std_error: Optional[float] = None
    recommended_action: str = "NO_BET" # "BET" or "NO_BET"
    no_bet_reasons: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def ev(self) -> float:
        """Alias for expected_value."""
        return self.expected_value

    @property
    def edge(self) -> float:
        """Alias for value_edge."""
        return self.value_edge

    def to_dict(self) -> Dict[str, Any]:
        """Convert CandidateSelection to dictionary."""
        return {
            "match_id": self.match_id,
            "market": self.market,
            "selection": self.selection,
            "odds_1xbet": self.odds_1xbet,
            "p_calibrated": self.p_calibrated,
            "p_fair_devigged": self.p_fair_devigged,
            "expected_value": self.expected_value,
            "value_edge": self.value_edge,
            "fractional_kelly": self.fractional_kelly,
            "flat_stake": self.flat_stake,
            "line": self.line,
            "raw_model_prob": self.raw_model_prob,
            "prob_lower_bound": self.prob_lower_bound,
            "prob_upper_bound": self.prob_upper_bound,
            "simulation_std_error": self.simulation_std_error,
            "recommended_action": self.recommended_action,
            "no_bet_reasons": self.no_bet_reasons,
            "created_at": self.created_at.isoformat(),
        }


class EdgeCalculator:
    """Quantitative Edge Calculator for EV, de-vigged value edge, and Kelly allocation."""

    DEFAULT_KELLY_FRACTION: float = 0.25
    MIN_KELLY_BOUND: float = 0.0
    MAX_KELLY_BOUND: float = 0.05
    FLAT_PAPER_STAKE: float = 1.0

    @staticmethod
    def compute_ev(p_calibrated: float, odds_1xbet: float) -> float:
        """Compute Expected Value: EV = p_calibrated * odds_1xbet - 1.0.

        Args:
            p_calibrated: Post-calibration probability in [0.0, 1.0].
            odds_1xbet: Execution decimal odds from 1xBet (> 1.0).

        Returns:
            Expected value per 1.0 unit stake (e.g. 0.08 for +8% EV).
        """
        if odds_1xbet <= 1.0:
            return -1.0
        return float(p_calibrated * odds_1xbet - 1.0)

    @staticmethod
    def compute_edge(p_calibrated: float, p_fair_devigged: float) -> float:
        """Compute Value Edge: edge = p_calibrated - p_fair_devigged.

        Args:
            p_calibrated: Calibrated model probability.
            p_fair_devigged: Margin-removed true market probability.

        Returns:
            Absolute probability difference (e.g. 0.04 for +4% probability advantage).
        """
        return float(p_calibrated - p_fair_devigged)

    @classmethod
    def compute_fractional_kelly(
        cls,
        p_calibrated: float,
        odds_1xbet: float,
        fraction: float = DEFAULT_KELLY_FRACTION,
        min_bound: float = MIN_KELLY_BOUND,
        max_bound: float = MAX_KELLY_BOUND,
    ) -> float:
        """Compute informational Fractional Kelly stake.

        Formula: f* = ((p * o - 1) / (o - 1)) * 0.25, strictly bounded in [0.0, 0.05].

        Args:
            p_calibrated: Calibrated probability of success.
            odds_1xbet: Decimal odds (> 1.0).
            fraction: Kelly fractional multiplier (default 0.25 / quarter-Kelly).
            min_bound: Minimum allocation bound (0.0).
            max_bound: Maximum allocation bound (0.05 / 5% bankroll cap).

        Returns:
            Fractional Kelly stake bounded in [min_bound, max_bound].
        """
        b = odds_1xbet - 1.0
        if b <= 0.0:
            return 0.0

        p = p_calibrated
        q = 1.0 - p

        # Kelly criterion: (b*p - q) / b == (p*o - 1) / (o - 1)
        raw_kelly = (b * p - q) / b
        if raw_kelly <= 0.0:
            return 0.0

        fractional = raw_kelly * fraction
        return float(np.clip(fractional, min_bound, max_bound))

    @staticmethod
    def devig_market(all_odds: List[float], method: str = "multiplicative") -> List[float]:
        """De-vig a full market's decimal odds to derive fair probabilities."""
        if method == "shin" and len(all_odds) == 3:
            fair_probs, _ = DeVIgEngine.shin_devig(all_odds)
            return fair_probs
        return DeVIgEngine.multiplicative_devig(all_odds)

    @classmethod
    def evaluate_selection(
        cls,
        match_id: str,
        market: str,
        selection: str,
        odds_1xbet: float,
        p_calibrated: float,
        p_fair_devigged: Optional[float] = None,
        market_all_odds: Optional[List[float]] = None,
        selection_index: int = 0,
        line: Optional[float] = None,
        raw_model_prob: Optional[float] = None,
        prob_lower_bound: Optional[float] = None,
        prob_upper_bound: Optional[float] = None,
        simulation_std_error: Optional[float] = None,
        recommended_action: str = "NO_BET",
        no_bet_reasons: Optional[List[str]] = None,
    ) -> CandidateSelection:
        """Construct a fully evaluated CandidateSelection.

        Args:
            match_id: Unique fixture identifier.
            market: Canonical market name (e.g. 'MATCH_1X2', 'TOTAL_GOALS_2_5').
            selection: Target outcome (e.g. '1', 'OVER').
            odds_1xbet: Decimal odds price from 1xBet.
            p_calibrated: Calibrated model win probability.
            p_fair_devigged: De-vigged fair market probability. If omitted, derived from market_all_odds.
            market_all_odds: Optional complete set of bookmaker odds for devigging.
            selection_index: Index of current selection within market_all_odds.
            line: Market line (e.g. 2.5).
            raw_model_prob: Pre-calibration raw model probability.
            prob_lower_bound: Credible interval lower bound.
            prob_upper_bound: Credible interval upper bound.
            simulation_std_error: Monte Carlo standard error.
            recommended_action: Action string ("BET" or "NO_BET").
            no_bet_reasons: Reasons list if NO_BET.

        Returns:
            Immutable CandidateSelection instance.
        """
        if p_fair_devigged is None:
            if market_all_odds and len(market_all_odds) > 1:
                fair_probs = cls.devig_market(market_all_odds)
                p_fair = fair_probs[selection_index]
            else:
                p_fair = 1.0 / odds_1xbet if odds_1xbet > 0 else 0.0
        else:
            p_fair = p_fair_devigged

        ev = cls.compute_ev(p_calibrated, odds_1xbet)
        edge = cls.compute_edge(p_calibrated, p_fair)
        kelly = cls.compute_fractional_kelly(p_calibrated, odds_1xbet)

        return CandidateSelection(
            match_id=match_id,
            market=market,
            selection=selection,
            odds_1xbet=odds_1xbet,
            p_calibrated=p_calibrated,
            p_fair_devigged=p_fair,
            expected_value=ev,
            value_edge=edge,
            fractional_kelly=kelly,
            flat_stake=cls.FLAT_PAPER_STAKE,
            line=line,
            raw_model_prob=raw_model_prob,
            prob_lower_bound=prob_lower_bound,
            prob_upper_bound=prob_upper_bound,
            simulation_std_error=simulation_std_error,
            recommended_action=recommended_action,
            no_bet_reasons=no_bet_reasons or [],
        )
