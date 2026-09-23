"""
Comprehensive Unit Tests for Contextual Bandit Policy, Counterfactual Logging,
Strict Safety Subordination, and Offline Policy Evaluation (OPE).
"""

import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from python.engine.nobet_gate import NoBetGate
from python.rl.action_space import Action, V1_ACTIONS
from python.rl.bandit_policy import (
    LinUCBAgent,
    ThompsonSamplingAgent,
    RLDecisionLayer,
)
from python.rl.counterfactual_logger import (
    CounterfactualLogger,
    CandidateDecisionOpportunity,
)
from python.rl.off_policy_evaluator import (
    OffPolicyEvaluator,
    OPEResult,
    PromotionEvaluationResult,
)
from python.rl.reward import MultiObjectiveRewardCalculator, RewardCalculator


class MockCandidate:
    """Mock prediction candidate for testing decision logic and safety gates."""
    def __init__(
        self,
        decision="BET_CANDIDATE",
        ev=0.08,
        value_edge=0.05,
        lineup_confirmed=True,
        home_starters_count=11,
        away_starters_count=11,
        odds_age_seconds=60.0,
        monte_carlo_se=0.01,
        decimal_odds=2.10,
        calibrated_probability=0.52,
        raw_probability=0.55,
        probability_lower=0.47,
        probability_upper=0.57,
        uncertainty=0.02,
        is_market_suspended=False,
        odds_available=True,
    ):
        self.market = "1x2_home"
        self.competition = "Premier League"
        self.selection = "Home"
        self.decimal_odds = decimal_odds
        self.implied_probability = 1.0 / decimal_odds
        self.calibrated_probability = calibrated_probability
        self.raw_probability = raw_probability
        self.expected_value = ev
        self.value_edge = value_edge
        self.probability_lower = probability_lower
        self.probability_upper = probability_upper
        self.uncertainty = uncertainty
        self.lineup_confirmed = lineup_confirmed
        self.home_starters_count = home_starters_count
        self.away_starters_count = away_starters_count
        self.odds_age_seconds = odds_age_seconds
        self.monte_carlo_se = monte_carlo_se
        self.is_market_suspended = is_market_suspended
        self.odds_available = odds_available
        self.data_freshness_score = 1.0
        self.odds_freshness_score = 1.0
        self.model_confidence = 0.95
        self.simulation_count_log = 4.0
        self.market_history_n = 500
        self.decision = decision
        self.candidate_id = "test_cand_001"
        self.fixture_id = 99999
        self.match_timestamp = "2026-09-24T18:00:00Z"


class MockMatchState:
    def __init__(self, is_live=False):
        self.minute = 0.0
        self.score_difference = 0
        self.total_goals = 0
        self.red_cards_home = 0
        self.red_cards_away = 0
        self.is_live = is_live
        self.competition_tier = 1


# =========================================================================
# 1. Counterfactual Logger Tests
# =========================================================================

def test_counterfactual_logging_all_candidates_and_settlement():
    """Verify logging of candidate opportunities (both BET and ABSTAIN) and settlement."""
    logger = CounterfactualLogger()

    # 1. Log a BET opportunity
    opp1 = logger.record_opportunity(
        fixture_id=101,
        match_timestamp="2026-09-24T12:00:00Z",
        market="1x2_home",
        competition="La Liga",
        decimal_odds=2.20,
        fair_probability=0.48,
        expected_value=0.06,
        value_edge=0.04,
        raw_probability=0.50,
        calibrated_probability=0.49,
        probability_interval=(0.44, 0.54),
        gate_action="BET",
        gate_reasons=[],
        chosen_action="BET",
        action_propensity=0.75,
        uncertainty=0.02,
        lineup_verified=True,
    )

    # 2. Log an ABSTAIN / Rejected opportunity
    opp2 = logger.record_opportunity(
        fixture_id=102,
        match_timestamp="2026-09-24T14:30:00Z",
        market="over_2.5",
        competition="Serie A",
        decimal_odds=1.85,
        fair_probability=0.55,
        expected_value=-0.04,
        value_edge=-0.02,
        raw_probability=0.52,
        calibrated_probability=0.51,
        probability_interval=(0.45, 0.57),
        gate_action="NO_BET",
        gate_reasons=["NEGATIVE_EV"],
        chosen_action="ABSTAIN",
        action_propensity=1.0,
        uncertainty=0.03,
        lineup_verified=True,
    )

    assert len(logger) == 2
    assert opp1.action_propensity == 0.75
    assert opp2.action_propensity == 1.0
    assert opp1.settled is False

    # Settle opp1 (BET won at 2.20 odds with closing odds 2.00)
    logger.log_settlement(
        candidate_id=opp1.candidate_id,
        actual_outcome="win",
        closing_odds=2.00,
    )
    settled_opp1 = logger.get_candidate(opp1.candidate_id)
    assert settled_opp1.settled is True
    assert pytest.approx(settled_opp1.realized_return) == 1.20  # (2.20 - 1.0)
    assert pytest.approx(settled_opp1.clv) == (2.20 / 2.00) - 1.0  # +10% CLV
    assert settled_opp1.counterfactual_return == 0.0  # Counterfactual ABSTAIN has 0 return

    # Settle opp2 (ABSTAIN settled, actual match had under 2.5 goals -> loss for over)
    logger.log_settlement(
        candidate_id=opp2.candidate_id,
        actual_outcome="loss",
        closing_odds=1.80,
    )
    settled_opp2 = logger.get_candidate(opp2.candidate_id)
    assert settled_opp2.settled is True
    assert settled_opp2.realized_return == 0.0  # We abstained, 0 realized return
    assert pytest.approx(settled_opp2.counterfactual_return) == -1.0  # Had we bet, we would have lost 1 unit


def test_counterfactual_logger_serialization_and_dataframe():
    """Verify serialization to JSON, round-trip loading, and DataFrame export."""
    logger = CounterfactualLogger()
    logger.record_opportunity(
        candidate_id="cand_123",
        fixture_id=555,
        match_timestamp="2026-09-24T20:00:00Z",
        market="BTTS_yes",
        competition="UCL",
        decimal_odds=1.90,
        fair_probability=0.55,
        expected_value=0.045,
        value_edge=0.03,
        raw_probability=0.58,
        calibrated_probability=0.55,
        probability_interval=(0.50, 0.60),
        gate_action="BET",
        gate_reasons=[],
        chosen_action="BET",
        action_propensity=0.68,
        context_vector=[1.90, 0.55, 0.045, 0.03, 0.55, 0.10, 0.02, 0.5, 1.0, 1.0],
    )
    logger.log_settlement(candidate_id="cand_123", actual_outcome="loss")

    # DataFrame export
    df = logger.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df["candidate_id"].iloc[0] == "cand_123"
    assert df["realized_return"].iloc[0] == -1.0
    assert "feature_0" in df.columns

    # JSON round-trip
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        logger.to_json(tmp_path)
        loaded = CounterfactualLogger.from_json(tmp_path)
        assert len(loaded) == 1
        opp = loaded.get_candidate("cand_123")
        assert opp is not None
        assert opp.fixture_id == 555
        assert opp.realized_return == -1.0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# =========================================================================
# 2. Contextual Bandit Agents (LinUCB & Thompson Sampling)
# =========================================================================

def test_linucb_agent_action_selection_and_updates():
    """Test LinUCB agent score calculation, propensity computation, and parameter updates."""
    agent = LinUCBAgent(n_actions=2, n_features=5, alpha=1.0, temperature=1.0)
    context = np.array([1.0, 0.5, -0.2, 0.8, 0.1])

    # Initial state (covariance = I, response = 0): scores are driven by confidence radius
    scores = agent.get_ucb_scores(context)
    assert len(scores) == 2
    # Because A_0 = A_1 = I and b_0 = b_1 = 0, initial scores are equal
    assert np.isclose(scores[0], scores[1])

    # Default tie-breaking selects ABSTAIN (action index 0)
    assert agent.select_action(context, sample=False) == 0

    # Propensities should be equal and sum to 1.0
    propensities = agent.get_action_propensities(context)
    assert len(propensities) == 2
    assert np.isclose(propensities[0], 0.5)
    assert np.isclose(propensities[1], 0.5)

    # Reward BET action (action 1) with large positive returns
    for _ in range(5):
        agent.update(action=1, context=context, reward=2.5)

    # After positive reward updates, action 1 should have higher UCB score and higher propensity
    updated_scores = agent.get_ucb_scores(context)
    assert updated_scores[1] > updated_scores[0]
    updated_props = agent.get_action_propensities(context)
    assert updated_props[1] > updated_props[0]
    assert agent.select_action(context, sample=False) == 1

    # Serialization test
    serialized = agent.serialize()
    reconstructed = LinUCBAgent.from_dict(serialized)
    assert np.allclose(reconstructed.b[1], agent.b[1])


def test_thompson_sampling_agent_action_selection_and_updates():
    """Test Thompson Sampling Bayesian linear regression, analytical propensities, and updates."""
    agent = ThompsonSamplingAgent(n_actions=2, n_features=4, v=0.5)
    context = np.array([1.0, -0.5, 0.3, 0.7])

    # Initial propensities
    p_initial = agent.get_action_propensities(context)
    assert len(p_initial) == 2
    assert np.isclose(p_initial[0], 0.5, atol=0.05)
    assert np.isclose(np.sum(p_initial), 1.0)

    # Heavily reward action 1 (BET)
    for _ in range(10):
        agent.update(action=1, context=context, reward=3.0)

    # Heavily penalize action 0 (ABSTAIN)
    for _ in range(10):
        agent.update(action=0, context=context, reward=-1.0)

    p_updated = agent.get_action_propensities(context)
    assert p_updated[1] > 0.90
    assert p_updated[0] < 0.10

    # Greedy action should be 1
    assert agent.select_action(context, sample=False) == 1

    # Serialization test
    serialized = agent.serialize()
    reconstructed = ThompsonSamplingAgent.from_dict(serialized)
    assert np.allclose(reconstructed.f[1], agent.f[1])


# =========================================================================
# 3. Strict Statistical Subordination & Adversarial States
# =========================================================================

def test_strict_subordination_adversarial_states():
    """Verify that under any safety gate failure, bandit is physically prohibited from betting."""
    agent = LinUCBAgent(n_features=20, alpha=1.0)
    # Prime agent with extreme positive bias for action 1 (BET)
    agent.b[1] = np.full(20, 100.0)

    layer = RLDecisionLayer(agent=agent, min_observations=0, mode="ACTIVE")
    layer.is_enabled = True

    match_state = MockMatchState()

    # 1. Adversarial State: Negative EV (ev = -0.05)
    cand_neg_ev = MockCandidate(ev=-0.05)
    decision = layer.decide(cand_neg_ev, match_state, n_settled_bets=2000)
    assert decision == "NO_BET", "Bandit must not override Negative EV gate"

    # 2. Adversarial State: Unconfirmed Lineup (lineup_confirmed = False)
    cand_unconf_lineup = MockCandidate(ev=0.10, lineup_confirmed=False)
    decision = layer.decide(cand_unconf_lineup, match_state, n_settled_bets=2000)
    assert decision == "NO_BET", "Bandit must not override unconfirmed lineups"

    # 3. Adversarial State: Invalid starter count (10 starters instead of 11)
    cand_starter_count = MockCandidate(ev=0.10, home_starters_count=10)
    decision = layer.decide(cand_starter_count, match_state, n_settled_bets=2000)
    assert decision == "NO_BET", "Bandit must not override incomplete 11 vs 11 lineup sheet"

    # 4. Adversarial State: Stale Odds (age > 900 seconds pre-match)
    cand_stale_odds = MockCandidate(ev=0.10, odds_age_seconds=1200.0)
    decision = layer.decide(cand_stale_odds, match_state, n_settled_bets=2000)
    assert decision == "NO_BET", "Bandit must not override stale odds gate"

    # 5. Adversarial State: High Uncertainty (Monte Carlo SE > 0.02)
    cand_high_se = MockCandidate(ev=0.10, monte_carlo_se=0.05)
    decision = layer.decide(cand_high_se, match_state, n_settled_bets=2000)
    assert decision == "NO_BET", "Bandit must not override high uncertainty gate"

    # 6. Adversarial State: Market Suspended
    cand_suspended = MockCandidate(ev=0.10, is_market_suspended=True)
    decision = layer.decide(cand_suspended, match_state, n_settled_bets=2000)
    assert decision == "NO_BET", "Bandit must not override suspended market"

    # 7. Safe State: All gates pass -> Active bandit allowed to bet
    cand_safe = MockCandidate(ev=0.10, lineup_confirmed=True, odds_age_seconds=30.0, monte_carlo_se=0.005)
    decision = layer.decide(cand_safe, match_state, n_settled_bets=2000)
    assert decision == "BET_CANDIDATE", "Bandit allowed to select BET only when all safety gates pass"


def test_research_mode_quarantine():
    """Verify that in RESEARCH mode, production decision defaults to statistical champion."""
    agent = LinUCBAgent(n_features=20)
    layer = RLDecisionLayer(agent=agent, min_observations=1000, mode="RESEARCH")
    layer.is_enabled = False  # Research default

    cand = MockCandidate(decision="BET_CANDIDATE", ev=0.08)
    match_state = MockMatchState()

    # In research mode, production decision is pass-through champion
    assert layer.decide(cand, match_state, n_settled_bets=50) == "BET_CANDIDATE"

    # Even if enabled, if n_settled_bets < 1000, still research quarantine
    layer.is_enabled = True
    assert layer.decide(cand, match_state, n_settled_bets=500) == "BET_CANDIDATE"


# =========================================================================
# 4. Multi-Objective Reward Function
# =========================================================================

def test_multi_objective_reward_calculation():
    """Test Reward = PnL_flat_stake + lambda_clv * CLV - gamma_uncertainty * uncertainty."""
    calc = MultiObjectiveRewardCalculator(lambda_clv=0.5, gamma_uncertainty=0.2)

    # 1. ABSTAIN action always yields 0.0 reward
    r_abstain = calc.calculate(
        action="ABSTAIN",
        outcome="win",
        decimal_odds=2.50,
        clv=0.10,
        uncertainty=0.05,
    )
    assert r_abstain == 0.0

    # 2. Winning BET:
    # decimal_odds = 2.40 -> PnL = 1.40
    # CLV = +0.10 (beat closing odds) -> bonus = 0.5 * 0.10 = +0.05
    # uncertainty = 0.05 -> penalty = 0.2 * 0.05 = -0.01
    # Total Reward = 1.40 + 0.05 - 0.01 = 1.44
    r_win = calc.calculate(
        action="BET",
        outcome="win",
        decimal_odds=2.40,
        clv=0.10,
        uncertainty=0.05,
    )
    assert pytest.approx(r_win) == 1.44

    # 3. Losing BET with negative CLV and higher uncertainty:
    # PnL = -1.0
    # CLV = -0.04 -> bonus = 0.5 * (-0.04) = -0.02
    # uncertainty = 0.10 -> penalty = 0.2 * 0.10 = -0.02
    # Total Reward = -1.0 - 0.02 - 0.02 = -1.04
    r_loss = calc.calculate(
        action="BET",
        outcome="loss",
        decimal_odds=2.00,
        clv=-0.04,
        uncertainty=0.10,
    )
    assert pytest.approx(r_loss) == -1.04

    # 4. Backwards-compatible RewardCalculator delegation
    legacy_calc = RewardCalculator(lambda_clv=0.5, gamma_uncertainty=0.2)
    r_delegated = legacy_calc.calculate_multi_objective(
        action="BET",
        outcome="win",
        decimal_odds=2.40,
        clv=0.10,
        uncertainty=0.05,
    )
    assert pytest.approx(r_delegated) == 1.44


# =========================================================================
# 5. Offline Policy Evaluation (IPS, DM, DR, Bootstrap)
# =========================================================================

def test_off_policy_evaluation_ips_dm_dr():
    """Verify OPE engine computes valid IPS, DM, and DR values with bootstrap CIs."""
    np.random.seed(42)
    N = 200
    d = 4

    # Generate synthetic logged dataset
    contexts = np.random.randn(N, d)
    # Behavior policy: randomized exploration with propensity p_b ~ Uniform(0.3, 0.7)
    behavior_p = np.random.uniform(0.3, 0.7, size=N)
    actions = (np.random.rand(N) < behavior_p).astype(int)

    # True reward generating process: action 1 has positive payoff when context[0] > 0
    rewards = np.zeros(N)
    for i in range(N):
        if actions[i] == 1:
            rewards[i] = 1.0 if contexts[i, 0] > 0 else -1.0
        else:
            rewards[i] = 0.0

    evaluator = OffPolicyEvaluator(max_weight=20.0, n_bootstraps=500, random_seed=42)

    # Target policy: bets when context[0] > 0, abstains otherwise (smart policy)
    def smart_target_policy(x):
        return 1 if x[0] > 0 else 0

    logged_data = (contexts, actions, rewards, behavior_p)
    result = evaluator.evaluate_policy(logged_data, smart_target_policy, policy_name="smart_policy")

    assert isinstance(result, OPEResult)
    assert result.sample_size == N
    # Smart policy should achieve positive value on DR, IPS, and DM
    assert result.dr_value > 0.0
    assert result.ips_value > 0.0
    assert result.dm_value > 0.0
    # Bootstrap confidence intervals must bound point estimates
    assert result.ci_lower < result.dr_value < result.ci_upper
    assert result.weights_max <= 20.0  # Clipped to max_weight


# =========================================================================
# 6. Policy Promotion Gatekeeper
# =========================================================================

def test_policy_promotion_gatekeeper_rejection_and_acceptance():
    """Verify gatekeeper rejects inferior/noisy policies and accepts statistically superior ones."""
    np.random.seed(42)
    N = 1200
    d = 3
    contexts = np.random.randn(N, d)
    behavior_p = np.full(N, 0.5)
    actions = (np.random.rand(N) < 0.5).astype(int)

    evaluator = OffPolicyEvaluator(max_weight=20.0, n_bootstraps=300, random_seed=42)

    # 1. Inferior Policy: Always bets on negative expectation
    bad_rewards = np.where(actions == 1, -1.0, 0.0)
    bad_logged_data = (contexts, actions, bad_rewards, behavior_p)
    bad_policy = lambda x: 1  # Always bets

    bad_decision = evaluator.evaluate_promotion_eligibility(
        bad_logged_data, bad_policy, baseline_value=0.0, min_samples=1000
    )
    assert bad_decision.eligible is False
    assert any("NEGATIVE_OR_ZERO_DR_VALUE" in r for r in bad_decision.reasons)

    # 2. Insufficient Data: Sample size < min_samples
    small_contexts = contexts[:200]
    small_actions = actions[:200]
    small_rewards = np.where(small_actions == 1, 1.5, 0.0)
    small_p = behavior_p[:200]
    small_logged_data = (small_contexts, small_actions, small_rewards, small_p)

    small_decision = evaluator.evaluate_promotion_eligibility(
        small_logged_data, lambda x: 1, baseline_value=0.0, min_samples=1000
    )
    assert small_decision.eligible is False
    assert any("INSUFFICIENT_SAMPLE_SIZE" in r for r in small_decision.reasons)

    # 3. Statistically Superior Policy: High win rate on action 1 with 1,200 samples
    good_rewards = np.where(actions == 1, 1.5, 0.0)
    good_logged_data = (contexts, actions, good_rewards, behavior_p)
    good_policy = lambda x: 1

    good_decision = evaluator.evaluate_promotion_eligibility(
        good_logged_data, good_policy, baseline_value=0.0, min_samples=1000
    )
    assert good_decision.eligible is True
    assert len(good_decision.reasons) == 0
    assert good_decision.dr_estimate > 0.0
    assert good_decision.ci_lower > 0.0
    assert good_decision.sharpe_estimate > 0.0
