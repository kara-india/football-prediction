# PHASE 0 — REPOSITORY & SECURITY HARDENING

## 1. Goal
Remediate the critical P0 security exposure of leaked credentials, establish a reproducible and pinned Python environment, fix CI failure propagation, and reconcile the Supabase migration baseline so all subsequent development builds on a secure, deterministic foundation.

## 2. Criticality
**P0 — STOP-THE-LINE** (Must be completed before any model or worker execution).

## 3. Prerequisites
- Access to repository git command line.
- Access to Supabase Project Dashboard (`https://supabase.com/dashboard/project/qqcxjjkgvqknesrtnwal`).
- API-Football account to generate a new rotated API key.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 0.1 [Secrets Scrubbing]**: Remove exposed API key (`073534f7111a37868a403c5cd51d83fa`) from `README.md`, `src/app/api/matches/live/route.ts`, and `src/app/api/matches/upcoming/route.ts`. Replace with strict `process.env.API_FOOTBALL_KEY` (throw informative 500 error if missing, zero hard-coded fallback).
- **Task 0.2 [Python Dependency Pinning]**: Create `python/requirements.txt` containing pinned versions for `numpy`, `scipy`, `pandas`, `scikit-learn`, `python-dateutil`, `pydantic`, `fastapi`, `uvicorn`, `httpx`, `python-dotenv`, `supabase`, `pytest`, `pytest-asyncio`. Create `python/requirements-dev.txt` for linting (`ruff`, `mypy`).
- **Task 0.3 [CI Workflow Hardening]**: Update `.github/workflows/ci.yml`:
  - Remove error swallowing (`|| echo 'lint check done'`, `|| echo 'type check done'`).
  - Ensure failure on non-zero exit code for `tsc --noEmit`, `pytest`, and `npm run lint`.
  - Add Python dependency installation step with cache verification.

### Sequential Tasks (Must follow 0.1 - 0.3)
- **Task 0.4 [Supabase Migration Reconciliation]**:
  - Compare SQL in `supabase/migrations/` (001 through 004) against PostgreSQL 17 system catalog in production.
  - Establish `supabase_migrations` table tracking applied migrations to prevent replaying existing DDL.
  - Verify `SUPABASE_SERVICE_ROLE_KEY` is strictly absent from all client bundles (`src/app/`, `src/components/`, public env).
- **Task 0.5 [Verification & Smoke Test]**: Run clean install in isolated environment and verify zero leaked strings.

## 5. Files / Modules Affected
- `README.md`
- `src/app/api/matches/live/route.ts`
- `src/app/api/matches/upcoming/route.ts`
- `python/requirements.txt` [NEW]
- `python/requirements-dev.txt` [NEW]
- `.github/workflows/ci.yml`
- `supabase/migrations/000_reconcile_baseline.sql` [NEW]

## 6. Database Changes
- Establish migration tracking table `supabase_migrations` if not native.
- Audit RLS policies on sensitive tables: revoke public write access on `model_predictions`, `model_versions`, `paper_bets`, `learning_runs`.

## 7. Tests Required
- `tests/test_security_audit.py`: Scans git staging and repository files for regex matches of API keys, service role keys, and database passwords.
- `tests/test_environment_clean.py`: Verifies import of all required Python modules from clean virtual environment.

## 8. Acceptance Criteria
- [ ] No hardcoded API keys exist anywhere in source code or `README.md`.
- [ ] `pip install -r python/requirements.txt` succeeds from scratch in CI and locally.
- [ ] CI fails if lint or typecheck fails (no `|| echo 'done'`).
- [ ] Supabase schema is authoritative and matches Git migrations.
- [ ] RLS on Supabase blocks anonymous client INSERT/UPDATE on `model_predictions` and `paper_bets`.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Scrub hardcoded keys from all files.
  2. Create `python/requirements.txt` and `python/requirements-dev.txt`.
  3. Rewrite `.github/workflows/ci.yml` with strict error enforcement.
  4. Generate baseline migration reconciliation script.
  5. Run security audit test suite.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Log in to [API-Sports](https://dashboard.api-football.com) and **revoke/rotate** the exposed API key (`073534f7111a37868a403c5cd51d83fa`).
  2. Add new `API_FOOTBALL_KEY` to GitHub Repository Secrets (`Settings > Secrets > Actions`).
  3. Add `SUPABASE_SERVICE_ROLE_KEY` to GitHub Repository Secrets.
  4. Set `API_FOOTBALL_KEY` in local `.env.local` (ensure `.env.local` remains gitignored).

## 11. Rollback Plan
- If migration reconciliation encounters table lock, rollback via transaction `ROLLBACK;`.
- Git revert commit if CI workflow breaks repository checks.

## 12. Risks
- Secret rotation might temporarily disable live match fetching until the user updates GitHub secrets and local `.env.local`.

## 13. What Must NOT Be Considered Complete
- Merely removing the key from the latest commit while leaving it in `.env.example` or active in API-Sports without rotation.
- Generating a `requirements.txt` without testing a clean `pip install`.
