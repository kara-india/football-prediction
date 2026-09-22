import numpy as np
import pytest
from python.rl.state_representation import RLState
from python.rl.action_space import Action, V1_ACTIONS
from python.rl.reward import RewardCalculator
from python.rl.contextual_bandit import LinUCBAgent, RLDecisionLayer
from python.rl.experience_replay import Experience, ExperienceReplay
from datetime import datetime

class DummyCandidate:
    def __init__(self, decision='BET_CANDIDATE'):
        self.market = 'Match Odds'
        self.selection = 'Home'
        self.decimal_odds = 2.0
        self.implied_probability = 0.5
        self.calibrated_probability = 0.55
        self.raw_probability = 0.6
        self.expected_value = 0.1
        self.probability_lower = 0.4
        self.probability_upper = 0.7
        self.uncertainty = 0.1
        self.data_freshness_score = 1.0
        self.odds_freshness_score = 1.0
        self.model_confidence = 0.9
        self.simulation_count_log = 3.0
        self.market_history_n = 100
        self.decision = decision

class DummyMatchState:
    def __init__(self):
        self.minute = 0.5
        self.score_difference = 1
        self.total_goals = 1
        self.red_cards_home = 0
        self.red_cards_away = 0
        self.is_live = True
        self.competition_tier = 1

def test_rl_state_array():
    candidate = DummyCandidate()
    match_state = DummyMatchState()
    state = RLState.from_candidate(candidate, match_state)
    arr = state.to_array()
    assert len(arr) == 20
    assert np.all(arr >= -1.0) and np.all(arr <= 1.0)

def test_rl_decision_layer_disabled():
    agent = LinUCBAgent(n_features=20)
    reward_calc = RewardCalculator()
    layer = RLDecisionLayer(agent, reward_calc, min_observations=0)
    layer.is_enabled = False
    
    candidate = DummyCandidate('BET_CANDIDATE')
    match_state = DummyMatchState()
    assert layer.decide(candidate, match_state, 1000) == 'BET_CANDIDATE'

def test_rl_decision_layer_min_observations():
    agent = LinUCBAgent(n_features=20)
    reward_calc = RewardCalculator()
    layer = RLDecisionLayer(agent, reward_calc, min_observations=500)
    layer.is_enabled = True
    
    candidate = DummyCandidate('BET_CANDIDATE')
    match_state = DummyMatchState()
    assert layer.decide(candidate, match_state, 100) == 'BET_CANDIDATE'

def test_rl_cannot_override_no_bet():
    agent = LinUCBAgent(n_features=20)
    reward_calc = RewardCalculator()
    layer = RLDecisionLayer(agent, reward_calc, min_observations=0)
    layer.is_enabled = True
    
    candidate = DummyCandidate('NO_BET')
    match_state = DummyMatchState()
    assert layer.decide(candidate, match_state, 1000) == 'NO_BET'

def test_reward_win_loss():
    calc = RewardCalculator()
    r_win = calc.calculate_reward('BET', 'win', 2.0, 1.0, 0.5, 0, 0.0, 0.0)
    assert r_win == 1.0
    r_loss = calc.calculate_reward('BET', 'loss', 2.0, 1.0, 0.5, 0, 0.0, 0.0)
    assert r_loss == -1.0

def test_reward_stale_data():
    calc = RewardCalculator()
    r = calc.calculate_reward('BET', 'win', 2.0, 1.0, 0.5, 400, 0.0, 0.0)
    assert r < 1.0  # Penalty applied

def test_linucb_selects_abstain_when_uncertain():
    agent = LinUCBAgent(n_features=20, alpha=1.0)
    context = np.zeros(20)
    action = agent.select_action(context)
    assert action == 0  # ABSTAIN

def test_linucb_update():
    agent = LinUCBAgent(n_features=20)
    context = np.ones(20)
    agent.update(0, context, 1.0)
    assert np.any(agent.b[0] != 0)

def test_experience_replay():
    er = ExperienceReplay(max_size=2)
    e1 = Experience(np.zeros(20), 0, 1.0, np.zeros(20), True, datetime.now(), 'id1')
    e2 = Experience(np.zeros(20), 0, 1.0, np.zeros(20), True, datetime.now(), 'id2')
    e3 = Experience(np.zeros(20), 0, 1.0, np.zeros(20), True, datetime.now(), 'id3')
    er.add(e1)
    er.add(e2)
    er.add(e3)
    assert len(er) == 2
    batch = er.sample(2)
    assert len(batch) == 2
