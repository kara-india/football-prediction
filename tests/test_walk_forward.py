"""
Automated Test Suite for Walk-Forward Validation, Metrics Engine & Model Comparator
Verifies mathematical correctness of Brier, Log Loss, ECE, ROI, CLV, Max Drawdown,
LIV Engine, Diebold-Mariano tests, and objective promotion gates.
"""
from datetime import date, datetime, timezone
import numpy as np
import pandas as pd
import pytest

from python.backtesting.walk_forward import WalkForwardValidator
from python.backtesting.metrics_engine import (
    MetricsEngine,
    LineupInformationValueEngine,
    BacktestMetricsSummary,
)
from python.backtesting.model_comparator import ModelComparator, ComparisonResult


# =====================================================================
# 1. TEMPORAL FOLD GENERATION & ZERO OVERLAP
# =====================================================================

def test_fold_generation_no_overlap_sliding():
    """Verify sliding temporal folds have zero window overlap between train and test."""
    wf = WalkForwardValidator(
        initial_train_months=12,
        calibration_months=3,
        test_months=1,
        step_months=1,
        mode="sliding",
    )
    start_date = date(2021, 1, 1)
    end_date = date(2023, 1, 1)

    folds = wf.generate_folds(pd.DataFrame(), start_date, end_date)
    assert len(folds) > 0

    for i, fold in enumerate(folds):
        assert fold["train_start"] < fold["train_end"]
        assert fold["train_end"] <= fold["cal_start"]
        assert fold["cal_start"] < fold["cal_end"]
        assert fold["cal_end"] <= fold["test_start"]
        assert fold["test_start"] < fold["test_end"]
        assert fold["test_end"] <= end_date

        if i > 0:
            prev = folds[i - 1]
            # In sliding mode, train_start advances
            assert fold["train_start"] > prev["train_start"]
            assert fold["test_start"] > prev["test_start"]


def test_fold_generation_expanding():
    """Verify expanding temporal folds keep train_start anchored at start_date."""
    wf = WalkForwardValidator(
        initial_train_months=12,
        calibration_months=2,
        test_months=1,
        step_months=1,
        mode="expanding",
    )
    start_date = date(2020, 1, 1)
    end_date = date(2021, 8, 1)

    folds = wf.generate_folds(pd.DataFrame(), start_date, end_date)
    assert len(folds) >= 4

    for fold in folds:
        assert fold["train_start"] == start_date
        assert fold["cal_start"] == fold["train_end"]
        assert fold["test_start"] == fold["cal_end"]


# =====================================================================
# 2. DETERMINISTIC EMPIRICAL METRICS EVALUATION
# =====================================================================

def test_brier_score_binary_deterministic():
    """Binary Brier Score matches exact manual computation."""
    engine = MetricsEngine()
    y_true = np.array([1, 0, 1, 1])
    y_prob = np.array([0.8, 0.2, 0.6, 0.9])
    # Diff: [-0.2, 0.2, -0.4, -0.1]
    # Squared: [0.04, 0.04, 0.16, 0.01] -> Sum = 0.25 -> Mean = 0.0625
    bs = engine.brier_score(y_true, y_prob)
    assert pytest.approx(bs, abs=1e-6) == 0.0625


def test_brier_score_multiclass_deterministic():
    """Multi-class Brier Score matches exact manual computation."""
    engine = MetricsEngine()
    y_true = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ])
    y_prob = np.array([
        [0.7, 0.2, 0.1],
        [0.1, 0.8, 0.1],
    ])
    # Obs 1: (0.7-1)^2 + 0.2^2 + 0.1^2 = 0.09 + 0.04 + 0.01 = 0.14
    # Obs 2: 0.1^2 + (0.8-1)^2 + 0.1^2 = 0.01 + 0.04 + 0.01 = 0.06
    # Mean across 2 obs: (0.14 + 0.06) / 2 = 0.10
    bs = engine.brier_score(y_true, y_prob)
    assert pytest.approx(bs, abs=1e-6) == 0.10


def test_log_loss_deterministic():
    """Binary Log-Loss matches exact negative log-likelihood."""
    engine = MetricsEngine()
    y_true = np.array([1, 0])
    y_prob = np.array([0.8, 0.2])
    # -1/2 * (1*ln(0.8) + (1-0)*ln(1-0.2)) = -ln(0.8) = ~0.22314355
    expected = -np.log(0.8)
    ll = engine.log_loss(y_true, y_prob)
    assert pytest.approx(ll, abs=1e-6) == expected


def test_ece_deterministic():
    """Expected Calibration Error across uniform bins."""
    engine = MetricsEngine()
    # Perfectly calibrated case: prob 0.7 has 70% positive rate, prob 0.2 has 20%
    y_true = np.array([1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    y_prob = np.array([0.7] * 10 + [0.2] * 10)
    # Bin 1 (0.2): acc = 2/10 = 0.2, pred = 0.2, diff = 0.0
    # Bin 2 (0.7): acc = 7/10 = 0.7, pred = 0.7, diff = 0.0
    ece = engine.expected_calibration_error(y_true, y_prob, n_bins=10)
    assert pytest.approx(ece, abs=1e-6) == 0.0


def test_roi_and_drawdown_deterministic():
    """Flat 1.0 unit staking ROI and Maximum Drawdown computation."""
    engine = MetricsEngine()
    pnl = [1.0, -1.0, -1.0, 2.0]
    # Sum PnL = 1.0, Total stake = 4.0 -> ROI = 0.25 (25%)
    roi = engine.flat_staking_roi(pnl)
    assert pytest.approx(roi, abs=1e-6) == 0.25

    # Bankroll starting at 100:
    # After +1.0: 101.0 (Peak: 101.0, DD: 0.0)
    # After -1.0: 100.0 (Peak: 101.0, DD: 1.0)
    # After -1.0: 99.0  (Peak: 101.0, DD: 2.0)
    # After +2.0: 101.0 (Peak: 101.0, DD: 0.0)
    dd = engine.maximum_drawdown(pnl, initial_bankroll=100.0)
    assert pytest.approx(dd["max_drawdown_units"], abs=1e-6) == 2.0
    assert pytest.approx(dd["max_drawdown_pct"], abs=1e-4) == (2.0 / 101.0)


def test_clv_deterministic():
    """Closing Line Value (CLV) matches o_pred / o_close - 1.0."""
    engine = MetricsEngine()
    odds_pred = [2.20, 1.80]
    odds_close = [2.00, 2.00]
    # (2.20 / 2.00 - 1) = +0.10, (1.80 / 2.00 - 1) = -0.10
    clv = engine.closing_line_value(odds_pred, odds_close)
    assert pytest.approx(clv, abs=1e-6) == 0.0


# =====================================================================
# 3. LINEUP INFORMATION VALUE (LIV) ENGINE
# =====================================================================

def test_liv_engine_accuracy_improvement():
    """Confirmed lineups improving probability forecasts produce positive LIV deltas."""
    liv_engine = LineupInformationValueEngine()

    records = [
        {"outcome": 1, "p_pre": 0.50, "p_post": 0.80, "odds_pre": 2.0, "odds_post": 1.6, "competition": "EPL", "market": "1X2"},
        {"outcome": 0, "p_pre": 0.50, "p_post": 0.20, "odds_pre": 2.0, "odds_post": 2.6, "competition": "EPL", "market": "1X2"},
        {"outcome": 1, "p_pre": 0.50, "p_post": 0.75, "odds_pre": 2.0, "odds_post": 1.7, "competition": "LaLiga", "market": "1X2"},
        {"outcome": 0, "p_pre": 0.50, "p_post": 0.25, "odds_pre": 2.0, "odds_post": 2.5, "competition": "LaLiga", "market": "1X2"},
    ]

    report = liv_engine.evaluate_liv(records)

    # Post-lineup Brier score should be lower, meaning LIV_Brier is positive
    assert report.brier_post < report.brier_pre
    assert report.liv_brier > 0.0
    assert report.liv_log_loss > 0.0
    assert report.mean_abs_prob_delta > 0.20
    assert "EPL" in report.by_competition
    assert "LaLiga" in report.by_competition


# =====================================================================
# 4. RANDOM NOISE MODEL PENALTY
# =====================================================================

def test_random_noise_predictions_yield_high_brier_and_negative_roi():
    """Random noise predictions on competitive fixtures must yield Brier > 0.25 and negative ROI."""
    rng = np.random.default_rng(12345)
    N = 600

    # 50/50 competitive outcomes
    y_true = rng.binomial(1, 0.5, size=N)
    # Pure noise uninformative predictions
    noise_probs = rng.uniform(0.1, 0.9, size=N)

    # Bookmaker odds with 5% margin (fair 2.00 price priced at 1.90)
    market_odds = np.full(N, 1.90)

    engine = MetricsEngine()
    bs = engine.brier_score(y_true, noise_probs)
    # Expected Brier for uniform noise on 50/50 is E[(U - Y)^2] = 1/3 ~ 0.333 > 0.25
    assert bs > 0.25

    # Paper bets placed when noise prob >= 0.5
    pnl = []
    for y, p in zip(y_true, noise_probs):
        if p >= 0.5:
            pnl.append(0.90 if y == 1 else -1.0)

    roi = engine.flat_staking_roi(pnl)
    # ROI should be significantly negative due to 5% vig on noise
    assert roi < -0.02


# =====================================================================
# 5. DIEBOLD-MARIANO TEST & OBJECTIVE PROMOTION GATE
# =====================================================================

def test_diebold_mariano_identical_forecasts():
    """Identical models yield DM statistic 0.0 and p-value 1.0."""
    comparator = ModelComparator()
    losses = np.array([0.1, 0.2, 0.05, 0.3, 0.15] * 20)
    dm_stat, p_val, d_bar = comparator.diebold_mariano_test(losses, losses)
    assert pytest.approx(dm_stat, abs=1e-4) == 0.0
    assert pytest.approx(p_val, abs=1e-4) == 1.0
    assert pytest.approx(d_bar, abs=1e-4) == 0.0


def test_model_comparator_promotes_superior_challenger():
    """Challenger with statistically significant lower Brier, stable ECE, and positive CLV is PROMOTED."""
    rng = np.random.default_rng(42)
    N = 300

    x = rng.normal(0, 1, size=N)
    p_true = 1.0 / (1.0 + np.exp(-2.0 * x))
    y_true = (rng.uniform(0, 1, size=N) < p_true).astype(int)

    # Champion: overconfident model with poor calibration (ECE > 0.13)
    champ_probs = np.where(p_true > 0.5, 0.95, 0.05)

    # Challenger: well-calibrated posterior model with lower Brier and lower ECE
    chal_probs = p_true

    odds_pred = np.full(N, 2.05)
    odds_close = np.full(N, 2.00)  # +2.5% CLV

    comparator = ModelComparator(min_sample_size=100, significance_threshold=0.05)
    result = comparator.compare(
        y_true=y_true,
        prob_champion=champ_probs,
        prob_challenger=chal_probs,
        odds_prediction=odds_pred,
        odds_closing=odds_close,
    )

    assert result.recommendation == "PROMOTE"
    assert result.criteria_met["sample_size"] is True
    assert result.criteria_met["brier_reduction"] is True
    assert result.criteria_met["statistical_significance"] is True
    assert result.diebold_mariano_p_value < 0.05
    assert result.brier_reduction > 0.02


def test_model_comparator_rejects_inferior_challenger():
    """Challenger with higher Brier score is REJECTED."""
    rng = np.random.default_rng(999)
    N = 250
    y_true = rng.binomial(1, 0.50, size=N)

    # Champion is better than Challenger
    champ_probs = np.where(y_true == 1, 0.75, 0.25)
    chal_probs = rng.uniform(0.1, 0.9, size=N)

    comparator = ModelComparator(min_sample_size=100)
    result = comparator.compare(y_true, champ_probs, chal_probs)

    assert result.recommendation == "REJECT"
    assert result.criteria_met["brier_reduction"] is False


def test_model_comparator_insufficient_data():
    """Sample size below threshold returns INSUFFICIENT_DATA."""
    comparator = ModelComparator(min_sample_size=100)
    y_true = [1, 0, 1] * 10  # N = 30 < 100
    p_champ = [0.5] * 30
    p_chal = [0.6] * 30

    result = comparator.compare(y_true, p_champ, p_chal)
    assert result.recommendation == "INSUFFICIENT_DATA"
    assert result.criteria_met["sample_size"] is False


# =====================================================================
# 6. WALK-FORWARD VALIDATOR REAL METRIC VERIFICATION
# =====================================================================

def test_walk_forward_validator_real_metrics_no_mock():
    """WalkForwardValidator computes authentic empirical metrics across folds (no fake 0.1 constants)."""
    rng = np.random.default_rng(777)
    n_matches = 400
    dates = pd.date_range("2022-01-01", "2023-08-30", periods=n_matches)

    df = pd.DataFrame({
        "match_id": range(n_matches),
        "date": dates,
        "feature_1": rng.normal(0, 1, size=n_matches),
        "feature_2": rng.normal(0, 1, size=n_matches),
        "odds": rng.uniform(1.8, 2.2, size=n_matches),
    })
    # Target linked to feature_1
    prob = 1.0 / (1.0 + np.exp(-1.5 * df["feature_1"]))
    df["outcome"] = (rng.uniform(0, 1, size=n_matches) < prob).astype(int)

    validator = WalkForwardValidator(
        initial_train_months=6,
        calibration_months=2,
        test_months=1,
        step_months=1,
        calibration_method="platt",
    )

    from sklearn.linear_model import LogisticRegression

    results = validator.validate_model(
        model_factory=lambda: LogisticRegression(),
        features=df,
        target_col="outcome",
        date_col="date",
    )

    # Assert metrics are real numbers and NOT the old fake constants (brier=0.1, log_loss=0.2)
    assert results["mean_brier"] != 0.1
    assert results["mean_log_loss"] != 0.2
    assert results["mean_brier"] > 0.0
    assert results["mean_log_loss"] > 0.0
    assert results["mean_ece"] >= 0.0
    assert len(results["folds"]) > 0
    assert results["total_predictions"] > 0
