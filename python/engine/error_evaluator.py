"""
Post-Settlement Error Evaluation and Taxonomy Engine
Decomposes forecast loss (Brier, Log-Loss, Calibration Residuals, Scoreline Error)
and classifies outcome errors into the authoritative 11-category causal taxonomy.
"""
from typing import Optional, Dict, Any, Tuple
import uuid
import numpy as np

from python.data_contracts import (
    CanonicalSettlement,
    CanonicalForecastError,
    ErrorCategory,
)


class ErrorEvaluator:
    """Post-settlement analytical decomposition and error taxonomy classifier."""

    @staticmethod
    def compute_brier_contribution(p: float, y: int) -> float:
        """Compute Brier Score contribution: (p - y)^2.

        Args:
            p: Forecast calibrated probability in [0.0, 1.0].
            y: Ground-truth binary outcome {0, 1}.

        Returns:
            Squared probability error.
        """
        return float((p - float(y)) ** 2)

    @staticmethod
    def compute_log_loss_contribution(p: float, y: int, eps: float = 1e-15) -> float:
        """Compute binary cross-entropy (Log-Loss) contribution.

        Formula: -(y * ln(p) + (1-y) * ln(1-p))
        """
        p_c = float(np.clip(p, eps, 1.0 - eps))
        return float(-(y * np.log(p_c) + (1.0 - y) * np.log(1.0 - p_c)))

    @staticmethod
    def compute_calibration_residual(p: float, empirical_rate: float) -> float:
        """Compute calibration residual: p - empirical_rate."""
        return float(p - empirical_rate)

    @staticmethod
    def compute_scoreline_error(
        predicted_home_goals: float,
        predicted_away_goals: float,
        actual_home_goals: int,
        actual_away_goals: int,
    ) -> int:
        """Compute absolute goal difference error: |(pred_H - pred_A) - (act_H - act_A)|."""
        pred_diff = predicted_home_goals - predicted_away_goals
        act_diff = float(actual_home_goals - actual_away_goals)
        return int(round(abs(pred_diff - act_diff)))

    @staticmethod
    def compute_ev_realization(profit_loss: float, expected_value: float) -> float:
        """Compute realized EV difference: profit_loss - expected_value."""
        return float(profit_loss - expected_value)

    @classmethod
    def classify_error(
        cls,
        settlement: CanonicalSettlement,
        p_calibrated: float,
        empirical_rate: float = 0.5,
        predicted_home_goals: Optional[float] = None,
        predicted_away_goals: Optional[float] = None,
        expected_value: float = 0.0,
        data_missing: bool = False,
        source_conflict: bool = False,
        odds_stale: bool = False,
        is_live: bool = False,
        live_state_error: bool = False,
        lineup_misassessment: bool = False,
        player_projection_error: bool = False,
        tactical_mismatch: bool = False,
        team_strength_miss: bool = False,
        parameter_drift: bool = False,
        calibration_error_threshold: float = 0.15,
        scoreline_error_threshold: int = 3,
        prediction_stage: str = "FINAL_PREMATCH",
    ) -> CanonicalForecastError:
        """Classify post-settlement failure into authoritative 11-category taxonomy.

        Categories:
        1. TEAM_STRENGTH_MISS
        2. LINEUP_MISASSESSMENT
        3. PLAYER_PROJECTION_ERROR
        4. TACTICAL_MISMATCH
        5. LIVE_STATE_ERROR
        6. ODDS_STALENESS
        7. SOURCE_CONFLICT
        8. DATA_MISSING
        9. CALIBRATION_ERROR
        10. PARAMETER_DRIFT
        11. RANDOM_VARIANCE
        """
        outcome_won = (settlement.actual_outcome == "WON")
        y = 1 if outcome_won else 0

        # Loss metrics
        brier = cls.compute_brier_contribution(p_calibrated, y)
        log_loss = cls.compute_log_loss_contribution(p_calibrated, y)
        cal_res = cls.compute_calibration_residual(p_calibrated, empirical_rate)
        ev_realized = cls.compute_ev_realization(settlement.profit_loss, expected_value)

        # Scoreline & goal metrics
        h_goals = settlement.actual_home_goals if settlement.actual_home_goals is not None else 0
        a_goals = settlement.actual_away_goals if settlement.actual_away_goals is not None else 0
        actual_total = h_goals + a_goals

        score_err = 0
        goal_res = None
        if predicted_home_goals is not None and predicted_away_goals is not None:
            score_err = cls.compute_scoreline_error(
                predicted_home_goals, predicted_away_goals, h_goals, a_goals
            )
            pred_total = predicted_home_goals + predicted_away_goals
            goal_res = float(pred_total - actual_total)

        # Hierarchical causal classification
        primary: ErrorCategory
        secondary: Optional[ErrorCategory] = None
        notes: str

        if data_missing:
            primary = ErrorCategory.DATA_MISSING
            notes = "Upstream match/player data streams were missing or truncated."
        elif source_conflict:
            primary = ErrorCategory.SOURCE_CONFLICT
            notes = "Discrepancy detected between independent upstream data providers."
        elif odds_stale:
            primary = ErrorCategory.ODDS_STALENESS
            notes = "Execution price was outdated relative to market movement."
        elif is_live and live_state_error:
            primary = ErrorCategory.LIVE_STATE_ERROR
            notes = "In-play simulation desynchronized from continuous live pitch state."
        elif lineup_misassessment:
            primary = ErrorCategory.LINEUP_MISASSESSMENT
            notes = "Unanticipated lineup omission or starter absence altered team projection."
        elif player_projection_error or settlement.market in ("ANYTIME_GOALSCORER", "PLAYER_PROPS"):
            primary = ErrorCategory.PLAYER_PROJECTION_ERROR
            notes = "Player-level minutes or conditional goal/card projection deviated from expectation."
        elif tactical_mismatch:
            primary = ErrorCategory.TACTICAL_MISMATCH
            notes = "Extreme tactical game-state divergence or stylistic mismatch."
        elif team_strength_miss or score_err >= scoreline_error_threshold:
            primary = ErrorCategory.TEAM_STRENGTH_MISS
            notes = f"Large goal difference residual ({score_err} goals); baseline team rating miss."
        elif parameter_drift:
            primary = ErrorCategory.PARAMETER_DRIFT
            notes = "Long-term model parameter decay or covariate shift detected."
        elif abs(cal_res) > calibration_error_threshold:
            primary = ErrorCategory.CALIBRATION_ERROR
            notes = f"Model probability residual |{cal_res:.3f}| exceeds threshold {calibration_error_threshold}."
        else:
            primary = ErrorCategory.RANDOM_VARIANCE
            notes = "Forecast well-specified and edge positive; result within expected sports variance."

        return CanonicalForecastError(
            error_id=str(uuid.uuid4()),
            prediction_id=settlement.prediction_id,
            match_id=settlement.match_id,
            brier_contribution=round(brier, 6),
            log_loss_contribution=round(log_loss, 6),
            calibration_residual=round(cal_res, 6),
            scoreline_error=score_err,
            ev_realization=round(ev_realized, 4),
            clv=settlement.clv,
            primary_category=primary,
            secondary_category=secondary,
            evidence_notes=notes,
            goal_count_residual=goal_res,
            prediction_stage=prediction_stage,
        )
