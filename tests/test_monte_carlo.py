import math
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

def test_neutral_simulator_has_no_hidden_score_or_red_card_effect():
    state_a = get_base_state()
    state_b = get_base_state()
    state_b.score_home = 2
    state_b.score_away = 0
    state_b.minute = 75
    state_b.period = 'second_half'

    state_c = get_base_state()
    state_c.red_cards_home = 1

    sim_a = MonteCarloSimulator(seed=123)
    sim_b = MonteCarloSimulator(seed=123)
    sim_c = MonteCarloSimulator(seed=123)

    res_a = sim_a.simulate_match_from_state(state_a, 0.02, 0.02, n_simulations=5000)
    res_b = sim_b.simulate_match_from_state(state_b, 0.02, 0.02, n_simulations=5000)
    res_c = sim_c.simulate_match_from_state(state_c, 0.02, 0.02, n_simulations=5000)

    # Without a fitted hazard model, the future goal process is identical;
    # the observed starting score/red card may change the final outcome,
    # but must not silently change goal intensity.
    assert res_a.goal_distribution == res_c.goal_distribution
    assert res_a.goal_distribution == {
        total_goals: prob
        for total_goals, prob in res_b.goal_distribution.items()
    }

def test_standard_error_matches_theoretical_formula():
    """Verify empirical standard error matches sqrt(p * (1 - p) / N) and decays with 1/sqrt(N)."""
    state = get_base_state()
    sim = MonteCarloSimulator(seed=42)

    # 1. Test at N = 10,000
    res_10k = sim.simulate_match_from_state(state, 0.02, 0.02, n_simulations=10000)
    p_home_10k = sum(1 for p in res_10k.paths if p.final_score_home > p.final_score_away) / 10000
    expected_se_10k = math.sqrt(p_home_10k * (1.0 - p_home_10k) / 10000)

    assert pytest.approx(res_10k.std_error, rel=0.15) == expected_se_10k

    # 2. Test at N = 40,000 (should be roughly half the standard error of 10,000: 1/sqrt(4) = 0.5)
    res_40k = sim.simulate_match_from_state(state, 0.02, 0.02, n_simulations=40000)
    assert res_40k.std_error < res_10k.std_error
    ratio = res_40k.std_error / res_10k.std_error
    assert 0.40 <= ratio <= 0.60


def test_vectorized_cpu_benchmark_10k_paths():
    """Verify 10,000 paths simulate in < 250ms on CPU."""
    import time
    state = get_base_state()
    sim = MonteCarloSimulator(seed=42)

    t0 = time.perf_counter()
    res = sim.simulate_match_from_state(state, 0.02, 0.02, n_simulations=10000)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert len(res.paths) == 10000
    assert elapsed_ms < 250.0, f"Simulation exceeded 250ms benchmark: took {elapsed_ms:.1f}ms"


def test_vectorized_simulator_early_convergence():
    """Verify simulate_with_convergence halts early when target standard error is achieved."""
    from python.simulation.vectorized_mc import VectorizedMonteCarloSimulator
    vec_sim = VectorizedMonteCarloSimulator(seed=42)
    state = get_base_state()

    paths, dist = vec_sim.simulate_with_convergence(
        state=state,
        home_lambda_per_min=0.02,
        away_lambda_per_min=0.02,
        min_simulations=10000,
        max_simulations=50000,
        target_std_error=0.005,
        batch_size=5000,
    )

    assert dist["std_error"] <= 0.005
    assert len(paths) >= 10000

