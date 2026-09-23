"""
Authoritative 10-Point NO-BET Gate Engine
Strict risk filter enforcing algorithmic capital protection before any candidate
wager can be considered actionable.
"""
from typing import NamedTuple, List, Optional, Dict, Any, Union
from dataclasses import dataclass


class NoBetGateResult(NamedTuple):
    """Result of 10-point gate evaluation supporting tuple unpacking and named access."""
    action: str              # "BET" | "NO_BET"
    reasons: List[str]       # Empty list if action == "BET"


class NoBetGate:
    """Authoritative 10-Point NO-BET Gate."""

    # Threshold constants
    MIN_EDGE: float = 0.03                  # Minimum 3.0% expected value / edge
    PREMATCH_MAX_ODDS_AGE_SEC: float = 900  # 15 minutes
    LIVE_MAX_ODDS_AGE_SEC: float = 60       # 60 seconds
    MAX_MONTE_CARLO_SE: float = 0.02        # Standard error <= 0.02
    MAX_CREDIBLE_INTERVAL: float = 0.15     # 95% Credible interval width <= 0.15
    MIN_REGIME_SAMPLE: int = 100            # Calibration regime sample size
    MIN_HISTORICAL_SAMPLE: int = 200        # Minimum 200 matches for competition context

    def evaluate(
        self,
        ev: float,
        edge: Optional[float] = None,
        lineup_confirmed: bool = True,
        home_starters_count: Optional[int] = 11,
        away_starters_count: Optional[int] = 11,
        odds_age_seconds: float = 0.0,
        is_live: bool = False,
        is_market_suspended: bool = False,
        odds_available: bool = True,
        odds_1xbet: Optional[float] = None,
        monte_carlo_se: Optional[float] = None,
        credible_interval_width: Optional[float] = None,
        prob_lower: Optional[float] = None,
        prob_upper: Optional[float] = None,
        model_calibrated: bool = True,
        regime_sample_size: Optional[int] = None,
        source_conflict: bool = False,
        source_conflicts: Optional[List[str]] = None,
        player_starter_confirmed: Optional[bool] = None,
        player_minutes_uncertain: bool = False,
        historical_sample_size: int = 500,
    ) -> NoBetGateResult:
        """Evaluate match and market candidate against authoritative 10-point gate.

        1. NEGATIVE_EV: EV <= 0.0
        2. EDGE_BELOW_THRESHOLD: EV < 0.03 (min 3% edge)
        3. LINEUP_UNCONFIRMED: starting lineups not verified 11 vs 11
        4. ODDS_STALE: 1xBet price timestamp > 15m old pre-match or > 60s live
        5. MARKET_SUSPENDED: 1xBet price unavailable or locked
        6. HIGH_UNCERTAINTY: Monte Carlo SE > 0.02 or credible interval > 0.15
        7. MODEL_UNCALIBRATED: Insufficient sample size in regime or uncalibrated
        8. SOURCE_CONFLICT: Inconsistency between upstream providers
        9. PLAYER_MINUTES_UNCERTAIN: Player not confirmed starter
        10. INSUFFICIENT_SAMPLE: Historical sample < 200 matches

        Returns:
            (action: "BET" | "NO_BET", reasons: list[str])
        """
        reasons: List[str] = []

        # 1 & 2: Expected Value & Minimum Edge Threshold
        if ev <= 0.0:
            reasons.append("NEGATIVE_EV")
        elif ev < self.MIN_EDGE or (edge is not None and edge < self.MIN_EDGE):
            reasons.append("EDGE_BELOW_THRESHOLD")

        # 3: Lineup Confirmation (verified 11 vs 11)
        if not lineup_confirmed:
            reasons.append("LINEUP_UNCONFIRMED")
        elif (home_starters_count is not None and home_starters_count != 11) or (
            away_starters_count is not None and away_starters_count != 11
        ):
            reasons.append("LINEUP_UNCONFIRMED")

        # 4: Odds Staleness (> 15m pre-match, > 60s live)
        max_odds_age = self.LIVE_MAX_ODDS_AGE_SEC if is_live else self.PREMATCH_MAX_ODDS_AGE_SEC
        if odds_age_seconds > max_odds_age:
            reasons.append("ODDS_STALE")

        # 5: Market Suspension / Unavailability
        if is_market_suspended or not odds_available or (odds_1xbet is not None and odds_1xbet <= 1.0):
            reasons.append("MARKET_SUSPENDED")

        # 6: High Uncertainty (Monte Carlo SE > 0.02 or credible interval > 0.15)
        ci_width = credible_interval_width
        if ci_width is None and prob_lower is not None and prob_upper is not None:
            ci_width = prob_upper - prob_lower

        if (monte_carlo_se is not None and monte_carlo_se > self.MAX_MONTE_CARLO_SE) or (
            ci_width is not None and ci_width > self.MAX_CREDIBLE_INTERVAL
        ):
            reasons.append("HIGH_UNCERTAINTY")

        # 7: Model Uncalibrated / Insufficient Regime Sample
        if not model_calibrated:
            reasons.append("MODEL_UNCALIBRATED")
        elif regime_sample_size is not None and regime_sample_size < self.MIN_REGIME_SAMPLE:
            reasons.append("MODEL_UNCALIBRATED")

        # 8: Upstream Provider Source Conflict
        if source_conflict or (source_conflicts and len(source_conflicts) > 0):
            reasons.append("SOURCE_CONFLICT")

        # 9: Player Starter / Minutes Uncertainty
        if player_minutes_uncertain or player_starter_confirmed is False:
            reasons.append("PLAYER_MINUTES_UNCERTAIN")

        # 10: Insufficient Historical Sample (< 200 matches)
        if historical_sample_size < self.MIN_HISTORICAL_SAMPLE:
            reasons.append("INSUFFICIENT_SAMPLE")

        action = "BET" if len(reasons) == 0 else "NO_BET"
        return NoBetGateResult(action=action, reasons=reasons)
