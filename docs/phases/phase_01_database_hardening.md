# PHASE 1 — DATABASE & MIGRATION HARDENING

## 1. Goal
Reconcile the migration baseline between Git migration files and the live Supabase PostgreSQL 17 database, enforce strict Row Level Security (RLS) policies to protect prediction and learning IP, and create necessary B-tree indexes for foreign keys to ensure sub-millisecond analytical query performance.

## 2. Criticality
**P0 — STOP-THE-LINE** (Must be completed before core data ingestion and worker execution).

## 3. Prerequisites
- Phase 0 completed (credentials scrubbed, Python environment reproducible).
- Supabase Project URL (`https://qqcxjjkgvqknesrtnwal.supabase.co`) and service role key accessible.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 1.1 [Schema Audit & Drift Detection]**: Run a Python script against `information_schema` and `pg_catalog` to compare existing database tables and columns against `supabase/migrations/001_initial_schema.sql` through `004_historical_matches.sql`.
- **Task 1.2 [RLS Policy Hardening]**: Draft `supabase/migrations/005_rls_hardening.sql`:
  - Enforce read-only access for `anon` / `authenticated` roles on public fixture data (`matches`, `competitions`, `odds_snapshots`).
  - Completely revoke client-side INSERT/UPDATE/DELETE on sensitive tables (`model_predictions`, `paper_bets`, `paper_bet_settlements`, `learning_runs`, `engine_settings`, `provider_usage`).
- **Task 1.3 [Foreign Key & Query Indexing]**: Identify unindexed foreign keys flagged by Supabase performance advisor and add B-tree indexes for:
  - `matches(competition_id)`, `matches(home_team_id)`, `matches(away_team_id)`, `matches(kickoff_utc)`
  - `lineups(match_id)`, `lineups(player_id)`
  - `match_events(match_id)`
  - `odds_snapshots(match_id, canonical_market, source_timestamp)`
  - `model_predictions(match_id, market)`
  - `paper_bets(prediction_id, status)`

### Sequential Tasks (Follows 1.1 - 1.3)
- **Task 1.4 [Migration Application & Verification]**: Apply the SQL migration via Supabase and verify with an automated test suite.
- **Task 1.5 [RLS Negative Testing]**: Verify that an anonymous Supabase client cannot insert or mutate predictions or paper bets.

## 5. Files / Modules Affected
- `supabase/migrations/000_baseline_reconciliation.sql` [NEW]
- `supabase/migrations/005_rls_and_indexing_hardening.sql` [NEW]
- `src/lib/supabase/client.ts`
- `src/lib/supabase/server.ts`
- `tests/test_database_schema.py` [NEW]

## 6. Database Changes
- Add baseline tracking table: `CREATE TABLE IF NOT EXISTS public.schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT NOW());`.
- Update RLS policies across all 27 tables.
- Add foreign key and analytical query indexes.

## 7. Tests Required
- `tests/test_database_schema.py`: Connects with both anon key and service role key to test:
  1. Anon read succeeds on `matches`.
  2. Anon insert fails on `model_predictions` (raises RLS permission denied).
  3. Service role insert succeeds on `model_predictions`.
  4. Verify all foreign key indexes exist in `pg_indexes`.

## 8. Acceptance Criteria
- [ ] Schema drift between git migrations and Supabase is documented and resolved.
- [ ] No anonymous or browser client can create or modify rows in `model_predictions` or `paper_bets`.
- [ ] All foreign keys have corresponding B-tree indexes in PostgreSQL.
- [ ] Automated database test suite passes with zero errors.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Generate SQL migration files (`000_baseline_reconciliation.sql` and `005_rls_and_indexing_hardening.sql`).
  2. Write automated test suite `tests/test_database_schema.py`.
  3. Execute verification script using service role and anon keys.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Open Supabase Dashboard $\to$ **SQL Editor**.
  2. Paste contents of `supabase/migrations/005_rls_and_indexing_hardening.sql` and click **Run**.
  3. Confirm query execution returns "Success. No rows returned".

## 11. Rollback Plan
- If query execution fails or breaks client reads, execute `DROP POLICY` and re-apply permissive read policies from migration backup.

## 12. Risks
- Restricting RLS could break existing Next.js frontend pages if server routes accidentally used the client-side anonymous Supabase client instead of the service role client. Ensure all write APIs use `src/lib/supabase/server.ts`.

## 13. What Must NOT Be Considered Complete
- Deleting indexes blindly without checking query plans.
- Leaving `FOR ALL USING (true)` on any prediction, bet, or worker state table.
