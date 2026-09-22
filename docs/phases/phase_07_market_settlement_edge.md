# PHASE 7 — MARKET SETTLEMENT, CALIBRATION & NO-BET EDGE ENGINE

## 1. Goal
Implement the end-to-end decision engine starting with the First Vertical Slice (**Over/Under 2.5 Goals**). Establish rigorous out-of-sample probability calibration (Isotonic and Platt scaling), compute true mathematical Expected Value ($\text{EV}$) against 1xBet prices, enforce the comprehensive 10-point **NO-BET Gate**, record immutable predictions to `model_predictions`, and implement automated market settlement against verified match results.

## 2. Criticality
**P1 — HIGH** (Connects statistical model distributions directly to betting intelligence and decision making).

## 3. Prerequisites
- Phase 4 (1xBet odds engine) and Phase 6 (Statistical models & Monte Carlo) completed.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 7.1 [Out-of-Sample Calibration Engine]**: Rewrite `python/calibration/calibrator.py`:
  - Enforce strict temporal fold separation: train base model on Fold 1, calibrate on Fold 2, evaluate on Fold 3. Never calibrate on training data.
  - Implement Isotonic Regression and Platt (Logistic) scaling.
  - Compute calibration quality diagnostics: Expected Calibration Error (ECE), Brier Score, and 10-bin reliability curves.
  - Version calibration models in Supabase `calibration_versions`.
- **Task 7.2 [Expected Value & Edge Engine]**: Create `python/engine/edge_calculator.py`:
  - Calculate raw model probability $p_{\text{raw}}$ and calibrated probability $p_{\text{calibrated}}$.
  - Compute expected value: $\text{EV} = p_{\text{calibrated}} \cdot o_{1\text{xbet}} - 1.0$.
  - Calculate informational Fractional Kelly stake ($f^* = \frac{p \cdot o - 1}{o - 1} \cdot 0.25$). Flat 1.0 unit staking is used for all paper evaluation; Kelly is advisory.
- **Task 7.3 [Authoritative 10-Point NO-BET Gate]**: Create `python/engine/nobet_gate.py`:
  - Evaluates every candidate selection against the standard taxonomy:
    1. `NEGATIVE_EV`: $\text{EV} \le 0.0$.
    2. `EDGE_BELOW_THRESHOLD`: $\text{EV} < 0.03$ (minimum 3% edge configuration).
    3. `LINEUP_UNCONFIRMED`: Official starting XI not verified.
    4. `ODDS_STALE`: 1xBet price timestamp $> 15\text{m}$ old (pre-match) or $> 60\text{s}$ (live).
    5. `MARKET_SUSPENDED`: 1xBet line locked or inactive.
    6. `HIGH_UNCERTAINTY`: Monte Carlo standard error $> 0.02$ or credible interval width $> 0.15$.
    7. `MODEL_UNCALIBRATED`: Regime sample size insufficient for reliable calibration.
    8. `SOURCE_CONFLICT`: Discordance between live state feeds.
    9. `PLAYER_MINUTES_UNCERTAIN`: Player not confirmed starter (for player markets).
    10. `INSUFFICIENT_SAMPLE`: Historical sample size $< 200$ matches for competition.
  - If any condition trips, sets `recommended_action = "NO_BET"` and attaches failure codes.
- **Task 7.4 [Market Settlement Engine]**: Create `python/engine/settlement.py`:
  - Validates full-time scores and settles markets:
    - `TOTAL_GOALS_2_5`: WON if $(\text{home\_goals} + \text{away\_goals} > 2.5)$, else LOST.
    - `MATCH_1X2`: Home win, Draw, Away win.
    - `BTTS`: Yes if both $> 0$, else No.
    - `DOUBLE_CHANCE`: 1X, 12, X2.
  - Computes P&L on 1.0 unit stake and logs closing line value (CLV).

### Sequential Tasks (Follows 7.1 - 7.4)
- **Task 7.5 [First Vertical Slice End-to-End Test]**: Execute complete pipeline on historical fixture:
  Data $\to$ Dixon-Coles $\to$ Monte Carlo $\to$ Calibration $\to$ 1xBet EV $\to$ NO-BET Gate $\to$ Prediction Record $\to$ Settlement.
- **Task 7.6 [Ledger Immutability Test]**: Confirm that prediction rows in Supabase cannot be altered once written except for settlement fields.

## 5. Files / Modules Affected
- `python/calibration/calibrator.py`
- `python/engine/edge_calculator.py` [NEW]
- `python/engine/nobet_gate.py` [NEW]
- `python/engine/settlement.py` [NEW]
- `tests/test_calibration_and_edge.py` [NEW]
- `tests/test_settlement.py` [NEW]

## 6. Database Changes
- Table constraints: `model_predictions` has check constraint on `recommended_action IN ('BET', 'NO_BET')`.
- Table: `paper_bets` linked via foreign key to `model_predictions(id)`.

## 7. Tests Required
- `tests/test_calibration_and_edge.py`:
  1. Test ECE calculation on synthetic perfectly calibrated vs miscalibrated forecasts.
  2. Verify that selection with $p = 0.55$, $o = 1.80$ ($\text{EV} = -0.01$) trips `NEGATIVE_EV`.
  3. Verify that selection with $p = 0.55$, $o = 1.90$ ($\text{EV} = +0.045$) passes edge gate if lineups confirmed.
  4. Verify that unconfirmed lineup forces `NO_BET` even with positive EV.
- `tests/test_settlement.py`:
  1. Test settlement for 2-1 result: Over 2.5 WON, Home WON, BTTS WON.
  2. Test settlement for 2-0 result: Under 2.5 WON, BTTS LOST.

## 8. Acceptance Criteria
- [ ] Over/Under 2.5 vertical slice runs end-to-end with zero errors.
- [ ] Calibration reduces Brier score and improves ECE on holdout sets.
- [ ] NO-BET gate strictly rejects all negative EV and unconfirmed lineup matches.
- [ ] Settled paper bets compute exact flat-stake P&L and Closing Line Value (CLV).

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Build calibration, edge, NO-BET, and settlement modules.
  2. Run `pytest tests/test_calibration_and_edge.py tests/test_settlement.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Run a sample prediction and settlement run from terminal:
     ```powershell
     python -m python.engine.edge_calculator --test-fixture
     ```
  2. Confirm output JSON displays calibrated probability, EV, and attached NO-BET reasons.

## 11. Rollback Plan
- Revert edge calculator logic to reject all bets (`default_action = 'NO_BET'`) if unexpected errors occur.

## 12. Risks
- Overconfidence in small sample regimes. Prevented by rule #10 of the NO-BET gate (`INSUFFICIENT_SAMPLE`).

## 13. What Must NOT Be Considered Complete
- Any system that produces betting recommendations without checking the 10 NO-BET criteria.
- Fitting calibration models on the same data used to fit Dixon-Coles parameters.
