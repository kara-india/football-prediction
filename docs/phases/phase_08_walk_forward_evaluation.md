# PHASE 8 — WALK-FORWARD VALIDATION & REPLAY BACKTESTER

## 1. Goal
Build a mathematically authentic historical replay backtester and walk-forward validation framework. Completely excise fake placeholder metrics (`brier: 0.1`, `log_loss: 0.2`, hardcoded `winner: challenger`) from `walk_forward.py`. Enforce strict point-in-time state reconstruction ($\text{available\_at} \le T$), generate real out-of-sample performance metrics (Brier, Log Loss, ECE, ROI, CLV, Max Drawdown), and establish an objective champion/challenger comparison engine.

## 2. Criticality
**P0 — STOP-THE-LINE** (Required to scientifically prove model predictive edge before risking capital or deploying production workers).

## 3. Prerequisites
- Phase 3 (Historical matches), Phase 6 (Statistical models), and Phase 7 (Calibration & Settlement) completed.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 8.1 [Point-in-Time Feature Reconstructor]**: Create `python/backtesting/point_in_time_replayer.py`:
  - Reconstructs exact database and feature state as of any historical timestamp $T$.
  - Enforces the **No-Lookahead Invariant**:
    $$\forall \text{ entity } e \in \text{State}(T): \quad e.\text{available\_at} \le T$$
  - Excludes any match result, goal, card, or injury occurring at or after $T$.
- **Task 8.2 [Walk-Forward Temporal Splitter]**: Rewrite `python/backtesting/walk_forward.py`:
  - Implements sliding or expanding temporal folds:
    - Fold $k$: Train on $[T_0, T_1]$ (e.g., 24 months), Calibrate on $[T_1, T_2]$ (e.g., 3 months), Evaluate out-of-sample on $[T_2, T_3]$ (e.g., 1 month).
    - Advances window by step $\Delta = 1\text{ month}$.
  - Fits model on training fold, calibrates on validation fold, generates predictions on test fold.
  - Settles predictions against historical match outcomes.
- **Task 8.3 [Authentic Metric Computation & LIV Engine]**: Create `python/backtesting/metrics_engine.py`:
  - Computes empirical out-of-sample metrics:
    - Multi-class and binary Brier Score: $\text{BS} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$.
    - Logarithmic Loss: $-\frac{1}{N} \sum [y_i \ln p_i + (1-y_i) \ln(1-p_i)]$.
    - Expected Calibration Error (ECE) across 10 equal-frequency bins.
    - Flat 1.0 unit staking ROI: $\frac{\text{Net Profit}}{\sum \text{Stakes}}$.
    - Closing Line Value (CLV): $\frac{o_{\text{prediction}}}{o_{\text{closing}}} - 1.0$.
    - Maximum Drawdown in units.
  - **Lineup Information Value (LIV) Evaluation**:
    - Pre-lineup vs post-lineup Brier score delta ($\text{LIV}_{\text{Brier}}$).
    - Pre-lineup vs post-lineup Log-Loss delta ($\text{LIV}_{\text{LogLoss}}$).
    - Market probability movement vs model probability movement after lineup release.
    - Segmented by competition, market, and favorite/underdog status.
  - Zero hard-coded values permitted.
- **Task 8.4 [Historical Lineup-Aware Replay & Prequential Runner]**:
  - Replays historical match timelines using exact production feature code:
    $\text{T-48h Initial} \to \text{T-60m Confirmed XI} \to \text{Lineup Prediction} \to \text{Kickoff} \to \text{FT Settlement} \to \text{Error Analysis}$.
  - Strict prequential protocol: predict $(t) \to$ observe outcome $(t) \to$ update learner $\to$ predict $(t+1)$.
  - If exact lineup publication timestamp is unverified, marks `lineup_availability_timestamp_quality = "UNKNOWN"` to prevent subtle temporal leakage.
- **Task 8.5 [Champion / Challenger Comparison]**: Create `python/backtesting/model_comparator.py`:
  - Runs paired Diebold-Mariano and Wilcoxon signed-rank tests to assess statistical significance of Brier score improvements.
  - Requires challenger to achieve lower Brier score, positive CLV, and stable ECE across multiple folds before recommending promotion.

### Sequential Tasks (Follows 8.1 - 8.5)
- **Task 8.6 [Strict No-Lookahead Replay Test Suite]**: Execute automated tests asserting that:
  - Lineups become visible strictly at or after verified publication timestamp.
  - Post-match player stats are completely inaccessible to pre-match features.
  - Final odds are inaccessible to earlier prediction checkpoints.
  - Injected future events (e.g. 80' red card) produce 0.0000 alteration in 20' predictions.
- **Task 8.7 [3-Year Historical Replay Execution]**: Run a 36-month walk-forward backtest on the top 5 European leagues and log performance reports and LIV metrics to Supabase `model_metrics`.

## 5. Files / Modules Affected
- `python/backtesting/walk_forward.py`
- `python/backtesting/point_in_time_replayer.py` [NEW]
- `python/backtesting/metrics_engine.py` [NEW]
- `python/backtesting/model_comparator.py` [NEW]
- `tests/test_walk_forward.py` [NEW]
- `tests/test_no_lookahead.py` [NEW]

## 6. Database Changes
- Populate `model_metrics`: `model_version`, `dataset_version`, `market`, `fold_index`, `brier_score`, `log_loss`, `ece`, `roi`, `clv`, `sample_size`, `drawdown`.

## 7. Tests Required
- `tests/test_no_lookahead.py`:
  1. Test that match records after timestamp $T$ are strictly invisible to feature generation.
  2. Test that player transfers occurring after $T$ are not reflected in historical team rosters.
- `tests/test_walk_forward.py`:
  1. Test that zero metrics are static constants.
  2. Verify that random noise model produces Brier score $> 0.25$ and negative ROI.
  3. Verify that model comparison identifies superior model on synthetic biased test data.

## 8. Acceptance Criteria
- [x] Hardcoded placeholder metrics (`brier: 0.1`, `winner: challenger`) completely excised.
- [x] No-lookahead invariant mathematically verified via unit tests.
- [x] Walk-forward evaluation runs across multiple temporal folds producing genuine empirical metrics.
- [x] Champion vs challenger comparison requires statistically significant improvement ($p < 0.05$) for promotion recommendation.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Implement walk-forward framework and metrics engine.
  2. Run `pytest tests/test_no_lookahead.py tests/test_walk_forward.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Execute full historical backtest from terminal:
     ```powershell
     python -m python.backtesting.walk_forward --run-full-backtest --leagues EPL,LaLiga,Bundesliga
     ```
  2. Review the printed out-of-sample metric summary (Brier, ECE, ROI, CLV).

## 11. Rollback Plan
- Revert backtest scripts to previous commit; baseline metrics in database remain unaffected.

## 12. Risks
- Compute time for historical parameter fitting over 36 folds. Mitigated by parallelizing fold execution using Python `multiprocessing` across CPU cores.

## 13. What Must NOT Be Considered Complete
- Any evaluation returning fixed mock constants.
- Any backtest evaluating models on data that overlapped with training or parameter estimation.
