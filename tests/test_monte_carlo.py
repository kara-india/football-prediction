import pytest
from python.simulation.match_state import MatchState
from python.simulation.event_intensities import EventIntensityEstimator
from python.simulation.monte_carlo import MonteCarloSimulator

def get_base_state():
    return MatchState(
        minute=0, added_time=0, score_home=0, score_away=0, period='first_half',
        possession_home=50.0, shots_home=0, shots_away=0, shots_on_target_home=0,
        shots_on_target_away=0, xg_home=0.0, xg_away=0.0, corners_home=0,
        corners_away=0, fouls_home=0, fouls_away=0, yellow_cards_home=0,
        yellow_cards_away=0, red_cards_home=0, red_cards_away=0, offsides_home=0,
        offsides_away=0, substitutions_home=0, substitutions_away=0,
        is_live=True, lineup_confirmed=True
    )

def test_reproducibility():
    state = get_base_state()
    estimator = EventIntensityEstimator()
    sim1 = MonteCarloSimulator(seed=42)
    res1 = sim1.simulate_match_from_state(state, 0.02, 0.02, estimator, n_simulations=100)
    
    sim2 = MonteCarloSimulator(seed=42)
    res2 = sim2.simulate_match_from_state(state, 0.02, 0.02, estimator, n_simulations=100)
    
    assert res1.score_distribution == res2.score_distribution

def test_1x2_probs_sum_to_one():
    state = get_base_state()
    estimator = EventIntensityEstimator()
    sim = MonteCarloSimulator(seed=42)
    res = sim.simulate_match_from_state(state, 0.02, 0.02, estimator, n_simulations=1000)
    probs = sim.extract_market_probabilities(res)
    assert pytest.approx(sum(probs['1x2'].values())) == 1.0

def test_draw_prob_higher_at_80():
    state0 = get_base_state()
    state80 = get_base_state()
    state80.minute = 80
    state80.period = 'second_half'
    
    estimator = EventIntensityEstimator()
    sim = MonteCarloSimulator(seed=42)
    
    res0 = sim.simulate_match_from_state(state0, 0.02, 0.02, estimator, n_simulations=5000)
    res80 = sim.simulate_match_from_state(state80, 0.02, 0.02, estimator, n_simulations=5000)
    
    p0 = sim.extract_market_probabilities(res0)['1x2']['X']
    p80 = sim.extract_market_probabilities(res80)['1x2']['X']
    
    assert p80 > p0

def test_home_win_prob_high_at_75_when_2_0():
    state = get_base_state()
    state.minute = 75
    state.period = 'second_half'
    state.score_home = 2
    
    estimator = EventIntensityEstimator()
    sim = MonteCarloSimulator(seed=42)
    res = sim.simulate_match_from_state(state, 0.02, 0.02, estimator, n_simulations=1000)
    probs = sim.extract_market_probabilities(res)
    
    assert probs['1x2']['1'] > probs['1x2']['2']
    assert probs['1x2']['1'] > 0.8

def test_away_win_prob_high_at_75_when_0_2():
    state = get_base_state()
    state.minute = 75
    state.period = 'second_half'
    state.score_away = 2
    
    estimator = EventIntensityEstimator()
    sim = MonteCarloSimulator(seed=42)
    res = sim.simulate_match_from_state(state, 0.02, 0.02, estimator, n_simulations=1000)
    probs = sim.extract_market_probabilities(res)
    
    assert probs['1x2']['2'] > probs['1x2']['1']
    assert probs['1x2']['2'] > 0.8

def test_btts_yes_at_85_1_1():
    state = get_base_state()
    state.minute = 85
    state.period = 'second_half'
    state.score_home = 1
    state.score_away = 1
    
    estimator = EventIntensityEstimator()
    sim = MonteCarloSimulator(seed=42)
    res = sim.simulate_match_from_state(state, 0.02, 0.02, estimator, n_simulations=1000)
    probs = sim.extract_market_probabilities(res)
    
    assert pytest.approx(probs['btts']['yes']) == 1.0

def test_over_25_high_at_0_when_2_1():
    state = get_base_state()
    state.score_home = 2
    state.score_away = 1
    
    estimator = EventIntensityEstimator()
    sim = MonteCarloSimulator(seed=42)
    res = sim.simulate_match_from_state(state, 0.02, 0.02, estimator, n_simulations=1000)
    probs = sim.extract_market_probabilities(res)
    
    assert pytest.approx(probs['over_under_25']['over']) == 1.0

def test_score_state_effect():
    # 2-0 at 75 vs 0-0 at 75
    state_2_0 = get_base_state()
    state_2_0.minute = 75
    state_2_0.period = 'second_half'
    state_2_0.score_home = 2
    
    state_0_0 = get_base_state()
    state_0_0.minute = 75
    state_0_0.period = 'second_half'
    
    estimator = EventIntensityEstimator()
    sim1 = MonteCarloSimulator(seed=42)
    res_2_0 = sim1.simulate_match_from_state(state_2_0, 0.02, 0.02, estimator, n_simulations=5000)
    
    sim2 = MonteCarloSimulator(seed=42)
    res_0_0 = sim2.simulate_match_from_state(state_0_0, 0.02, 0.02, estimator, n_simulations=5000)
    
    away_goals_2_0 = [p.final_score_away - state_2_0.score_away for p in res_2_0.paths]
    away_goals_0_0 = [p.final_score_away - state_0_0.score_away for p in res_0_0.paths]
    
    assert sum(away_goals_2_0) != sum(away_goals_0_0)
