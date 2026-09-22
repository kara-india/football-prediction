# PHASE 2 — QUOTA GOVERNANCE & COST SAFETY

## 1. Goal
Establish a single, authoritative, atomic quota management system inside PostgreSQL to strictly enforce the **₹0.00 external data cost** mandate. Completely eliminate fragmented local cache quota trackers (`.cache/api_quota.json`, `request_budget.json`, Python in-memory counters) and ensure that neither automated workers nor user refreshes can exceed the 100 free requests/day limit.

## 2. Criticality
**P0 — STOP-THE-LINE** (Must be active before running any live match ingestion or worker automation).

## 3. Prerequisites
- Phase 1 completed (database hardened, RLS enforced).
- Supabase SQL access to install stored functions.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 2.1 [Database Quota Governor Function]**: Create `supabase/migrations/006_quota_governance.sql`:
  - Table: `provider_usage` tracking `provider`, `date_utc`, `user_requests_made`, `worker_requests_made`, `daily_limit` (95), `user_reserve` (50), `worker_budget` (45), `safety_buffer` (5).
  - PL/pgSQL function: `reserve_api_quota(p_provider TEXT, p_cost INT, p_is_user BOOLEAN)`:
    - Atomically locks the daily quota row using `FOR UPDATE`.
    - If `p_is_user == TRUE`: verifies `user_requests_made + p_cost <= user_reserve`.
    - If `p_is_user == FALSE`: verifies `worker_requests_made + p_cost <= worker_budget`.
    - Returns JSON: `{"allowed": true, "remaining_user": X, "remaining_worker": Y}` or raises exception if exceeded.
- **Task 2.2 [TypeScript Quota Client Rewrite]**: Rewrite `src/lib/quotaGuard.ts`:
  - Remove all filesystem calls (`fs.readFileSync`, `.cache/api_quota.json`).
  - Invoke `supabase.rpc('reserve_api_quota', ...)` using the server Supabase client.
  - Return clear UI message if user budget is exhausted: "Daily live refresh quota reached. Resets at 00:00 UTC."
- **Task 2.3 [Python Central Quota Adapter]**: Update `python/adapters/quota_manager.py`:
  - Deprecate local `request_budget.json`.
  - Connect to Supabase to call `reserve_api_quota` before every API-Football HTTP request.
  - If rejected, worker gracefully abstains without throwing an unhandled exception.

### Sequential Tasks (Follows 2.1 - 2.3)
- **Task 2.4 [End-to-End Stress Test]**: Concurrently launch 10 parallel reservation attempts in Python and TypeScript to verify atomic row locking without race conditions or negative balances.
- **Task 2.5 [Purge Local Quota Artifacts]**: Delete `.cache/api_quota.json` and remove `.cache` references from codebase.

## 5. Files / Modules Affected
- `supabase/migrations/006_quota_governance.sql` [NEW]
- `src/lib/quotaGuard.ts`
- `src/app/api/matches/live/route.ts`
- `src/app/api/matches/upcoming/route.ts`
- `python/adapters/quota_manager.py`
- `python/adapters/api_football.py`
- `tests/test_quota_governance.py` [NEW]

## 6. Database Changes
- Migration `006_quota_governance.sql` creates function `reserve_api_quota` and enhances `provider_usage` table.

## 7. Tests Required
- `tests/test_quota_governance.py`:
  1. Test sequential reservation up to 45 worker requests; 46th request must be rejected.
  2. Test sequential reservation up to 50 user requests; 51st request must be rejected.
  3. Test concurrency: 20 simultaneous threads requesting 1 credit each; verify count increases by exactly 20.
  4. Test midnight UTC reset logic.

## 8. Acceptance Criteria
- [ ] Strictly zero filesystem quota files remain in the repository.
- [ ] Atomic reservations prevent race conditions between Next.js server actions and background workers.
- [ ] Hard stop at 95 total daily requests; 5 requests strictly held in reserve as an emergency buffer.
- [ ] Zero possibility of incurring billed overages from external API providers.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Generate SQL migration `006_quota_governance.sql`.
  2. Rewrite `src/lib/quotaGuard.ts` and `python/adapters/quota_manager.py`.
  3. Delete `.cache/api_quota.json`.
  4. Run concurrency test suite `tests/test_quota_governance.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. In Supabase SQL Editor, run `supabase/migrations/006_quota_governance.sql`.
  2. Confirm function creation by running `SELECT * FROM pg_proc WHERE proname = 'reserve_api_quota';`.

## 11. Rollback Plan
- Revert stored procedure changes and restore read-only quota tracking in case of deadlock.

## 12. Risks
- Database latency: if network to Supabase is slow, API reservation adds ~50ms overhead per call. This is completely acceptable given we make at most ~50 calls per day.

## 13. What Must NOT Be Considered Complete
- Any system where Next.js reads from `.cache` while Python reads from memory or Supabase.
- Any quota tracker that allows requests past 95 on the same UTC day.
