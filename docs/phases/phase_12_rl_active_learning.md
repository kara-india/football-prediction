# PHASE 12 — REINFORCEMENT LEARNING & CONTEXTUAL BANDIT POLICY

## 1. Goal
Implement an advanced, safe Reinforcement Learning (Contextual Bandit) policy layer that optimizes decision thresholds and market selection based on settled paper-bet outcomes. Learn whether abstention was optimal via counterfactual evaluation, evaluate policies using Inverse Propensity Scoring (IPS), and strictly enforce safety boundaries: the RL policy operates exclusively in `RESEARCH` mode until 1,000 verified paper bets have settled, and cannot bypass the fundamental lineup or negative EV gates.

## 2. Criticality
**P3 — ADVANCED RESEARCH** (Must never be activated until a large, statistically reliable evaluation ledger is established).

## 3. Prerequisites
- Phase 7 (Settlement & NO-BET), Phase 8 (Walk-forward backtest), and Phase 9 (Evaluator worker) completed.
- Minimum 500+ settled predictions logged in Supabase `prediction_results`.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 12.1 [Full Candidate Decision Dataset Logging]**: Create `python/rl/counterfactual_logger.py`:
  - When evaluating candidate bets, logs **all eligible candidate decision opportunities** (including `ABSTAIN` and rejected candidates) to prevent selection bias in the learning dataset.
  - For each opportunity, stores:
    - Context vector $X$: market, competition, team form, scoreline, odds, uncertainty/SE.
    - Probabilities: raw model probability, calibrated probability, probability interval.
    - Market metrics: 1xBet odds, devigged fair probability, EV, value edge.
    - Data quality tier and lineup verification state.
    - Available actions, chosen action, and action propensity $P(a \mid X)$ (required for off-policy evaluation).
    - Post-settlement: actual outcome, realized return, and counterfactual outcomes where valid.
- **Task 12.2 [Contextual Bandit Decision Layer & Subordination]**: Create `python/rl/bandit_policy.py`:
  - Implements a Contextual Bandit (LinUCB / Thompson Sampling) as a decision layer (action selection among `ABSTAIN` and market candidates), **not** as a replacement for the calibrated probability engine.
  - **Strict Statistical Subordination**: If any data safety gate fails (`LINEUP_UNCONFIRMED`, `ODDS_STALE`, `INSUFFICIENT_DATA`, `HIGH_UNCERTAINTY`), the action space is restricted strictly to $a = \text{ABSTAIN}$.
  - Controlled exploration: allows exploration in research/paper mode with recorded propensity scores while strictly adhering to safety gates.
  - Multi-objective reward: $\text{P\&L}_{\text{flat\_stake}} + \lambda \cdot \text{CLV} - \gamma \cdot \text{Uncertainty}$.
- **Task 12.3 [Offline Policy Evaluation Engine (OPE)]**: Create `python/rl/off_policy_evaluator.py`:
  - Evaluates candidate policies strictly offline using:
    - Doubly Robust (DR) estimation.
    - Inverse Propensity Scoring (IPS).
    - Temporal Replay backtesting (evaluating against unseen historical time folds).
    - Bootstrap confidence intervals for policy return and Sharpe ratio.
  - Rejects candidate policies unless out-of-sample improvement is statistically significant ($p < 0.05$).

### Sequential Tasks (Follows 12.1 - 12.3)
- **Task 12.4 [Research Mode Quarantine & Champion Gate]**: Enforce that the RL policy outputs decisions strictly to `research_predictions` table; production predictions remain driven by the validated champion statistical model until 1,000 verified paper bets have settled and OPE confirms out-of-sample superiority.
- **Task 12.5 [Safety Boundary Automated Tests]**: Verify that under simulated adversarial conditions, the bandit policy is physically prohibited from overriding the lineup gate or betting on negative EV markets.

## 5. Files / Modules Affected
- `python/rl/counterfactual_logger.py` [NEW]
- `python/rl/bandit_policy.py` [NEW]
- `python/rl/off_policy_evaluator.py` [NEW]
- `tests/test_bandit_policy.py` [NEW]

## 6. Database Changes
- Table: `rl_policy_runs` (id, policy_version, training_samples, mean_reward, ips_score, dr_score, parameters JSONB, created_at).
- Setting: `engine_settings.rl_enabled` (defaults to `false`).

## 7. Tests Required
- `tests/test_bandit_policy.py`:
  1. Test reward assignment accurately credits positive CLV and winning bets.
  2. Verify that bandit policy cannot execute BET on unconfirmed lineups under any parameter state.
  3. Verify off-policy evaluation rejects policies with high variance or negative expected return.

## 8. Acceptance Criteria
- [ ] Contextual bandit policy trains cleanly on historical paper bets.
- [ ] Off-policy evaluation proves policy value prior to any consideration of production use.
- [ ] Safety constraints cannot be violated by exploration parameters.
- [ ] System remains in `RESEARCH` mode until explicit user administrative activation.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Build counterfactual logger, bandit learner, and off-policy evaluator.
  2. Run `pytest tests/test_bandit_policy.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Inspect policy diagnostics after 1,000 matches have settled:
     ```powershell
     python -m python.rl.bandit_policy --evaluate
     ```
  2. To promote policy from research to production, execute in Supabase SQL Editor:
     ```sql
     UPDATE engine_settings SET rl_enabled = true WHERE id = 1;
     ```

## 11. Rollback Plan
- Instantly revert to pure statistical baseline by executing `UPDATE engine_settings SET rl_enabled = false WHERE id = 1;`.

## 12. Risks
- Policy overfitting to noisy short-term football outcomes. Mitigated by using Doubly Robust off-policy evaluation and conservative regularization.

## 13. What Must NOT Be Considered Complete
- Activating online reinforcement learning on live production predictions without an established, verified 1,000+ match paper bet history.
