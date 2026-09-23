"""
Offline Policy Evaluation (OPE) Engine for Contextual Bandits and Reinforcement Learning.
Provides statistically rigorous counterfactual policy evaluation using:
- Inverse Propensity Scoring (IPS) with weight clipping
- Direct Method (DM) via L2 Ridge regression
- Doubly Robust (DR) estimation
- Percentile bootstrap confidence intervals (B=1,000 resamples)
- Strict Policy Gatekeeper for promotion validation
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from python.rl.counterfactual_logger import CounterfactualLogger, CandidateDecisionOpportunity


@dataclass
class OPEResult:
    """Offline Policy Evaluation results for a target policy."""
    policy_name: str
    sample_size: int
    ips_value: float
    snips_value: float
    dm_value: float
    dr_value: float
    ci_lower: float
    ci_upper: float
    sharpe_dr: float
    sharpe_ci_lower: float
    sharpe_ci_upper: float
    weights_mean: float
    weights_max: float
    effective_sample_size: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PromotionEvaluationResult:
    """Result of policy gatekeeper promotion check."""
    eligible: bool
    policy_name: str
    sample_size: int
    dr_estimate: float
    ci_lower: float
    ci_upper: float
    ips_estimate: float
    dm_estimate: float
    sharpe_estimate: float
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OffPolicyEvaluator:
    """Offline Policy Evaluation (OPE) engine."""

    def __init__(
        self,
        max_weight: float = 20.0,
        ridge_alpha: float = 1.0,
        n_bootstraps: int = 1000,
        random_seed: Optional[int] = 42,
    ):
        self.max_weight = max_weight
        self.ridge_alpha = ridge_alpha
        self.n_bootstraps = n_bootstraps
        self.random_seed = random_seed
        if random_seed is not None:
            np.random.seed(random_seed)

    def extract_logged_data(
        self,
        logged_data: Union[pd.DataFrame, CounterfactualLogger, List[CandidateDecisionOpportunity], List[Dict[str, Any]], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]],
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Extract standard OPE arrays (contexts, actions, rewards, behavior_propensities).
        
        Returns:
            X: np.ndarray of shape (N, d)
            actions: np.ndarray of shape (N,) int
            rewards: np.ndarray of shape (N,) float
            behavior_p: np.ndarray of shape (N,) float
        """
        # If already a tuple of arrays
        if isinstance(logged_data, tuple) and len(logged_data) == 4:
            X, a, r, p = logged_data
            return np.asarray(X, dtype=float), np.asarray(a, dtype=int), np.asarray(r, dtype=float), np.asarray(p, dtype=float)

        if isinstance(logged_data, CounterfactualLogger):
            settled = logged_data.get_settled_candidates()
            if not settled:
                # Fall back to all if none settled (using realized_return or 0.0)
                settled = logged_data.get_all_candidates()
            return self._extract_from_opportunities(settled)

        if isinstance(logged_data, list):
            if len(logged_data) == 0:
                return np.empty((0, 0)), np.empty(0), np.empty(0), np.empty(0)
            if isinstance(logged_data[0], CandidateDecisionOpportunity):
                return self._extract_from_opportunities(logged_data)
            if isinstance(logged_data[0], dict):
                df = pd.DataFrame(logged_data)
                return self._extract_from_df(df)

        if isinstance(logged_data, pd.DataFrame):
            return self._extract_from_df(logged_data)

        raise ValueError(f"Unsupported logged_data format: {type(logged_data)}")

    def _extract_from_opportunities(
        self, opportunities: List[CandidateDecisionOpportunity]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        X_list, a_list, r_list, p_list = [], [], [], []
        for opp in opportunities:
            X_list.append(opp.context_vector)
            a_idx = opp.action_index if opp.action_index is not None else (1 if opp.chosen_action == "BET" else 0)
            a_list.append(a_idx)
            ret = opp.realized_return if opp.realized_return is not None else 0.0
            r_list.append(ret)
            p_val = opp.action_propensity if opp.action_propensity > 0 else 0.5
            p_list.append(p_val)

        return (
            np.asarray(X_list, dtype=float),
            np.asarray(a_list, dtype=int),
            np.asarray(r_list, dtype=float),
            np.asarray(p_list, dtype=float),
        )

    def _extract_from_df(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        feature_cols = [c for c in df.columns if c.startswith("feature_")]
        if feature_cols:
            X = df[feature_cols].values.astype(float)
        else:
            # Fall back to numerical columns excluding target/metadata
            exclude = {
                "candidate_id", "fixture_id", "match_timestamp", "market", "competition",
                "scoreline", "gate_action", "gate_reasons", "data_quality_tier",
                "chosen_action", "actual_outcome", "settled", "settled_at",
                "action_index", "action_propensity", "realized_return", "closing_odds",
                "clv", "counterfactual_return",
            }
            num_cols = [c for c in df.columns if c not in exclude and np.issubdtype(df[c].dtype, np.number)]
            X = df[num_cols].values.astype(float) if num_cols else np.zeros((len(df), 1))

        if "action_index" in df.columns:
            actions = df["action_index"].values.astype(int)
        elif "chosen_action" in df.columns:
            actions = (df["chosen_action"] == "BET").values.astype(int)
        else:
            actions = np.zeros(len(df), dtype=int)

        if "realized_return" in df.columns:
            rewards = df["realized_return"].fillna(0.0).values.astype(float)
        else:
            rewards = np.zeros(len(df), dtype=float)

        if "action_propensity" in df.columns:
            behavior_p = df["action_propensity"].fillna(0.5).values.astype(float)
        else:
            behavior_p = np.full(len(df), 0.5, dtype=float)

        return X, actions, rewards, behavior_p

    def get_target_policy_propensities(
        self,
        target_policy: Any,
        contexts: np.ndarray,
        actions: np.ndarray,
        n_actions: int = 2,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute target policy action propensities.
        
        Returns:
            target_p_chosen: np.ndarray of shape (N,) - probability of chosen action a_i
            all_target_probs: np.ndarray of shape (N, n_actions) - probabilities for all actions
        """
        N = len(contexts)
        all_probs = np.zeros((N, n_actions), dtype=float)

        # Case 1: target_policy is already an array of probabilities (N, n_actions) or (N,)
        if isinstance(target_policy, np.ndarray):
            if target_policy.ndim == 2:
                all_probs = target_policy
            elif target_policy.ndim == 1:
                all_probs[:, 1] = target_policy
                all_probs[:, 0] = 1.0 - target_policy
            p_chosen = all_probs[np.arange(N), actions]
            return p_chosen, all_probs

        # Case 2: target_policy has get_action_propensities
        if hasattr(target_policy, "get_action_propensities"):
            for i in range(N):
                probs = target_policy.get_action_propensities(contexts[i])
                all_probs[i, :len(probs)] = probs
            p_chosen = all_probs[np.arange(N), actions]
            return p_chosen, all_probs

        # Case 3: target_policy has agent with get_action_propensities (e.g. RLDecisionLayer)
        if hasattr(target_policy, "agent") and hasattr(target_policy.agent, "get_action_propensities"):
            for i in range(N):
                probs = target_policy.agent.get_action_propensities(contexts[i])
                all_probs[i, :len(probs)] = probs
            p_chosen = all_probs[np.arange(N), actions]
            return p_chosen, all_probs

        # Case 4: target_policy has select_action (deterministic policy)
        if hasattr(target_policy, "select_action"):
            for i in range(N):
                a_pred = target_policy.select_action(contexts[i])
                all_probs[i, a_pred] = 1.0
            p_chosen = all_probs[np.arange(N), actions]
            return p_chosen, all_probs

        # Case 5: target_policy is a callable function f(context) -> action or probs
        if callable(target_policy):
            for i in range(N):
                out = target_policy(contexts[i])
                if isinstance(out, (list, np.ndarray)):
                    all_probs[i, :len(out)] = out
                else:
                    all_probs[i, int(out)] = 1.0
            p_chosen = all_probs[np.arange(N), actions]
            return p_chosen, all_probs

        raise ValueError(f"Unsupported target_policy type: {type(target_policy)}")

    def fit_reward_model(
        self, contexts: np.ndarray, actions: np.ndarray, rewards: np.ndarray, n_actions: int = 2
    ) -> Dict[int, Any]:
        """Fit separate Ridge regression models Q_hat(x, a) -> r for each action a."""
        models: Dict[int, Any] = {}
        for a in range(n_actions):
            mask = (actions == a)
            if np.sum(mask) >= 2:
                model = Ridge(alpha=self.ridge_alpha, fit_intercept=True)
                model.fit(contexts[mask], rewards[mask])
                models[a] = model
            elif np.sum(mask) == 1:
                # Constant predictor
                val = float(rewards[mask][0])
                models[a] = lambda X, v=val: np.full(len(X), v)
            else:
                # No data for this action, predict zero
                models[a] = lambda X: np.zeros(len(X))
        return models

    def predict_q_values(
        self, q_models: Dict[int, Any], contexts: np.ndarray, n_actions: int = 2
    ) -> np.ndarray:
        """Predict Q_hat(x, a) for all actions.
        
        Returns:
            np.ndarray of shape (N, n_actions)
        """
        N = len(contexts)
        q_matrix = np.zeros((N, n_actions), dtype=float)
        for a in range(n_actions):
            model = q_models[a]
            if hasattr(model, "predict"):
                q_matrix[:, a] = model.predict(contexts)
            elif callable(model):
                q_matrix[:, a] = model(contexts)
        return q_matrix

    def inverse_propensity_scoring(
        self,
        actions: np.ndarray,
        rewards: np.ndarray,
        behavior_propensities: np.ndarray,
        target_propensities: np.ndarray,
    ) -> Tuple[float, float, np.ndarray]:
        """Compute Inverse Propensity Scoring (IPS) and Self-Normalized IPS (SnIPS).
        
        Returns:
            (v_ips, v_snips, weights)
        """
        eps = 1e-6
        p_b = np.maximum(behavior_propensities, eps)
        weights = target_propensities / p_b
        # Weight clipping
        clipped_weights = np.clip(weights, 0.0, self.max_weight)

        v_ips = float(np.mean(clipped_weights * rewards))
        sum_w = np.sum(clipped_weights)
        v_snips = float(np.sum(clipped_weights * rewards) / (sum_w + eps))

        return v_ips, v_snips, clipped_weights

    def direct_method(
        self,
        q_matrix: np.ndarray,
        target_probs: np.ndarray,
    ) -> float:
        """Compute Direct Method policy value: 1/N * sum_i sum_a pi(a | x_i) * Q_hat(x_i, a)."""
        # Element-wise product and row sum: expectation under target policy
        expected_q = np.sum(target_probs * q_matrix, axis=1)
        return float(np.mean(expected_q))

    def doubly_robust(
        self,
        actions: np.ndarray,
        rewards: np.ndarray,
        weights: np.ndarray,
        q_matrix: np.ndarray,
        target_probs: np.ndarray,
    ) -> Tuple[float, np.ndarray]:
        """Compute Doubly Robust (DR) policy value and per-sample DR scores.
        
        delta_i = sum_a pi(a | x_i) Q_hat(x_i, a) + w_i * (r_i - Q_hat(x_i, a_i))
        Returns:
            (v_dr, deltas)
        """
        N = len(actions)
        q_target = np.sum(target_probs * q_matrix, axis=1)
        q_chosen = q_matrix[np.arange(N), actions]

        deltas = q_target + weights * (rewards - q_chosen)
        v_dr = float(np.mean(deltas))
        return v_dr, deltas

    def bootstrap_confidence_interval(
        self,
        deltas: np.ndarray,
        ci_level: float = 0.95,
    ) -> Tuple[float, float, float, float]:
        """Compute percentile bootstrap confidence intervals for value and Sharpe ratio.
        
        Returns:
            (ci_lower, ci_upper, sharpe_ci_lower, sharpe_ci_upper)
        """
        N = len(deltas)
        if N < 2:
            val = float(deltas[0]) if N == 1 else 0.0
            return val, val, 0.0, 0.0

        resampled_means = np.zeros(self.n_bootstraps, dtype=float)
        resampled_sharpes = np.zeros(self.n_bootstraps, dtype=float)

        for b in range(self.n_bootstraps):
            idx = np.random.choice(N, size=N, replace=True)
            sample = deltas[idx]
            mean_b = np.mean(sample)
            std_b = np.std(sample, ddof=1)
            resampled_means[b] = mean_b
            resampled_sharpes[b] = mean_b / (std_b + 1e-8)

        alpha = 1.0 - ci_level
        lower_pct = 100.0 * (alpha / 2.0)
        upper_pct = 100.0 * (1.0 - alpha / 2.0)

        ci_lower = float(np.percentile(resampled_means, lower_pct))
        ci_upper = float(np.percentile(resampled_means, upper_pct))
        sharpe_ci_lower = float(np.percentile(resampled_sharpes, lower_pct))
        sharpe_ci_upper = float(np.percentile(resampled_sharpes, upper_pct))

        return ci_lower, ci_upper, sharpe_ci_lower, sharpe_ci_upper

    def evaluate_policy(
        self,
        logged_data: Union[pd.DataFrame, CounterfactualLogger, List[CandidateDecisionOpportunity], List[Dict[str, Any]], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]],
        target_policy: Any,
        policy_name: str = "target_bandit_policy",
    ) -> OPEResult:
        """Run complete Offline Policy Evaluation (IPS, SnIPS, DM, DR, Bootstrap CIs)."""
        X, actions, rewards, behavior_p = self.extract_logged_data(logged_data)
        N = len(X)
        if N == 0:
            return OPEResult(
                policy_name=policy_name,
                sample_size=0,
                ips_value=0.0,
                snips_value=0.0,
                dm_value=0.0,
                dr_value=0.0,
                ci_lower=0.0,
                ci_upper=0.0,
                sharpe_dr=0.0,
                sharpe_ci_lower=0.0,
                sharpe_ci_upper=0.0,
                weights_mean=0.0,
                weights_max=0.0,
                effective_sample_size=0.0,
            )

        n_actions = int(np.max(actions)) + 1 if len(actions) > 0 else 2
        n_actions = max(n_actions, 2)

        # Target policy propensities
        target_p, target_probs = self.get_target_policy_propensities(
            target_policy, X, actions, n_actions=n_actions
        )

        # 1. IPS & SnIPS
        v_ips, v_snips, weights = self.inverse_propensity_scoring(
            actions, rewards, behavior_p, target_p
        )

        # Effective sample size: (sum w)^2 / sum(w^2)
        ess = float((np.sum(weights) ** 2) / (np.sum(weights ** 2) + 1e-8))

        # 2. Direct Method
        q_models = self.fit_reward_model(X, actions, rewards, n_actions=n_actions)
        q_matrix = self.predict_q_values(q_models, X, n_actions=n_actions)
        v_dm = self.direct_method(q_matrix, target_probs)

        # 3. Doubly Robust
        v_dr, deltas = self.doubly_robust(actions, rewards, weights, q_matrix, target_probs)

        # 4. Bootstrap Confidence Intervals
        ci_lower, ci_upper, sharpe_lower, sharpe_upper = self.bootstrap_confidence_interval(deltas)
        std_dr = np.std(deltas, ddof=1) if N > 1 else 1.0
        sharpe_dr = float(v_dr / (std_dr + 1e-8))

        return OPEResult(
            policy_name=policy_name,
            sample_size=N,
            ips_value=v_ips,
            snips_value=v_snips,
            dm_value=v_dm,
            dr_value=v_dr,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            sharpe_dr=sharpe_dr,
            sharpe_ci_lower=sharpe_lower,
            sharpe_ci_upper=sharpe_upper,
            weights_mean=float(np.mean(weights)),
            weights_max=float(np.max(weights)),
            effective_sample_size=ess,
        )

    def evaluate_promotion_eligibility(
        self,
        logged_data: Union[pd.DataFrame, CounterfactualLogger, List[CandidateDecisionOpportunity], List[Dict[str, Any]], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]],
        target_policy: Any,
        baseline_value: float = 0.0,
        min_samples: int = 1000,
        policy_name: str = "candidate_policy",
    ) -> PromotionEvaluationResult:
        """Strict Policy Gatekeeper.
        
        Requires:
        1. Sample size >= min_samples (>= 1,000 settled bets for production promotion).
        2. DR estimate > baseline_value.
        3. Lower bound of 95% CI > baseline_value (statistically significant positive improvement).
        4. DR Sharpe ratio > 0.0.
        """
        ope = self.evaluate_policy(logged_data, target_policy, policy_name=policy_name)
        reasons: List[str] = []

        if ope.sample_size < min_samples:
            reasons.append(f"INSUFFICIENT_SAMPLE_SIZE: {ope.sample_size} < {min_samples} required")

        if ope.dr_value <= baseline_value:
            reasons.append(f"NEGATIVE_OR_ZERO_DR_VALUE: {ope.dr_value:.4f} <= baseline {baseline_value:.4f}")

        if ope.ci_lower <= baseline_value:
            reasons.append(f"NOT_STATISTICALLY_SIGNIFICANT: 95% CI lower bound {ope.ci_lower:.4f} <= baseline {baseline_value:.4f}")

        if ope.sharpe_dr <= 0.0:
            reasons.append(f"NEGATIVE_SHARPE: DR Sharpe {ope.sharpe_dr:.4f} <= 0.0")

        eligible = len(reasons) == 0
        return PromotionEvaluationResult(
            eligible=eligible,
            policy_name=policy_name,
            sample_size=ope.sample_size,
            dr_estimate=ope.dr_value,
            ci_lower=ope.ci_lower,
            ci_upper=ope.ci_upper,
            ips_estimate=ope.ips_value,
            dm_estimate=ope.dm_value,
            sharpe_estimate=ope.sharpe_dr,
            reasons=reasons,
        )
