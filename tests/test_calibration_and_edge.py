"""
Unit and Integration Tests for Probability Calibration and Edge Calculation Engine
Tests out-of-sample calibration (Isotonic and Platt), ECE, Brier score, reliability diagrams,
EV calculation, edge calculation, fractional Kelly sizing, and the authoritative 10-point NO-BET gate.
"""
import pytest
import numpy as np

from python.calibration.calibrator import ProbabilityCalibrator
from python.engine.edge_calculator import EdgeCalculator, CandidateSelection
from python.engine.nobet_gate import NoBetGate, NoBetGateResult


class TestProbabilityCalibrator:
    """Tests for ProbabilityCalibrator supporting Isotonic and Platt scaling."""

    def test_fit_and_calibrate_isotonic(self):
        calibrator = ProbabilityCalibrator(method="isotonic")
        np.random.seed(42)
        # Synthetic miscalibrated predictions: model overconfident
        raw_probs = np.random.uniform(0.1, 0.9, size=200)
        true_labels = (np.random.uniform(0, 1, size=200) < (raw_probs ** 1.5)).astype(int)

        # Train on out-of-sample calibration fold
        calibrator.fit(true_labels[:100], raw_probs[:100], method="isotonic")
        calibrated_test = calibrator.calibrate(raw_probs[100:], method="isotonic")

        assert isinstance(calibrated_test, np.ndarray)
        assert len(calibrated_test) == 100
        assert np.all(calibrated_test >= 0.001)
        assert np.all(calibrated_test <= 0.999)

    def test_fit_and_calibrate_platt_logistic(self):
        calibrator = ProbabilityCalibrator(method="platt")
        np.random.seed(123)
        raw_probs = np.random.uniform(0.1, 0.9, size=200)
        true_labels = (np.random.uniform(0, 1, size=200) < raw_probs).astype(int)

        calibrator.fit(true_labels[:100], raw_probs[:100], method="platt")
        eval_probs = np.linspace(0.1, 0.9, 50)
        calibrated_test = calibrator.calibrate(eval_probs, method="platt")

        assert isinstance(calibrated_test, np.ndarray)
        assert len(calibrated_test) == 50
        # Monotonicity check for Platt sigmoid
        assert np.all(np.diff(calibrated_test) >= 0)

    def test_strict_avoidance_of_in_sample_leakage(self):
        """Validates that calibrating out-of-sample data prevents in-sample target leakage."""
        calibrator = ProbabilityCalibrator()
        # Train fold
        y_train = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        p_train = np.array([0.2, 0.3, 0.4, 0.45, 0.55, 0.6, 0.7, 0.8])
        calibrator.fit(y_train, p_train, method="isotonic")

        # Test fold (never seen during fitting)
        p_test = np.array([0.1, 0.5, 0.9])
        p_calibrated = calibrator.calibrate(p_test)
        assert len(p_calibrated) == 3
        assert p_calibrated[0] <= p_calibrated[1] <= p_calibrated[2]

    def test_compute_ece_uniform_and_quantile(self):
        calibrator = ProbabilityCalibrator()
        y_true = np.array([1, 0, 1, 0, 1, 1, 0, 0, 1, 0])
        y_prob = np.array([0.9, 0.1, 0.85, 0.15, 0.7, 0.6, 0.3, 0.2, 0.95, 0.05])

        ece_uniform = calibrator.compute_ece(y_true, y_prob, n_bins=5, strategy="uniform")
        ece_quantile = calibrator.compute_ece(y_true, y_prob, n_bins=5, strategy="quantile")

        assert isinstance(ece_uniform, float)
        assert isinstance(ece_quantile, float)
        assert 0.0 <= ece_uniform <= 1.0
        assert 0.0 <= ece_quantile <= 1.0

    def test_compute_ece_perfect_calibration(self):
        calibrator = ProbabilityCalibrator()
        y_true = np.array([1, 0, 1, 0])
        y_prob = np.array([1.0, 0.0, 1.0, 0.0])
        assert calibrator.compute_ece(y_true, y_prob) == 0.0

    def test_compute_brier_score(self):
        calibrator = ProbabilityCalibrator()
        y_true = np.array([1, 0, 1, 0])
        y_prob = np.array([0.8, 0.2, 0.9, 0.1])
        # (0.2^2 + 0.2^2 + 0.1^2 + 0.1^2) / 4 = (0.04 + 0.04 + 0.01 + 0.01) / 4 = 0.10 / 4 = 0.025
        brier = calibrator.compute_brier_score(y_true, y_prob)
        assert pytest.approx(brier, abs=1e-5) == 0.025

    def test_get_reliability_curve(self):
        calibrator = ProbabilityCalibrator()
        y_true = np.array([0, 0, 1, 1, 0, 1, 1, 1, 1, 1])
        y_prob = np.linspace(0.05, 0.95, 10)

        curve = calibrator.get_reliability_curve(y_true, y_prob, n_bins=5)
        assert "bins" in curve
        assert "mean_predicted" in curve
        assert "empirical_accuracy" in curve
        assert len(curve["bins"]) == 5
        assert len(curve["mean_predicted"]) == 5
        assert len(curve["empirical_accuracy"]) == 5
        assert sum(curve["counts"]) == 10


class TestEdgeCalculator:
    """Tests for EdgeCalculator and CandidateSelection."""

    def test_compute_ev(self):
        # 60% probability at 2.0 odds: EV = 0.60 * 2.0 - 1.0 = +0.20
        assert pytest.approx(EdgeCalculator.compute_ev(0.60, 2.0)) == 0.20
        # 40% probability at 2.0 odds: EV = 0.40 * 2.0 - 1.0 = -0.20
        assert pytest.approx(EdgeCalculator.compute_ev(0.40, 2.0)) == -0.20
        # Odds <= 1.0: EV should be -1.0
        assert EdgeCalculator.compute_ev(0.50, 1.0) == -1.0

    def test_compute_edge(self):
        p_calibrated = 0.54
        p_fair = 0.50
        assert pytest.approx(EdgeCalculator.compute_edge(p_calibrated, p_fair)) == 0.04

    def test_fractional_kelly_stake(self):
        # p = 0.55, odds = 2.0 -> raw Kelly = (0.55*2 - 1)/(2-1) = 0.10
        # quarter-Kelly = 0.10 * 0.25 = 0.025 (2.5%)
        f_star = EdgeCalculator.compute_fractional_kelly(0.55, 2.0, fraction=0.25)
        assert pytest.approx(f_star, abs=1e-5) == 0.025

    def test_fractional_kelly_bounds(self):
        # Negative EV -> 0.0 bound
        f_neg = EdgeCalculator.compute_fractional_kelly(0.40, 2.0)
        assert f_neg == 0.0

        # Massive edge -> capped at 0.05 (5% bankroll cap)
        f_large = EdgeCalculator.compute_fractional_kelly(0.95, 3.0)
        assert f_large == 0.05

    def test_evaluate_selection_candidate_dataclass(self):
        candidate = EdgeCalculator.evaluate_selection(
            match_id="match-abc",
            market="TOTAL_GOALS_2_5",
            selection="OVER",
            odds_1xbet=2.10,
            p_calibrated=0.55,
            p_fair_devigged=0.48,
            line=2.5,
            recommended_action="BET",
        )

        assert isinstance(candidate, CandidateSelection)
        assert candidate.match_id == "match-abc"
        assert candidate.market == "TOTAL_GOALS_2_5"
        assert pytest.approx(candidate.expected_value, abs=1e-4) == 0.155  # 0.55 * 2.10 - 1 = 0.155
        assert pytest.approx(candidate.value_edge, abs=1e-4) == 0.07       # 0.55 - 0.48 = 0.07
        assert candidate.flat_stake == 1.0
        assert candidate.fractional_kelly > 0.0
        assert candidate.ev == candidate.expected_value
        assert candidate.edge == candidate.value_edge


class TestNoBetGate:
    """Authoritative 10-Point NO-BET Gate Verification."""

    def setup_method(self):
        self.gate = NoBetGate()

    def test_gate_pass_all_checks(self):
        action, reasons = self.gate.evaluate(
            ev=0.06,
            edge=0.05,
            lineup_confirmed=True,
            home_starters_count=11,
            away_starters_count=11,
            odds_age_seconds=120,
            is_live=False,
            is_market_suspended=False,
            odds_available=True,
            monte_carlo_se=0.008,
            credible_interval_width=0.08,
            model_calibrated=True,
            historical_sample_size=400,
        )
        assert action == "BET"
        assert reasons == []

    def test_point_1_negative_ev(self):
        action, reasons = self.gate.evaluate(ev=-0.02, historical_sample_size=300)
        assert action == "NO_BET"
        assert "NEGATIVE_EV" in reasons

    def test_point_2_edge_below_threshold(self):
        action, reasons = self.gate.evaluate(ev=0.02, historical_sample_size=300)
        assert action == "NO_BET"
        assert "EDGE_BELOW_THRESHOLD" in reasons

    def test_point_3_lineup_unconfirmed(self):
        action, reasons = self.gate.evaluate(ev=0.05, lineup_confirmed=False, historical_sample_size=300)
        assert action == "NO_BET"
        assert "LINEUP_UNCONFIRMED" in reasons

        action2, reasons2 = self.gate.evaluate(
            ev=0.05, lineup_confirmed=True, home_starters_count=10, away_starters_count=11, historical_sample_size=300
        )
        assert action2 == "NO_BET"
        assert "LINEUP_UNCONFIRMED" in reasons2

    def test_point_4_odds_stale(self):
        # Pre-match odds > 15m (900s)
        action_pre, reasons_pre = self.gate.evaluate(
            ev=0.05, odds_age_seconds=950, is_live=False, historical_sample_size=300
        )
        assert "ODDS_STALE" in reasons_pre

        # Live odds > 60s
        action_live, reasons_live = self.gate.evaluate(
            ev=0.05, odds_age_seconds=75, is_live=True, historical_sample_size=300
        )
        assert "ODDS_STALE" in reasons_live

    def test_point_5_market_suspended(self):
        action, reasons = self.gate.evaluate(
            ev=0.05, is_market_suspended=True, historical_sample_size=300
        )
        assert "MARKET_SUSPENDED" in reasons

    def test_point_6_high_uncertainty(self):
        # MC SE > 0.02
        _, reasons_se = self.gate.evaluate(ev=0.05, monte_carlo_se=0.025, historical_sample_size=300)
        assert "HIGH_UNCERTAINTY" in reasons_se

        # Credible interval > 0.15
        _, reasons_ci = self.gate.evaluate(
            ev=0.05, prob_lower=0.40, prob_upper=0.60, historical_sample_size=300
        )
        assert "HIGH_UNCERTAINTY" in reasons_ci

    def test_point_7_model_uncalibrated(self):
        _, reasons = self.gate.evaluate(ev=0.05, model_calibrated=False, historical_sample_size=300)
        assert "MODEL_UNCALIBRATED" in reasons

    def test_point_8_source_conflict(self):
        _, reasons = self.gate.evaluate(ev=0.05, source_conflict=True, historical_sample_size=300)
        assert "SOURCE_CONFLICT" in reasons

    def test_point_9_player_minutes_uncertain(self):
        _, reasons = self.gate.evaluate(
            ev=0.05, player_minutes_uncertain=True, historical_sample_size=300
        )
        assert "PLAYER_MINUTES_UNCERTAIN" in reasons

    def test_point_10_insufficient_sample(self):
        _, reasons = self.gate.evaluate(ev=0.05, historical_sample_size=150)
        assert "INSUFFICIENT_SAMPLE" in reasons
