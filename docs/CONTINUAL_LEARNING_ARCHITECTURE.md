# CONTINUAL LEARNING, LINEUP-TRIGGERED INFERENCE & RL DECISION ARCHITECTURE
## Football Prediction Intelligence Platform — Core Lifecycle Specification

**Status**: AUTHORITATIVE SPECIFICATION  
**Applies To**: Phases 7, 8, 9, 10, 11, and 12  
**Core Principle**: Predict → Observe → Evaluate → Learn → Validate → Promote → Future Prediction

---

## 1. High-Level Architectural Lifecycle

The platform enforces a closed-loop, prequential (predict-then-update) intelligence lifecycle where historical data, real-time lineup arrivals, outcome settlement, error taxonomy, online adaptation, and reinforcement learning operate as a unified, decoupled background pipeline.

```text
                  BACKGROUND ENGINE
                        │
                        ▼
                Match / Data Collector
                        │
                        ▼
                 Canonical Data Layer
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       Initial Prediction    Lineup Monitor
       (Checkpoint A: T1)          │
                           Lineup Detected
                           (T-60m window)
                                   │
                                   ▼
                         Lineup-aware Prediction
                         (Checkpoint B: T2)
                                   │
             ┌─────────────────────┴────────────────────┐
             ▼                                          ▼
      Prediction Ledger                         Paper Decision Ledger
     (Immutable Snapshot)                      (All Eligible Candidates)
             │                                          │
             └──────────────────┬───────────────────────┘
                                ▼
                         Match Completion
                                │
                                ▼
                         Settlement / Result
                                │
                                ▼
                          Error Analysis
                     (Taxonomy Classification)
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
           Online Learning              RL / Bandit
           (Layer 2/3 Drift)         (Layer 4 Actions)
                  │                           │
                  └─────────────┬─────────────┘
                                ▼
                     Challenger Validation
                   (Temporal Holdout Test)
                                │
                                ▼
                       Controlled Promotion
                     (Champion vs Challenger)
                                │
                                ▼
                         Future Predictions
```

### 1.1 Non-Negotiable Invariants
1. **Engine-Browser Separation**: The browser **never** checks previous results, retrains models, or recalculates predictions. The browser is a pure read-only consumer of immutable persisted state. The background engine operates autonomously even if the user never opens the site.
2. **Every Eligible Match**: Every fixture in the allowlisted competition scope is predicted and recorded, regardless of whether the final decision is `BET` or `NO_BET`. Storing every decision opportunity prevents selection bias in downstream learning and offline policy evaluation.
3. **Immutable Prediction Snapshots**: When new information arrives (e.g., confirmed lineups), a *new* versioned checkpoint snapshot is created. Historical predictions are never mutated or overwritten.
4. **Predict-Then-Update Temporal Protocol**: At no point may the outcome of match $t$ alter prediction $t$. The outcome of match $t$ may only update the learning dataset and affect predictions for matches at $t+1$ or later ($available\_at \le prediction\_timestamp$).

---

## 2. Multi-Checkpoint Forecasting Lifecycle

A match progresses through distinct temporal forecasting checkpoints, each capturing the exact information available at that timestamp.

```text
Match enters horizon (T-48h)
      │
      ▼
[CHECKPOINT A: INITIAL]
      │
      ├─ Features: Elo ratings, multi-dimensional EWMA form, team strength, historical H2H
      ├─ Odds: Early 1xBet prices
      ├─ Output: Initial probabilities, initial EV, pre-lineup market status
      │
      ▼
Lineup Window approaches (T-60m to T-45m)
      │
      ▼
Lineup Announced & Verified (11 vs 11)
      │
      ▼
[CHECKPOINT B: LINEUP_CONFIRMED]
      │
      ├─ Features: Actual starting XI, confirmed bench, tactical formation, starter xG/90, late absences
      ├─ Odds: Reconciled 1xBet pre-kickoff prices
      ├─ Engine: Full model re-run, recalibration, 10k-path vectorized Monte Carlo
      ├─ Output: Final pre-match probabilities, Lineup Information Delta, final EV, NO-BET gate
      │
      ▼
Late Lineup Revision (if injury in warm-up)
      │
      ▼
[CHECKPOINT B2: LINEUP_V2] (Immutable revision snapshot if starting XI changes)
      │
      ▼
Kickoff (T=0)
      │
      ▼
[CHECKPOINT C: LIVE_INPLAY] (Dynamic in-play state snapshots triggered by match events)
      │
      ▼
Full-Time Whistle (FT)
      │
      ▼
Settlement & Learning Loop
```

### 2.1 Checkpoint Stage Definitions
- `INITIAL`: Generated 24–48 hours before kickoff. Models expected team rosters based on recent appearances and injury lists.
- `LINEUP_CONFIRMED` (`LINEUP_V1`): Generated immediately upon receipt and validation of official 11 vs 11 team sheets (~60m before kickoff).
- `LINEUP_V2` (Optional): Generated if an official pre-match lineup amendment occurs (e.g., warm-up injury).
- `FINAL_PREMATCH`: Generated at T-5m incorporating closing odds and final line movements.
- `LIVE`: Generated during live play at milestone events or regular minute intervals.

---

## 3. Lineup Event as a First-Class System Event

Lineup arrival is not a passive data field; it is an active system trigger that executes a deterministic recalculation pipeline.

```text
LINEUP_NOT_FOUND
        ↓
LINEUP_DETECTED (API-Football fixture lineup payload received)
        ↓
LINEUP_VALIDATED (Strict 11 vs 11 starter check, senior men's gate)
        ↓
LINEUP_CHANGED (Diff against previous expected roster or V1 lineup)
        ↓
LINEUP_FEATURES_REBUILT (Starter-specific attacking/defensive ratings, missing minutes)
        ↓
MODEL_RECALCULATED (Dixon-Coles & statistical attack/defense multipliers adjusted)
        ↓
CALIBRATION_APPLIED (Out-of-sample isotonic / Platt probability adjustment)
        ↓
SIMULATION_EXECUTED (Vectorized Monte Carlo competing hazard re-simulation)
        ↓
ODDS_RECONCILED (1xBet fresh line fetched & devigged via Shin method)
        ↓
EV_CALCULATED (Model probability vs fair market price edge)
        ↓
NO_BET_GATE (10-point safety and data freshness check)
        ↓
PREDICTION_SNAPSHOT_STORED (Persisted immutably to model_predictions table)
```

### 3.1 Lineup Information Value (LIV) Metric
For every match with confirmed lineups, the platform persists and evaluates the empirical information value added by lineups:

$$\Delta p = p_{\text{lineup}} - p_{\text{initial}}$$
$$\Delta o = o_{\text{market, lineup}} - o_{\text{market, initial}}$$

The evaluation engine computes:
- $\text{Brier}_{\text{initial}}$ vs $\text{Brier}_{\text{lineup}}$
- $\text{LogLoss}_{\text{initial}}$ vs $\text{LogLoss}_{\text{lineup}}$
- $\text{CLV}_{\text{initial}}$ vs $\text{CLV}_{\text{lineup}}$
- Calibration reliability curves separated by checkpoint stage.

This answers the fundamental research question: *Does confirmed starting XI data quantitatively improve forecast accuracy, and in which competitions/markets is the signal strongest?*

---

## 4. Quota-Aware Targeted Lineup Polling

To preserve the ₹0 external cost guarantee (capped at 95 API-Football requests/day, with 45 allocated to background workers):

1. **Zero Early Polling**: No lineup polling is executed $> 75\text{m}$ before kickoff.
2. **Targeted Window**: Matches inside the prediction horizon entering the $[T-60\text{m}, T-40\text{m}]$ window are polled in prioritized batches.
3. **Immediate Termination**: As soon as official 11 vs 11 starters are validated for both teams, polling for that fixture terminates permanently.
4. **Fallback Handling**: If lineups are unconfirmed at $T-15\text{m}$, polling ceases, and the match is assigned `NO_BET` with reason code `LINEUP_UNCONFIRMED`.

---

## 5. Layered Learning Architecture

Rather than monolithic and uncontrolled retraining of the entire model suite, continual learning is partitioned into four distinct architectural layers with escalating validation requirements.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: CONTEXTUAL BANDIT / RL DECISION POLICY                             │
│ • Action Selection: ABSTAIN, PAPER_BET_1X2, PAPER_BET_OU, PAPER_BET_BTTS    │
│ • Staking Policy: Fractional Kelly with uncertainty shrinkage               │
│ • Constraint: STRICTLY SUBORDINATE to Layer 1-3 NO-BET gates                │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 3: ONLINE RESIDUAL & DRIFT CORRECTION                                 │
│ • Moving team-strength adjustments & tactical style drift                   │
│ • Fast EWMA adaptation with Ridge/L2 shrinkage toward baseline              │
│ • Market residual tracking (closing line deviation tracking)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 2: PROBABILITY CALIBRATION & UNCERTAINTY MONITORING                   │
│ • Continuous Brier score, Log-Loss, and ECE tracking                        │
│ • Dynamic temperature scaling and isotonic binning updates                  │
│ • Challenger calibration validation on rolling 100-match window             │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 1: BASE FORECASTING MODELS                                            │
│ • Bivariate Poisson / Dixon-Coles solver with time decay xi                 │
│ • Dynamic Elo rating system & Multi-dimensional EWMA form                   │
│ • Negative Binomial count distributions (cards, corners)                    │
│ • Scheduled retraining across 5-year historical partitions                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Hard Safety Rule: RL Subordination
Reinforcement Learning / Contextual Bandits **never** override statistical or data-safety gates. If any gate fails (`LINEUP_UNCONFIRMED`, `ODDS_STALE`, `MARGIN_EXCESSIVE`, `HIGH_UNCERTAINTY`), the system forces `ABSTAIN` / `NO_BET` regardless of RL action value.

---

## 6. Outcome Settlement, Error Taxonomy & Learning Dataset

Immediately upon match completion, the background Evaluator worker settles predictions and classifies forecast errors.

### 6.1 Recorded Outcomes
- `actual_home_goals`, `actual_away_goals`, `actual_total_goals`
- `actual_cards_home`, `actual_cards_away`, `actual_corners`
- `result_1x2` (`HOME_WIN`, `DRAW`, `AWAY_WIN`)
- `result_over_under_25` (`OVER`, `UNDER`)
- `result_btts` (`YES`, `NO`)

### 6.2 Error Taxonomy Classification
Every settled prediction is audited and classified into standard causal categories:
1. `TEAM_STRENGTH_MISS`: Core Dixon-Coles / Elo rating misestimated team baseline.
2. `LINEUP_MISASSESSMENT`: Unanticipated bench rotation or key player position shift.
3. `PLAYER_PROJECTION_ERROR`: Key striker or goalkeeper underperformed expected goals.
4. `TACTICAL_MISMATCH`: High-press vs low-block clash generated anomalous game state.
5. `LIVE_STATE_ERROR`: Early red card or penalty skewed baseline match hazard.
6. `ODDS_STALENESS`: Market moved significantly after prediction generation.
7. `SOURCE_CONFLICT`: Discrepancy between provider team sheet and actual formation.
8. `DATA_MISSING`: Incomplete player minutes or historical records.
9. `CALIBRATION_ERROR`: Systemic overconfidence in high-probability bracket.
10. `PARAMETER_DRIFT`: League-wide goal scoring rate shifted away from historical mean.
11. `RANDOM_VARIANCE`: Match outcome within normal Poisson/binomial probability bounds.

### 6.3 Full Candidate Logging (RL Dataset)
To support unbiased offline policy evaluation, the learning ledger records **all decision opportunities**:
- Features and context at decision time.
- Model probabilities and calibrated probability intervals.
- 1xBet odds, devigged fair probability, EV, and edge.
- Data quality flags and lineup state.
- Available actions and chosen action.
- Action propensity $P(\text{action} \mid \text{context})$.
- Actual realized outcome and counterfactual returns.

---

## 7. Controlled Champion / Challenger Promotion Protocol

Production models are protected by a strict promotion gate. No autonomous online update may silently become the production Champion without passing temporal out-of-sample criteria.

```text
New Historical / Live Batch
            │
            ▼
Challenger Model Trained
            │
            ▼
Temporal Walk-Forward Validation (Preceding 6 Months Holdout)
            │
            ▼
Multi-Criteria Evaluation vs Champion:
  [ ] Sample size >= 250 matches
  [ ] Out-of-sample Brier score improvement (> 0.005)
  [ ] Log-Loss non-degradation
  [ ] Expected Calibration Error (ECE) <= 0.035
  [ ] Positive Closing Line Value (CLV > +1.5%)
  [ ] Max Drawdown <= Champion Drawdown
  [ ] Market coverage stability
            │
      ┌─────┴─────┐
      │           │
   Passed       Failed
      │           │
      ▼           ▼
Promote to    Retain in
CHAMPION      CHALLENGER
(Log git_sha) (Audit logs)
```

---

## 8. Summary of Implementation Milestones

- **Phase 7**: Market Settlement & Edge Engine (Closing odds devigging, true edge derivation, Kelly staking, settlement recorder, error taxonomy classifier).
- **Phase 8**: Walk-Forward Historical Validation (Historical lineup-aware replay, temporal no-lookahead verification, Lineup Information Value audit).
- **Phase 9**: Background Worker Automation (Autonomous targeted lineup watcher, event-triggered recomputation, settlement evaluator, online learner runner).
- **Phase 10**: Production Hardening & Observability (Drift monitoring, champion/challenger observability, quota alerts).
- **Phase 11**: Sofascore Terminal UI (Multi-checkpoint visualization, pre/post lineup probability delta, Model Improvement Dashboard).
- **Phase 12**: Contextual Bandit & Offline Policy Evaluation (Doubly Robust / IPS offline evaluation, multi-candidate decision logging, safety-subordinated RL policy).
