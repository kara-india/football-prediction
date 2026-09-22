import pytest
import numpy as np
from python.calibration.calibrator import ProbabilityCalibrator
from python.calibration.ev_calculator import EVCalculator
from python.calibration.no_bet_gate import NoBetGate

def test_brier_score_perfect():
    cal = ProbabilityCalibrator()
    y_true = np.array([1, 0, 1, 0])
    y_pred = np.array([1.0, 0.0, 1.0, 0.0])
    assert cal.compute_brier_score(y_true, y_pred) == 0.0

def test_brier_score_wrong():
    cal = ProbabilityCalibrator()
    y_true = np.array([1, 0, 1, 0])
    y_pred = np.array([0.0, 1.0, 0.0, 1.0])
    assert cal.compute_brier_score(y_true, y_pred) == 1.0

def test_log_loss_finite():
    cal = ProbabilityCalibrator()
    y_true = np.array([1, 0])
    y_pred = np.array([1.0, 0.0])  # Log of 0 normally infinite
    loss = cal.compute_log_loss(y_true, y_pred)
    assert np.isfinite(loss)
    assert loss < 1e-5

def test_ece_perfect():
    cal = ProbabilityCalibrator()
    y_true = np.array([1, 0, 1, 0])
    y_pred = np.array([1.0, 0.0, 1.0, 0.0])
    assert cal.compute_ece(y_true, y_pred) == 0.0

def test_ev_binary():
    ev_calc = EVCalculator()
    assert ev_calc.compute_ev_binary(0.6, 2.0) > 0.0
    assert ev_calc.compute_ev_binary(0.4, 2.0) < 0.0
    assert ev_calc.compute_ev_binary(0.5, 2.0) == 0.0

def test_de_vig():
    ev_calc = EVCalculator()
    odds = [2.0, 3.0, 6.0]  # Implied: 0.5 + 0.333 + 0.166 = 1.0
    probs = ev_calc.de_vig_multiplicative(odds)
    assert pytest.approx(sum(probs)) == 1.0
    
    odds_vig = [1.9, 2.8, 5.5]
    probs_vig = ev_calc.de_vig_multiplicative(odds_vig)
    assert pytest.approx(sum(probs_vig)) == 1.0

def test_implied_prob():
    ev_calc = EVCalculator()
    assert ev_calc.compute_implied_probability(2.0) == 0.5
    assert ev_calc.compute_implied_probability(4.0) == 0.25

def test_no_bet_gate_stale_odds():
    gate = NoBetGate()
    result = gate.evaluate(
        market='1x2', selection='1', line=None, decimal_odds=2.0, raw_probability=0.6,
        market_probability=0.5, calibrated_probability=0.6, probability_lower=0.55, probability_upper=0.65,
        simulation_count=20000, simulation_std_error=0.005, data_freshness_seconds=10, odds_freshness_seconds=4000,
        is_live=False, lineup_confirmed=True, is_market_suspended=False, model_calibrated=True,
        historical_sample_size=500, provider_healthy=True
    )
    assert not result.is_candidate
    assert 'STALE_ODDS' in result.no_bet_reasons

def test_no_bet_gate_negative_ev():
    gate = NoBetGate()
    result = gate.evaluate(
        market='1x2', selection='1', line=None, decimal_odds=1.5, raw_probability=0.4,
        market_probability=0.5, calibrated_probability=0.4, probability_lower=0.35, probability_upper=0.45,
        simulation_count=20000, simulation_std_error=0.005, data_freshness_seconds=10, odds_freshness_seconds=10,
        is_live=False, lineup_confirmed=True, is_market_suspended=False, model_calibrated=True,
        historical_sample_size=500, provider_healthy=True
    )
    assert not result.is_candidate
    assert 'NEGATIVE_EV' in result.no_bet_reasons

def test_no_bet_gate_suspended():
    gate = NoBetGate()
    result = gate.evaluate(
        market='1x2', selection='1', line=None, decimal_odds=2.5, raw_probability=0.5,
        market_probability=0.4, calibrated_probability=0.5, probability_lower=0.45, probability_upper=0.55,
        simulation_count=20000, simulation_std_error=0.005, data_freshness_seconds=10, odds_freshness_seconds=10,
        is_live=False, lineup_confirmed=True, is_market_suspended=True, model_calibrated=True,
        historical_sample_size=500, provider_healthy=True
    )
    assert not result.is_candidate
    assert 'MARKET_SUSPENDED' in result.no_bet_reasons

def test_no_bet_gate_pass():
    gate = NoBetGate()
    result = gate.evaluate(
        market='1x2', selection='1', line=None, decimal_odds=2.5, raw_probability=0.5,
        market_probability=0.4, calibrated_probability=0.5, probability_lower=0.45, probability_upper=0.55,
        simulation_count=20000, simulation_std_error=0.005, data_freshness_seconds=10, odds_freshness_seconds=10,
        is_live=False, lineup_confirmed=True, is_market_suspended=False, model_calibrated=True,
        historical_sample_size=500, provider_healthy=True
    )
    assert result.is_candidate
    assert result.decision == 'BET_CANDIDATE'

def test_probability_interval():
    ev_calc = EVCalculator()
    results = [float(x) for x in range(101)] # 0 to 100
    lower, upper = ev_calc.compute_probability_interval(results, confidence=0.90)
    assert lower == pytest.approx(5.0)
    assert upper == pytest.approx(95.0)

def test_kelly_fraction():
    ev_calc = EVCalculator()
    kelly_pos = ev_calc.compute_kelly_fraction(0.55, 2.0, fraction=0.25)
    assert kelly_pos > 0.0
    
    kelly_neg = ev_calc.compute_kelly_fraction(0.45, 2.0, fraction=0.25)
    assert kelly_neg == 0.0
