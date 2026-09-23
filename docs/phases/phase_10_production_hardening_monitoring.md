# PHASE 10 — PRODUCTION HARDENING, MONITORING & RETENTION

## 1. Goal
Harden the production infrastructure against data growth, race conditions, and unmonitored failures. Establish database idempotency locks to eliminate duplicate predictions and odds records, implement automated data retention pruning to stay well within Supabase free-tier limits, and create an unauthenticated health check endpoint (`/api/engine/health`) that reports platform vitals without exposing internal security credentials.

## 2. Criticality
**P2 — MEDIUM** (Essential for long-term operational stability on free-tier infrastructure).

## 3. Prerequisites
- Phase 1 (Database), Phase 2 (Quota), and Phase 9 (Workers) completed.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 10.1 [Idempotency & Deduplication Engine]**: Create `python/storage/deduplicator.py`:
  - Enforces database upsert logic with unique natural keys:
    - Matches: `(provider, provider_fixture_id)`
    - Odds: `(match_id, bookmaker, canonical_market, selection, line, source_timestamp)`
    - Predictions: `(match_id, market, selection, line, prediction_timestamp)`
  - Utilizes PostgreSQL advisory locks during batch insertion to prevent race conditions.
- **Task 10.2 [Data Retention Pruner]**: Create `python/workers/retention_pruner.py`:
  - Pruning Policy:
    - Retain high-value analytical data indefinitely: `matches`, `lineups`, `odds_snapshots`, `model_predictions`, `paper_bets`, `model_metrics`.
    - Prune transient granular live tick data older than 14 days: `match_event_ticks`, raw provider response logs.
    - Prune completed `worker_runs` older than 30 days.
  - Executes as a weekly maintenance task to keep Supabase database storage below 500 MB.
- **Task 10.3 [Health Diagnostics Endpoint]**: Create `src/app/api/engine/health/route.ts`:
  - Checks Supabase database connectivity via lightweight ping (`SELECT 1`).
  - Reports current API quota status (daily requests consumed, remaining, reset time).
  - Reports status of latest worker runs from `worker_runs`.
  - Zero sensitive keys, tokens, or internal model algorithms returned in JSON response.

### Sequential Tasks (Follows 10.1 - 10.3)
- **Task 10.4 [Storage Audit & Stress Test]**: Simulate 1,000 duplicate prediction writes to verify zero table bloat or duplicate constraint violations.
- **Task 10.5 [Health Endpoint Verification]**: Hit `/api/engine/health` from browser and verify HTTP 200 with sanitized health metrics.

## 5. Files / Modules Affected
- `python/storage/deduplicator.py` [NEW]
- `python/workers/retention_pruner.py` [NEW]
- `src/app/api/engine/health/route.ts` [NEW]
- `tests/test_production_hardening.py` [NEW]

## 6. Database Changes
- Add retention cleanup stored procedure `prune_transient_logs(days_to_keep INT)`.

## 7. Tests Required
- `tests/test_production_hardening.py`:
  1. Test deduplication engine suppresses identical odds ticks within same minute.
  2. Verify retention pruner deletes rows older than 14 days while keeping predictions intact.
  3. Verify health endpoint returns 200 OK and contains no secret strings.

## 8. Acceptance Criteria
- [x] Database storage usage remains stabilized below Supabase 500 MB free quota limit.
- [x] Idempotency prevents duplicate predictions, bets, and settlements.
- [x] Health endpoint reports database status, remaining quota, and worker timestamps securely.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Build deduplicator, retention pruner, and health check route.
  2. Run `pytest tests/test_production_hardening.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Open browser to `http://localhost:3000/api/engine/health`.
  2. Confirm response JSON shows `status: "healthy"` and lists valid quota numbers.

## 11. Rollback Plan
- Revert retention script if accidental deletion of non-transient data occurs; restore from Supabase automated daily backup.

## 12. Risks
- Overly aggressive data pruning. Prevented by explicitly excluding `matches`, `model_predictions`, and `paper_bets` from the deletion query.

## 13. What Must NOT Be Considered Complete
- Any health check that exposes environment variables, database connection strings, or provider keys.
- Leaving live event snapshots to grow unbounded without retention policy.
