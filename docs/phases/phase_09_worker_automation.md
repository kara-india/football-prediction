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
- **Task 9.2 [Live State & Odds Worker]**: Create `python/workers/live_state_worker.py`:
  - Runs during active match windows.
  - Tracks live scores, elapsed minutes, and match events.
  - Dispatches targeted deep calls only when a high-impact event (goal, red card) is detected.
  - Snapshots live 1xBet market lines.
- **Task 9.3 [Prediction Runner Worker]**: Create `python/workers/analysis_worker.py`:
  - Selects eligible fixtures with verified lineups ($T-60\text{m}$ to $T-5\text{m}$).
  - Executes feature pipeline, Dixon-Coles estimation, vectorized Monte Carlo, and calibration.
  - Evaluates EV against 1xBet odds and executes NO-BET gate.
  - Inserts predictions into `model_predictions` and logs candidates to `paper_bets`.
- **Task 9.4 [Evaluator & Error Classification Worker]**: Rewrite `python/workers/evaluator_worker.py`:
  - Runs every 30 minutes to check matches with status `FT` (Full Time).
  - Finds all unsettled predictions for finished matches.
  - Computes settlement outcome (`WON`, `LOST`, `VOID`, `PUSH`), P&L, and Closing Line Value (CLV).
  - Classifies errors into standard taxonomy (`MODEL_OVERCONFIDENCE`, `BAD_SCORE_STATE`, `RED_CARD_EFFECT`, `RANDOM_VARIANCE`, `ODDS_MOVEMENT`).
  - Writes records to Supabase `prediction_results` and `prediction_errors`.
- **Task 9.5 [Unified CLI Orchestrator]**: Create `python/workers/runner.py`:
  - Dispatches CLI commands: `python -m python.workers.runner <job_name> [--dry-run]`.
  - Wraps execution in atomic database logging (`worker_runs` table: `worker_name`, `started_at`, `finished_at`, `status`, `items_processed`, `api_requests_made`, `error_message`).
  - Enforces execution mutex: prevents overlapping executions of the same worker type.

### Sequential Tasks (Follows 9.1 - 9.5)
- **Task 9.6 [GitHub Actions Scheduled Workflow]**: Create `.github/workflows/worker_cron.yml`:
  - Triggers discovery worker daily and analysis worker hourly during weekend match windows.
  - Injects `SUPABASE_SERVICE_ROLE_KEY` and `API_FOOTBALL_KEY` securely from repository secrets.
- **Task 9.7 [Worker Idempotency Test]**: Run evaluator worker twice consecutively on the same match results; assert that zero duplicate settlements or double payouts are recorded.

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
- [ ] Empty `pass` statements completely removed from all worker files.
- [ ] Workers execute cleanly from terminal via `python -m python.workers.runner <job>`.
- [ ] Evaluator worker automatically settles bets and logs error taxonomy upon match completion.
- [ ] Worker execution history logged to Supabase `worker_runs`.

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
