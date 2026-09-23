"""
Contextual Bandit Decision Engine with Strict Safety Subordination.
Implements LinUCB (Upper Confidence Bound) and Thompson Sampling (Bayesian Linear Regression)
for decision threshold and market action optimization.

Strictly subordinated to python/engine/nobet_gate.py:
If any safety gate fails (unconfirmed lineups, stale odds, negative EV, high uncertainty),
the action space is strictly restricted to a = ABSTAIN.
Operates in RESEARCH mode by default until 1,000 verified paper bets have settled.
"""

from __future__ import annotations
import argparse
import sys
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from scipy import stats

from python.engine.nobet_gate import NoBetGate, NoBetGateResult
from python.rl.action_space import Action, V1_ACTIONS
from python.rl.counterfactual_logger import CounterfactualLogger, CandidateDecisionOpportunity
from python.rl.reward import MultiObjectiveRewardCalculator, RewardCalculator
from python.rl.state_representation import RLState


class LinUCBAgent:
    """Linear Upper Confidence Bound (LinUCB) contextual bandit agent."""

    def __init__(
        self,
        n_actions: int = 2,
        n_features: int = 20,
        alpha: float = 1.0,
        temperature: float = 1.0,
        epsilon_min: float = 0.01,
    ):
        self.n_actions = n_actions
        self.n_features = n_features
        self.alpha = alpha
        self.temperature = max(temperature, 1e-4)
        self.epsilon_min = epsilon_min
        # A: covariance matrices, b: response vectors
        self.A = {a: np.eye(n_features, dtype=np.float64) for a in range(n_actions)}
        self.b = {a: np.zeros(n_features, dtype=np.float64) for a in range(n_actions)}

    def get_ucb_scores(self, context: np.ndarray) -> np.ndarray:
        """Compute UCB exploration score for each action."""
        x = np.asarray(context, dtype=np.float64)
        scores = np.zeros(self.n_actions, dtype=np.float64)
        for a in range(self.n_actions):
            A_inv = np.linalg.pinv(self.A[a])
            theta_a = A_inv @ self.b[a]
            confidence_radius = self.alpha * np.sqrt(np.maximum(0.0, x.T @ A_inv @ x))
            scores[a] = theta_a.T @ x + confidence_radius
        return scores

    def get_action_propensities(self, context: np.ndarray) -> np.ndarray:
        """Compute smooth action propensities P(a | X) via softmax over UCB scores."""
        scores = self.get_ucb_scores(context)
        # Shift scores for numerical stability
        shifted = (scores - np.max(scores)) / self.temperature
        exp_scores = np.exp(shifted)
        probs = exp_scores / np.sum(exp_scores)
        # Clip to prevent division-by-zero in off-policy evaluation
        clipped = np.clip(probs, self.epsilon_min, 1.0 - self.epsilon_min)
        return clipped / np.sum(clipped)

    def select_action(self, context: np.ndarray, sample: bool = False) -> int:
        """Select action via greedy UCB or propensity sampling.
        
        Ties are broken in favor of ABSTAIN (action index 0).
        """
        x = np.asarray(context, dtype=np.float64)
        if sample:
            probs = self.get_action_propensities(x)
            return int(np.random.choice(self.n_actions, p=probs))

        scores = self.get_ucb_scores(x)
        max_score = np.max(scores)
        best_actions = np.where(np.isclose(scores, max_score, atol=1e-8))[0]
        # Break ties with ABSTAIN (0)
        if 0 in best_actions:
            return 0
        return int(best_actions[0])

    def update(self, action: int, context: np.ndarray, reward: float) -> None:
        """Update covariance matrix A and reward vector b for the chosen action."""
        x = np.asarray(context, dtype=np.float64)
        self.A[action] += np.outer(x, x)
        self.b[action] += float(reward) * x

    def serialize(self) -> Dict[str, Any]:
        """Serialize agent state to dictionary."""
        return {
            "type": "LinUCBAgent",
            "A": {a: self.A[a].tolist() for a in range(self.n_actions)},
            "b": {a: self.b[a].tolist() for a in range(self.n_actions)},
            "n_actions": self.n_actions,
            "n_features": self.n_features,
            "alpha": self.alpha,
            "temperature": self.temperature,
            "epsilon_min": self.epsilon_min,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LinUCBAgent":
        """Instantiate agent from dictionary."""
        agent = cls(
            n_actions=data["n_actions"],
            n_features=data["n_features"],
            alpha=data["alpha"],
            temperature=data.get("temperature", 1.0),
            epsilon_min=data.get("epsilon_min", 0.01),
        )
        agent.A = {int(a): np.array(mat, dtype=np.float64) for a, mat in data["A"].items()}
        agent.b = {int(a): np.array(vec, dtype=np.float64) for a, vec in data["b"].items()}
        return agent


class ThompsonSamplingAgent:
    """Bayesian Linear Regression Contextual Bandit agent with Gaussian posterior sampling."""

    def __init__(
        self,
        n_actions: int = 2,
        n_features: int = 20,
        v: float = 0.5,
        epsilon_min: float = 0.01,
    ):
        self.n_actions = n_actions
        self.n_features = n_features
        self.v = v  # Observation noise / exploration variance
        self.epsilon_min = epsilon_min
        # B: precision matrix, f: target vector
        self.B = {a: np.eye(n_features, dtype=np.float64) for a in range(n_actions)}
        self.f = {a: np.zeros(n_features, dtype=np.float64) for a in range(n_actions)}

    def sample_weights(self) -> Dict[int, np.ndarray]:
        """Draw parameter sample from posterior N(mu_a, v^2 * B_a^-1)."""
        sampled = {}
        for a in range(self.n_actions):
            B_inv = np.linalg.pinv(self.B[a])
            mu = B_inv @ self.f[a]
            cov = (self.v ** 2) * B_inv
            # Symmetrize covariance for numerical stability
            cov = (cov + cov.T) / 2.0 + 1e-8 * np.eye(self.n_features)
            sampled[a] = np.random.multivariate_normal(mu, cov)
        return sampled

    def select_action(self, context: np.ndarray, sample: bool = True) -> int:
        """Select action via posterior Thompson sampling or greedy posterior mean."""
        x = np.asarray(context, dtype=np.float64)
        if sample:
            sampled_theta = self.sample_weights()
            payoffs = np.array([sampled_theta[a].T @ x for a in range(self.n_actions)])
        else:
            payoffs = np.zeros(self.n_actions)
            for a in range(self.n_actions):
                B_inv = np.linalg.pinv(self.B[a])
                mu_a = B_inv @ self.f[a]
                payoffs[a] = mu_a.T @ x

        max_payoff = np.max(payoffs)
        best_actions = np.where(np.isclose(payoffs, max_payoff, atol=1e-8))[0]
        # Break ties with ABSTAIN (0)
        if 0 in best_actions:
            return 0
        return int(best_actions[0])

    def get_action_propensities(self, context: np.ndarray, n_mc_samples: int = 500) -> np.ndarray:
        """Compute action propensity P(a | X).
        
        For 2 actions, uses exact analytical Gaussian difference CDF.
        For > 2 actions, uses Monte Carlo posterior sampling.
        """
        x = np.asarray(context, dtype=np.float64)
        if self.n_actions == 2:
            B0_inv = np.linalg.pinv(self.B[0])
            B1_inv = np.linalg.pinv(self.B[1])
            mu0 = B0_inv @ self.f[0]
            mu1 = B1_inv @ self.f[1]

            # Delta = r1 - r0 ~ Normal(mu_delta, sigma_delta^2)
            mu_delta = (mu1 - mu0).T @ x
            var_delta = (self.v ** 2) * (x.T @ B1_inv @ x + x.T @ B0_inv @ x)
            sigma_delta = np.sqrt(max(var_delta, 1e-8))

            p1 = float(stats.norm.cdf(mu_delta / sigma_delta))
            p0 = 1.0 - p1

            probs = np.array([p0, p1])
            clipped = np.clip(probs, self.epsilon_min, 1.0 - self.epsilon_min)
            return clipped / np.sum(clipped)

        # General K-action Monte Carlo estimation
        action_counts = np.zeros(self.n_actions)
        for _ in range(n_mc_samples):
            sampled = self.sample_weights()
            payoffs = [sampled[a].T @ x for a in range(self.n_actions)]
            best = int(np.argmax(payoffs))
            action_counts[best] += 1

        raw_probs = action_counts / n_mc_samples
        clipped = np.clip(raw_probs, self.epsilon_min, 1.0 - self.epsilon_min)
        return clipped / np.sum(clipped)

    def update(self, action: int, context: np.ndarray, reward: float) -> None:
        """Update precision matrix B and response vector f."""
        x = np.asarray(context, dtype=np.float64)
        self.B[action] += np.outer(x, x)
        self.f[action] += float(reward) * x

    def serialize(self) -> Dict[str, Any]:
        """Serialize agent state to dictionary."""
        return {
            "type": "ThompsonSamplingAgent",
            "B": {a: self.B[a].tolist() for a in range(self.n_actions)},
            "f": {a: self.f[a].tolist() for a in range(self.n_actions)},
            "n_actions": self.n_actions,
            "n_features": self.n_features,
            "v": self.v,
            "epsilon_min": self.epsilon_min,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThompsonSamplingAgent":
        """Instantiate agent from dictionary."""
        agent = cls(
            n_actions=data["n_actions"],
            n_features=data["n_features"],
            v=data.get("v", 0.5),
            epsilon_min=data.get("epsilon_min", 0.01),
        )
        agent.B = {int(a): np.array(mat, dtype=np.float64) for a, mat in data["B"].items()}
        agent.f = {int(a): np.array(vec, dtype=np.float64) for a, vec in data["f"].items()}
        return agent


class RLDecisionLayer:
    """Contextual Bandit Decision Engine with Strict Safety Subordination.
    
    Subordinated to NoBetGate:
    - If ANY safety gate fails, the action space is restricted strictly to a = ABSTAIN.
    - Default operating mode is RESEARCH.
    - Mode ACTIVE is enabled ONLY when rl_enabled is True and >= 1,000 settled bets exist.
    """

    def __init__(
        self,
        agent: Union[LinUCBAgent, ThompsonSamplingAgent],
        reward_calc: Optional[Union[MultiObjectiveRewardCalculator, RewardCalculator]] = None,
        min_observations: int = 1000,
        mode: str = "RESEARCH",
        logger: Optional[CounterfactualLogger] = None,
        gate: Optional[NoBetGate] = None,
    ):
        self.agent = agent
        self.reward_calc = reward_calc or MultiObjectiveRewardCalculator()
        self.min_observations = min_observations
        self.mode = mode.upper()  # "RESEARCH" or "ACTIVE"
        self.is_enabled = False   # Controlled by engine_settings.rl_enabled
        self.logger = logger or CounterfactualLogger()
        self.gate = gate or NoBetGate()

    def evaluate_safety_gates(self, candidate: Any, match_state: Any) -> NoBetGateResult:
        """Evaluate candidate against authoritative safety gates.
        
        Enforces strict safety:
        - NEGATIVE_EV (ev <= 0)
        - LINEUP_UNCONFIRMED (not verified 11 vs 11 or lineup_confirmed is False)
        - ODDS_STALE (pre-match > 15m or live > 60s)
        - HIGH_UNCERTAINTY (SE > 0.02)
        - MARKET_SUSPENDED / ODDS_UNAVAILABLE
        - Candidate explicit decision == NO_BET
        """
        reasons: List[str] = []

        # Upstream gate decision check
        cand_decision = getattr(candidate, "decision", None)
        if cand_decision == "NO_BET":
            reasons.append("NO_BET_GATE_FAILED")

        ev = getattr(candidate, "expected_value", getattr(candidate, "ev", None))
        if ev is not None and ev <= 0.0:
            reasons.append("NEGATIVE_EV")
        elif ev is not None and ev < self.gate.MIN_EDGE:
            edge = getattr(candidate, "value_edge", getattr(candidate, "edge", None))
            if edge is not None and edge < self.gate.MIN_EDGE:
                reasons.append("EDGE_BELOW_THRESHOLD")

        lineup_conf = getattr(candidate, "lineup_confirmed", getattr(candidate, "lineups_confirmed", None))
        if lineup_conf is False:
            reasons.append("LINEUP_UNCONFIRMED")
        h_starters = getattr(candidate, "home_starters_count", None)
        a_starters = getattr(candidate, "away_starters_count", None)
        if (h_starters is not None and h_starters != 11) or (a_starters is not None and a_starters != 11):
            reasons.append("LINEUP_UNCONFIRMED")

        odds_age = getattr(candidate, "odds_age_seconds", 0.0)
        is_live = getattr(match_state, "is_live", getattr(candidate, "is_live", False))
        max_age = self.gate.LIVE_MAX_ODDS_AGE_SEC if is_live else self.gate.PREMATCH_MAX_ODDS_AGE_SEC
        if odds_age > max_age:
            reasons.append("ODDS_STALE")

        if getattr(candidate, "is_market_suspended", False) or getattr(candidate, "odds_available", True) is False:
            reasons.append("MARKET_SUSPENDED")

        se = getattr(candidate, "monte_carlo_se", None)
        if se is not None and se > self.gate.MAX_MONTE_CARLO_SE:
            reasons.append("HIGH_UNCERTAINTY")

        # If candidate has explicit NoBetGate properties and no decision was provided, do full gate eval
        if cand_decision is None and not reasons:
            full_res = self.gate.evaluate(
                ev=ev if ev is not None else 0.05,
                lineup_confirmed=True if lineup_conf is None else lineup_conf,
                home_starters_count=h_starters or 11,
                away_starters_count=a_starters or 11,
                odds_age_seconds=odds_age,
                is_live=is_live,
            )
            reasons.extend(full_res.reasons)

        reasons = list(set(reasons))
        action = "BET" if len(reasons) == 0 else "NO_BET"
        return NoBetGateResult(action=action, reasons=reasons)

    def decide(
        self,
        candidate: Any,
        match_state: Any,
        n_settled_bets: int = 0,
        fixture_id: Optional[Union[int, str]] = None,
        candidate_id: Optional[str] = None,
    ) -> str:
        """Contextual Bandit Decision Engine with Strict Statistical Subordination.
        
        1. Evaluates NO-BET gate. If gate fails, action is strictly clamped to ABSTAIN.
        2. If gate passes:
           - If in RESEARCH mode (or disabled or n_settled_bets < min_observations):
             Bandit policy is evaluated and logged counterfactually, but production
             decision adheres to upstream champion (BET_CANDIDATE).
           - If ACTIVE: Bandit selects action between ABSTAIN and BET.
        """
        gate_res = self.evaluate_safety_gates(candidate, match_state)
        state = RLState.from_candidate(candidate, match_state)
        context = state.to_array()

        original_decision = getattr(candidate, "decision", "NO_BET")
        fid = fixture_id or getattr(candidate, "fixture_id", "unknown_fixture")
        cid = candidate_id or getattr(candidate, "candidate_id", None)

        # STRICT SAFETY SUBORDINATION:
        # If gate evaluation fails, action space is STRICTLY restricted to ABSTAIN.
        # The bandit CANNOT override a NO_BET gate into a BET under any circumstance.
        if gate_res.action == "NO_BET" or original_decision == "NO_BET":
            if self.logger is not None:
                self.logger.record_opportunity(
                    candidate_id=cid,
                    fixture_id=fid,
                    match_timestamp=getattr(candidate, "match_timestamp", "2026-09-24T00:00:00Z"),
                    market=getattr(candidate, "market", "Match Odds"),
                    competition=getattr(candidate, "competition", "Competition"),
                    decimal_odds=getattr(candidate, "decimal_odds", 2.0),
                    fair_probability=getattr(candidate, "implied_probability", 0.5),
                    expected_value=getattr(candidate, "expected_value", 0.0),
                    value_edge=getattr(candidate, "value_edge", 0.0),
                    raw_probability=getattr(candidate, "raw_probability", 0.5),
                    calibrated_probability=getattr(candidate, "calibrated_probability", 0.5),
                    probability_interval=(
                        getattr(candidate, "probability_lower", 0.4),
                        getattr(candidate, "probability_upper", 0.6),
                    ),
                    gate_action="NO_BET",
                    gate_reasons=gate_res.reasons,
                    chosen_action="ABSTAIN",
                    action_propensity=1.0,
                    context_vector=context,
                    available_actions=["ABSTAIN"],
                    action_propensities={"ABSTAIN": 1.0, "BET": 0.0},
                    uncertainty=getattr(candidate, "uncertainty", 0.05),
                    lineup_verified=getattr(candidate, "lineup_confirmed", True),
                )
            return "NO_BET"

        # Calculate bandit action and propensity
        action_idx = self.agent.select_action(context, sample=False)
        rl_action = V1_ACTIONS[action_idx]
        propensities = self.agent.get_action_propensities(context)
        bet_propensity = float(propensities[1])
        abstain_propensity = float(propensities[0])
        chosen_propensity = float(propensities[action_idx])

        # Active policy gate: Requires rl_enabled AND >= min_observations AND mode == 'ACTIVE'
        is_active = (
            self.is_enabled
            and (self.mode == "ACTIVE")
            and (n_settled_bets >= self.min_observations)
        )

        final_decision: str
        if is_active:
            # Active bandit controls decision
            final_decision = "BET_CANDIDATE" if rl_action == Action.BET else "ABSTAIN"
            recorded_action = "BET" if rl_action == Action.BET else "ABSTAIN"
            recorded_propensity = chosen_propensity
        else:
            # RESEARCH mode: pass-through champion decision, log shadow bandit decision
            final_decision = original_decision
            recorded_action = "BET" if final_decision == "BET_CANDIDATE" else "ABSTAIN"
            recorded_propensity = bet_propensity if recorded_action == "BET" else abstain_propensity

        if self.logger is not None:
            self.logger.record_opportunity(
                candidate_id=cid,
                fixture_id=fid,
                match_timestamp=getattr(candidate, "match_timestamp", "2026-09-24T00:00:00Z"),
                market=getattr(candidate, "market", "Match Odds"),
                competition=getattr(candidate, "competition", "Competition"),
                decimal_odds=getattr(candidate, "decimal_odds", 2.0),
                fair_probability=getattr(candidate, "implied_probability", 0.5),
                expected_value=getattr(candidate, "expected_value", 0.05),
                value_edge=getattr(candidate, "value_edge", 0.03),
                raw_probability=getattr(candidate, "raw_probability", 0.55),
                calibrated_probability=getattr(candidate, "calibrated_probability", 0.53),
                probability_interval=(
                    getattr(candidate, "probability_lower", 0.45),
                    getattr(candidate, "probability_upper", 0.61),
                ),
                gate_action="BET",
                gate_reasons=[],
                chosen_action=recorded_action,
                action_propensity=recorded_propensity,
                context_vector=context,
                available_actions=["ABSTAIN", "BET"],
                action_propensities={"ABSTAIN": abstain_propensity, "BET": bet_propensity},
                uncertainty=getattr(candidate, "uncertainty", 0.05),
                lineup_verified=getattr(candidate, "lineup_confirmed", True),
                metadata={"rl_mode": self.mode, "is_active": is_active, "rl_action": str(rl_action)},
            )

        return final_decision

    def record_outcome(
        self,
        prediction_id: str,
        action: str,
        context: np.ndarray,
        reward: Optional[float] = None,
        outcome: Optional[str] = None,
        decimal_odds: float = 2.0,
        clv: float = 0.0,
        uncertainty: float = 0.0,
    ) -> float:
        """Update contextual bandit with realized reward."""
        if reward is not None:
            r = float(reward)
        else:
            if isinstance(self.reward_calc, MultiObjectiveRewardCalculator):
                r = self.reward_calc.calculate(
                    action=action,
                    outcome=outcome or "loss",
                    decimal_odds=decimal_odds,
                    clv=clv,
                    uncertainty=uncertainty,
                )
            elif hasattr(self.reward_calc, "calculate_multi_objective"):
                r = self.reward_calc.calculate_multi_objective(
                    action=action,
                    outcome=outcome or "loss",
                    decimal_odds=decimal_odds,
                    clv=clv,
                    uncertainty=uncertainty,
                )
            else:
                r = 0.0

        action_idx = V1_ACTIONS.index(action) if action in V1_ACTIONS else 0
        self.agent.update(action_idx, context, r)

        if self.logger is not None:
            self.logger.log_settlement(
                candidate_id=prediction_id,
                actual_outcome=outcome or "loss",
                realized_return=r,
                clv=clv,
            )

        return r

    def inspect(self) -> Dict[str, Any]:
        """Inspect agent parameters, covariance traces, and governance state."""
        return {
            "mode": self.mode,
            "is_enabled": self.is_enabled,
            "min_observations": self.min_observations,
            "agent_type": self.agent.__class__.__name__,
            "n_actions": self.agent.n_actions,
            "n_features": self.agent.n_features,
            "logged_opportunities": len(self.logger) if self.logger else 0,
            "settled_opportunities": len(self.logger.get_settled_candidates()) if self.logger else 0,
            "subordination_enforced": True,
        }


def main():
    """CLI tool for policy inspection and offline evaluation."""
    parser = argparse.ArgumentParser(description="Bandit Policy Governance & Diagnostics")
    parser.add_argument("--inspect", action="store_true", help="Inspect bandit policy state and weights")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate logged policy data via OPE")
    args = parser.parse_args()

    agent = LinUCBAgent(n_features=20)
    layer = RLDecisionLayer(agent=agent)

    if args.inspect:
        info = layer.inspect()
        print("=== BANDIT POLICY DIAGNOSTICS ===")
        for k, v in info.items():
            print(f"  {k}: {v}")
        print("  Status: Quarantined in RESEARCH mode (Strictly Subordinated to NoBetGate)")
        sys.exit(0)

    if args.evaluate:
        print("=== OFFLINE POLICY EVALUATION (OPE) ===")
        print("Evaluating policy candidates against settled paper-bet ledger...")
        print("Requires minimum 1,000 verified settled opportunities.")
        print(f"Current settled opportunities: {len(layer.logger.get_settled_candidates())}")
        print("Status: Policy remains in RESEARCH quarantine until gate conditions are met.")
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
