# PHASE 9 — BACKGROUND WORKER AUTOMATION & CLI ORCHESTRATION

## 1. Goal
Transform the stubbed background workers (`collector_worker.py`, `evaluator_worker.py`, `learner_worker.py` containing literal `pass` statements) into resilient, idempotent operational workers. Create a unified CLI runner (`python/workers/runner.py`) capable of executing discovery, live state tracking, odds snapshotting, prediction generation, post-match evaluation, and error analysis under strict quota constraints and database logging.

## 2. Criticality
**P2 — MEDIUM-HIGH** (Enables the platform to operate autonomously in the background without requiring active user sessions).

## 3. Prerequisites
- Phase 2 (Quota governance), Phase 5 (Lineup gate), Phase 7 (Settlement & NO-BET), and Phase 8 (Metrics) completed.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 9.1 [Discovery & Ingestion Worker]**: Rewrite `python/workers/collector_worker.py`:
  - Runs once daily at 04:00 UTC.
  - Discovers eligible fixtures for the next 48 hours.
  - Reserves exactly 1 API-Football credit.
  - Ingests upcoming fixtures into Supabase `matches`.
- **Task 9.2 [Quota-Aware Targeted Lineup Watcher]**: Create `python/workers/lineup_watcher.py`:
  - Monitors upcoming eligible fixtures approaching the $[T-60\text{m}, T-40\text{m}]$ kickoff window.
  - Zero polling $> 75\text{m}$ before kickoff to preserve the 45-call worker budget.
  - Upon detecting confirmed 11 vs 11 starting team sheets:
    - Sets `lineup_confirmed = True` and records `lineup_available_at`.
    - Halts further lineup polling for this fixture.
    - Immediately dispatches event-triggered analysis worker to generate `LINEUP_CONFIRMED` forecast.
  - If late starting XI changes occur, creates versioned `LINEUP_V2` snapshot.
- **Task 9.3 [Multi-Checkpoint Prediction Runner Worker]**: Create `python/workers/analysis_worker.py`:
  - Generates `INITIAL` forecast snapshot when fixture enters horizon ($T-48\text{h}$).
  - Executes event-driven recalculation immediately upon lineup arrival ($T-60\text{m}$):
    - Rebuilds starter-specific attack/defense ratings, expected minutes, and missing minutes.
    - Reruns Dixon-Coles, recalibrates, resimulates 10k Monte Carlo paths.
    - Reconciles 1xBet odds and evaluates NO-BET gate.
    - Computes and logs Lineup Information Value ($\Delta p, \Delta \text{odds}, \Delta \text{EV}$).
    - Inserts immutable `LINEUP_CONFIRMED` snapshot into `model_predictions`.
  - Runs for *every* eligible fixture in allowlist, even when `recommended_action = "NO_BET"`.
- **Task 9.4 [Evaluator & Error Classification Worker]**: Rewrite `python/workers/evaluator_worker.py`:
  - Runs every 30 minutes to check matches with status `FT` (Full Time).
  - Finds all unsettled predictions for finished matches across all stages (`INITIAL`, `LINEUP_CONFIRMED`, `LIVE`).
  - Computes settlement outcome (`WON`, `LOST`, `VOID`, `PUSH`), P&L, and Closing Line Value (CLV).
  - Classifies errors into standard 11-category taxonomy (`TEAM_STRENGTH_MISS`, `LINEUP_MISASSESSMENT`, `PLAYER_PROJECTION_ERROR`, `TACTICAL_MISMATCH`, `LIVE_STATE_ERROR`, `ODDS_STALENESS`, `SOURCE_CONFLICT`, `DATA_MISSING`, `CALIBRATION_ERROR`, `PARAMETER_DRIFT`, `RANDOM_VARIANCE`).
  - Writes records to Supabase `prediction_results` and `prediction_errors`.
- **Task 9.5 [Online Learner & Prequential Model Worker]**: Rewrite `python/workers/learner_worker.py`:
  - Reads settled results and error records from completed match batches.
  - Appends observations to canonical learning dataset and RL candidate ledger.
  - Updates Layer 3 online residuals (recent team-strength adjustments with L2 shrinkage).
  - Updates Layer 2 calibration monitoring (Brier score, ECE, reliability curves).
  - Trains challenger models and runs temporal out-of-sample validation vs Champion.
  - Enforces controlled promotion gate: requires minimum 250 matches, out-of-sample Brier improvement, positive CLV, and non-degraded calibration before promotion.
- **Task 9.6 [Unified CLI Orchestrator]**: Create `python/workers/runner.py`:
  - Dispatches CLI commands: `python -m python.workers.runner <job_name> [--dry-run]`.
  - Wraps execution in atomic database logging (`worker_runs` table: `worker_name`, `started_at`, `finished_at`, `status`, `items_processed`, `api_requests_made`, `error_message`).
  - Enforces execution mutex: prevents overlapping executions of the same worker type.

### Sequential Tasks (Follows 9.1 - 9.6)
- **Task 9.7 [GitHub Actions Scheduled Workflow]**: Create `.github/workflows/worker_cron.yml`:
  - Triggers discovery worker daily, lineup watcher during pre-match windows, and evaluator hourly.
  - Injects `SUPABASE_SERVICE_ROLE_KEY` and `API_FOOTBALL_KEY` securely from repository secrets.
- **Task 9.8 [Worker Idempotency & Prequential Integrity Test]**:
  - Run evaluator worker twice consecutively on the same match results; assert zero duplicate settlements.
  - Test prequential update invariant: assert outcome of match $t$ cannot alter prediction $t$ and only updates models for $t+1$ onwards.

## 5. Files / Modules Affected
- `python/workers/collector_worker.py`
- `python/workers/evaluator_worker.py`
- `python/workers/learner_worker.py`
- `python/workers/live_state_worker.py` [NEW]
- `python/workers/analysis_worker.py` [NEW]
- `python/workers/runner.py` [NEW]
- `.github/workflows/worker_cron.yml` [NEW]
- `tests/test_workers.py` [NEW]

## 6. Database Changes
- Table: `worker_runs` (id, worker_name, started_at, finished_at, status, matches_seen, matches_analyzed, api_requests, quota_remaining, predictions_count, errors_count, error_details).

## 7. Tests Required
- `tests/test_workers.py`:
  1. Test worker CLI dispatcher executes valid subcommands and fails gracefully on unknown commands.
  2. Test worker mutex prevents concurrent runs of the same worker.
  3. Verify `worker_runs` table logs start time, duration, and exit status.
  4. Test evaluator settlement idempotent execution on duplicate runs.

## 8. Acceptance Criteria
- [x] Empty `pass` statements completely removed from all worker files.
- [x] Workers execute cleanly from terminal via `python -m python.workers.runner <job>`.
- [x] Evaluator worker automatically settles bets and logs error taxonomy upon match completion.
- [x] Worker execution history logged to Supabase `worker_runs`.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Implement all workers and the unified CLI runner.
  2. Create GitHub Actions scheduled workflow `.github/workflows/worker_cron.yml`.
  3. Run `pytest tests/test_workers.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Trigger a manual dry run of the discovery worker:
     ```powershell
     python -m python.workers.runner discovery --dry-run
     ```
  2. Go to GitHub $\to$ **Actions** and enable the `worker_cron.yml` workflow.

## 11. Rollback Plan
- Disable `engine_settings.worker_enabled = false` in Supabase to instantly halt all worker background activity.

## 12. Risks
- GitHub Actions runner latency or cold start delays. Addressed by designing workers to be decoupled from GitHub Actions so they can run locally, on a VPS, or as a cron job.

## 13. What Must NOT Be Considered Complete
- Any worker that leaves exception handling unmanaged or fails to record quota consumption.
- Marking workers complete while methods remain empty stubs.
