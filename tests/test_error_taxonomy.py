"""
Tests for Error Taxonomy Classification and Analytical Decomposition
Validates Brier contribution, Log-Loss contribution, calibration residual, scoreline error,
EV realization, and the authoritative 11-category error taxonomy classification.
"""
import pytest
import numpy as np

from python.data_contracts import CanonicalSettlement, ErrorCategory, CanonicalForecastError
from python.engine.error_evaluator import ErrorEvaluator


class TestErrorDecomposition:
    """Verifies exact mathematical loss and error decomposition formulas."""

    def test_brier_contribution(self):
        # p = 0.70, outcome = WON (y = 1) -> (0.70 - 1.0)^2 = 0.09
        assert pytest.approx(ErrorEvaluator.compute_brier_contribution(0.70, 1)) == 0.09
        # p = 0.70, outcome = LOST (y = 0) -> (0.70 - 0.0)^2 = 0.49
        assert pytest.approx(ErrorEvaluator.compute_brier_contribution(0.70, 0)) == 0.49

    def test_log_loss_contribution(self):
        # p = 0.80, y = 1 -> -ln(0.80)
        expected_won = -np.log(0.80)
        assert pytest.approx(ErrorEvaluator.compute_log_loss_contribution(0.80, 1), abs=1e-5) == expected_won

        # p = 0.80, y = 0 -> -ln(1 - 0.80) = -ln(0.20)
        expected_lost = -np.log(0.20)
        assert pytest.approx(ErrorEvaluator.compute_log_loss_contribution(0.80, 0), abs=1e-5) == expected_lost

    def test_calibration_residual(self):
        # Model prob 0.65, empirical base rate in bucket 0.45 -> residual = +0.20
        assert pytest.approx(ErrorEvaluator.compute_calibration_residual(0.65, 0.45)) == 0.20

    def test_scoreline_error(self):
        # Pred: 2.1 H - 0.9 A (diff = +1.2). Actual: 0 H - 2 A (diff = -2.0)
        # Goal difference error = |1.2 - (-2.0)| = 3.2 -> rounded to 3
        err = ErrorEvaluator.compute_scoreline_error(2.1, 0.9, 0, 2)
        assert err == 3

        # Exact match
        assert ErrorEvaluator.compute_scoreline_error(2.0, 1.0, 2, 1) == 0

    def test_ev_realization(self):
        # Lost bet (-1.0 unit) with expected value +0.08 -> realization = -1.08
        realization = ErrorEvaluator.compute_ev_realization(-1.0, 0.08)
        assert pytest.approx(realization) == -1.08


class TestAuthoritative11CategoryTaxonomy:
    """Verifies that all 11 error taxonomy categories are diagnosed and assigned properly."""

    def _create_sample_settlement(self, actual_outcome="LOST", h_goals=0, a_goals=2, market="MATCH_1X2"):
        from datetime import datetime, timezone
        return CanonicalSettlement(
            prediction_id="pred-tax-1",
            match_id="match-tax-1",
            market=market,
            selection="1",
            odds_at_prediction=2.10,
            actual_outcome=actual_outcome,
            profit_loss=-1.0 if actual_outcome == "LOST" else 1.10,
            settled_at=datetime.now(timezone.utc),
            closing_odds=2.00,
            clv=0.05,
            actual_home_goals=h_goals,
            actual_away_goals=a_goals,
        )

    def test_category_1_team_strength_miss(self):
        settle = self._create_sample_settlement(h_goals=0, a_goals=4)
        # Predicted home blowout 3.0 - 0.5 (diff +2.5), actual 0 - 4 (diff -4.0) -> scoreline error 7
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.75,
            predicted_home_goals=3.0,
            predicted_away_goals=0.5,
        )
        assert err.primary_category == ErrorCategory.TEAM_STRENGTH_MISS
        assert err.scoreline_error >= 3

    def test_category_2_lineup_misassessment(self):
        settle = self._create_sample_settlement()
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.55,
            lineup_misassessment=True,
        )
        assert err.primary_category == ErrorCategory.LINEUP_MISASSESSMENT

    def test_category_3_player_projection_error(self):
        settle = self._create_sample_settlement(market="ANYTIME_GOALSCORER")
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.45,
            player_projection_error=True,
        )
        assert err.primary_category == ErrorCategory.PLAYER_PROJECTION_ERROR

    def test_category_4_tactical_mismatch(self):
        settle = self._create_sample_settlement()
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.55,
            tactical_mismatch=True,
        )
        assert err.primary_category == ErrorCategory.TACTICAL_MISMATCH

    def test_category_5_live_state_error(self):
        settle = self._create_sample_settlement()
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.60,
            is_live=True,
            live_state_error=True,
        )
        assert err.primary_category == ErrorCategory.LIVE_STATE_ERROR

    def test_category_6_odds_staleness(self):
        settle = self._create_sample_settlement()
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.55,
            odds_stale=True,
        )
        assert err.primary_category == ErrorCategory.ODDS_STALENESS

    def test_category_7_source_conflict(self):
        settle = self._create_sample_settlement()
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.55,
            source_conflict=True,
        )
        assert err.primary_category == ErrorCategory.SOURCE_CONFLICT

    def test_category_8_data_missing(self):
        settle = self._create_sample_settlement()
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.55,
            data_missing=True,
        )
        assert err.primary_category == ErrorCategory.DATA_MISSING

    def test_category_9_calibration_error(self):
        settle = self._create_sample_settlement(h_goals=1, a_goals=1)
        # Predicted difference close to actual, no operational issues, but large calibration residual
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.75,
            empirical_rate=0.45,  # residual = 0.30 > threshold 0.15
            predicted_home_goals=1.2,
            predicted_away_goals=1.0,
        )
        assert err.primary_category == ErrorCategory.CALIBRATION_ERROR

    def test_category_10_parameter_drift(self):
        settle = self._create_sample_settlement(h_goals=1, a_goals=1)
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.52,
            empirical_rate=0.50,
            predicted_home_goals=1.2,
            predicted_away_goals=1.0,
            parameter_drift=True,
        )
        assert err.primary_category == ErrorCategory.PARAMETER_DRIFT

    def test_category_11_random_variance(self):
        settle = self._create_sample_settlement(h_goals=1, a_goals=1)
        # Tight prediction, small scoreline error, small calibration residual, no operational issues
        err = ErrorEvaluator.classify_error(
            settlement=settle,
            p_calibrated=0.53,
            empirical_rate=0.51,  # residual 0.02
            predicted_home_goals=1.4,
            predicted_away_goals=1.1,
            expected_value=0.06,
        )
        assert err.primary_category == ErrorCategory.RANDOM_VARIANCE
        assert isinstance(err, CanonicalForecastError)
        assert err.brier_contribution > 0
        assert err.log_loss_contribution > 0
