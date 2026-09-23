"""
Reward Calculation Engine for Reinforcement Learning and Contextual Bandits.
Supports multi-objective reward optimization combining realized P&L, Closing Line Value (CLV),
and epistemic uncertainty penalties.
"""

from typing import Optional


class MultiObjectiveRewardCalculator:
    """Authoritative multi-objective reward calculator for Contextual Bandits.
    
    Reward = PnL_flat_stake + lambda_clv * CLV - gamma_uncertainty * uncertainty
    """

    def __init__(
        self,
        lambda_clv: float = 0.5,
        gamma_uncertainty: float = 0.2,
        stake: float = 1.0,
    ):
        self.lambda_clv = lambda_clv
        self.gamma_uncertainty = gamma_uncertainty
        self.stake = stake

    def calculate(
        self,
        action: str,
        outcome: str,  # 'win', 'loss', 'void'
        decimal_odds: float,
        clv: float = 0.0,
        uncertainty: float = 0.0,
        stake: Optional[float] = None,
    ) -> float:
        """Calculate multi-objective reward.
        
        Args:
            action: 'ABSTAIN' or 'BET'
            outcome: 'win', 'loss', or 'void'
            decimal_odds: 1xBet decimal price at time of decision
            clv: Closing Line Value ((taken_odds / closing_odds) - 1.0)
            uncertainty: Model standard error or credible interval width
            stake: Optional custom stake size (defaults to self.stake)
        """
        if action == "ABSTAIN":
            return 0.0

        if action != "BET":
            return 0.0

        wager_stake = stake if stake is not None else self.stake
        outcome_norm = outcome.lower().strip()

        # Flat-stake P&L
        if outcome_norm in ("win", "won", "1"):
            pnl = (decimal_odds - 1.0) * wager_stake
        elif outcome_norm in ("loss", "lost", "0"):
            pnl = -wager_stake
        else:  # void / push
            pnl = 0.0

        # Multi-objective composite reward
        reward = pnl + (self.lambda_clv * clv) - (self.gamma_uncertainty * uncertainty)
        return float(reward)


class RewardCalculator:
    """V1 Backwards-compatible and configurable reward calculator with risk penalties."""
    
    BASE_OVERCONFIDENCE_PENALTY = -0.5  # calibrated_prob >> actual outcome
    BASE_STALE_DATA_PENALTY = -0.2     # acted on stale data
    BASE_DRAWDOWN_PENALTY = -0.3       # contributed to significant drawdown
    BASE_POOR_CALIBRATION_PENALTY = -0.1  # model poorly calibrated

    def __init__(
        self,
        lambda_clv: float = 0.5,
        gamma_uncertainty: float = 0.2,
    ):
        self.multi_objective = MultiObjectiveRewardCalculator(
            lambda_clv=lambda_clv,
            gamma_uncertainty=gamma_uncertainty,
        )

    def calculate_reward(
        self,
        action: str,
        outcome: str,  # 'win', 'loss', 'void'
        decimal_odds: float,
        stake_units: float,
        calibrated_prob: float,
        data_freshness_seconds: int,
        current_drawdown: float,
        brier_contribution: float,
    ) -> float:
        """Original Phase 6 reward formula with risk penalty heuristics."""
        if action == "ABSTAIN":
            return 0.0

        if action == "BET":
            reward = 0.0
            if outcome == "win":
                reward = (decimal_odds - 1.0) * stake_units
            elif outcome == "loss":
                reward = -stake_units

            # Penalties
            actual_outcome = 1.0 if outcome == "win" else 0.0 if outcome == "loss" else 0.5
            reward += self.apply_overconfidence_penalty(calibrated_prob, actual_outcome)
            reward += self.apply_drawdown_penalty(current_drawdown)

            if data_freshness_seconds > 300:  # 5 minutes
                reward += self.BASE_STALE_DATA_PENALTY

            return reward

        return 0.0

    def calculate_multi_objective(
        self,
        action: str,
        outcome: str,
        decimal_odds: float,
        clv: float = 0.0,
        uncertainty: float = 0.0,
        stake: float = 1.0,
    ) -> float:
        """Delegates to MultiObjectiveRewardCalculator."""
        return self.multi_objective.calculate(
            action=action,
            outcome=outcome,
            decimal_odds=decimal_odds,
            clv=clv,
            uncertainty=uncertainty,
            stake=stake,
        )

    def apply_overconfidence_penalty(
        self, calibrated_prob: float, actual_outcome: float
    ) -> float:
        if calibrated_prob > 0.8 and actual_outcome == 0.0:
            return self.BASE_OVERCONFIDENCE_PENALTY * (calibrated_prob - 0.8) * 5.0
        return 0.0

    def apply_drawdown_penalty(
        self, current_drawdown: float, threshold: float = 0.10
    ) -> float:
        if current_drawdown > threshold:
            return self.BASE_DRAWDOWN_PENALTY
        return 0.0
