# DEPLOYMENT & MANUAL STEPS SPECIFICATION
# Football Prediction Intelligence Platform

This document defines the exact boundary between **Automated Actions by Claude** and **Mandatory Manual Actions by User** across all 13 development phases.

---

## Phase 0: Repository & Security Hardening

### Automated by Claude
1. Search and scrub all hardcoded occurrences of API key `073534f7111a37868a403c5cd51d83fa` across `README.md`, `src/app/api/matches/live/route.ts`, and `src/app/api/matches/upcoming/route.ts`.
2. Generate `python/requirements.txt` containing pinned versions:
   ```txt
   numpy==1.26.4
   scipy==1.13.1
   pandas==2.2.2
   scikit-learn==1.5.0
   python-dateutil==2.9.0.post0
   pydantic==2.7.4
   fastapi==0.111.0
   uvicorn==0.30.1
   httpx==0.27.0
   python-dotenv==1.0.1
   supabase==2.5.0
   pytest==8.2.2
   pytest-asyncio==0.23.7
   ```
3. Generate `python/requirements-dev.txt` with `ruff==0.4.9` and `mypy==1.10.0`.
4. Rewrite `.github/workflows/ci.yml` to remove `|| echo 'done'` and enforce strict error exit codes on `npm run lint`, `tsc --noEmit`, and `pytest`.
5. Run `tests/test_security_audit.py` to confirm zero active secrets in tracked code.

### Manual by User
1. **Rotate Leaked API Key**:
   - Go to [API-Sports Dashboard](https://dashboard.api-football.com/).
   - Navigate to **Account** $\to$ **API Keys**.
   - Revoke/Delete key `073534f7111a37868a403c5cd51d83fa`.
   - Generate a new free-tier API key.
2. **Update Local Environment**:
   - Open local `.env.local` in `c:\Users\Karan Jha\antigravity\scratch\football-prediction\.env.local`.
   - Update:
     ```env
     API_FOOTBALL_KEY=your_new_rotated_key_here
     ```
3. **Update GitHub Repository Secrets**:
   - Go to `https://github.com/kara-india/football-prediction/settings/secrets/actions`.
   - Add/Update Secret: `API_FOOTBALL_KEY` = `your_new_rotated_key_here`.
   - Add/Update Secret: `SUPABASE_SERVICE_ROLE_KEY` = `your_service_role_key`.

---

## Phase 1: Database & Migration Hardening

### Automated by Claude
1. Inspect live PostgreSQL 17 system catalog (`information_schema.tables`, `pg_indexes`, `pg_policies`).
2. Generate `supabase/migrations/000_baseline_reconciliation.sql` to formally record existing schema tables.
3. Generate `supabase/migrations/005_rls_and_indexing_hardening.sql`:
   - Revoke anonymous write access on `model_predictions`, `paper_bets`, `learning_runs`, `engine_settings`, `provider_usage`.
   - Add B-tree indexes for foreign keys: `matches(competition_id)`, `matches(home_team_id)`, `matches(away_team_id)`, `lineups(match_id)`, `odds_snapshots(match_id)`.
4. Create database validation test `tests/test_database_schema.py`.

### Manual by User
1. **Apply Migration via Supabase SQL Editor**:
   - Open Supabase SQL Editor: `https://supabase.com/dashboard/project/qqcxjjkgvqknesrtnwal/sql`.
   - Copy and paste contents of `supabase/migrations/005_rls_and_indexing_hardening.sql`.
   - Click **Run**.
2. **Verify RLS Enforcement**:
   - Verify that Anonymous read on `matches` returns 200 OK.
   - Verify that Anonymous INSERT into `model_predictions` returns 401 Unauthorized / RLS violation.

---

## Phase 2: Quota Governance & Cost Safety

### Automated by Claude
1. Create PostgreSQL stored function `reserve_api_quota(p_provider TEXT, p_cost INT, p_is_user BOOLEAN)` in `supabase/migrations/006_quota_governance.sql`.
2. Delete local `.cache/api_quota.json` and replace `src/lib/quotaGuard.ts` with Supabase-backed atomic reservation client.
3. Update `python/adapters/api_football.py` to route all external calls through `reserve_api_quota()`.
4. Add unit test `tests/test_quota_governance.py` validating that request #96 on the same UTC day is strictly rejected with `QuotaExceededError`.

### Manual by User
1. **Execute Quota Migration**:
   - Paste `supabase/migrations/006_quota_governance.sql` into Supabase SQL Editor and click **Run**.
2. **Inspect Initial Quota Row**:
   - Run query in Supabase SQL Editor:
     ```sql
     SELECT * FROM provider_usage WHERE provider = 'api-football';
     ```
   - Ensure `daily_requests_made` is set to current actual usage and `daily_limit` is set to 95.

---

## Phase 3: Zero-Cost Data Ingestion

### Automated by Claude
1. Build historical downloader script `python/ingestion/football_data_uk.py` to fetch past 5 seasons of match statistics (goals, shots, cards, corners, odds) for the 10 core European leagues.
2. Ingest into Supabase `historical_matches` and populate canonical `matches` table.
3. Implement `python/adapters/api_football.py:discover_fixtures()` utilizing 1 single bulk API call per 24 hours to fetch all daily fixtures across all leagues.
4. Implement data quality validator `python/ingestion/quality_scorer.py`.

### Manual by User
1. **Run Initial Data Ingestion**:
   - Run command in terminal:
     ```powershell
     python -m python.ingestion.football_data_uk --seasons 5
     ```
   - Verify script completes with 0 errors and confirms insertion into Supabase.

---

## Phase 4: Target Odds (1xBet) Engine

### Automated by Claude
1. Research and verify zero-cost 1xBet odds feeds (testing network reachability, rate limits, and market formats).
2. Implement `python/adapters/one_xbet_adapter.py`:
   - Real reachability check to 1xBet endpoint.
   - Parse canonical markets: `MATCH_1X2`, `TOTAL_GOALS` (1.5, 2.5, 3.5), `BTTS`.
   - Calculate de-vigged fair probabilities using shin or multiplicative margin removal.
   - If endpoint unreachable, return `OddsUnavailableException` (zero mocking).
3. Create snapshot writer to log odds to Supabase `odds_snapshots`.

### Manual by User
1. **Verify Connectivity**:
   - Run command in terminal:
     ```powershell
     python -m python.adapters.one_xbet_adapter --test-connection
     ```
   - Confirm whether 1xBet lines are reachable from your current IP or if proxy configuration is required.

---

## Phase 5: Lineup & Runtime Gatekeeper

### Automated by Claude
1. Build `python/workers/lineup_gatekeeper.py`:
   - Monitors matches scheduled within $T-60\text{ minutes}$.
   - Polls API-Football lineups endpoint (max 1 request per eligible match).
   - Validates official 11 starters per team and formation string.
   - Updates `matches.lineup_confirmed = true`.
2. Build competition allowlist filter enforcing only the 10 approved leagues + major tournaments.

### Manual by User
- No manual actions required. All operations automated via worker.

---

## Phase 6: Core Statistical Models & Monte Carlo

### Automated by Claude
1. **Overhaul Dixon-Coles (`python/models/dixon_coles.py`)**:
   - Enforce identifiability constraint: $\frac{1}{N}\sum \alpha_i = 1$.
   - Implement temporal decay optimization $\xi$.
   - Output exact bivariate Poisson score probabilities $P(X=x, Y=y)$.
2. **Dynamic Elo Rating (`python/models/elo.py`)**:
   - Re-rate all teams using 5-year historical data.
   - Calibrate K-factor and home ground advantage parameter.
3. **Multi-Dimensional Form (`python/models/form.py`)**:
   - Separate attacking, defensive, shot, and discipline EWMA components.
4. **Vectorized Monte Carlo (`python/simulation/vectorized_mc.py`)**:
   - In-play competing hazard simulator for goals, cards, and corners.
   - Calculate mathematical standard error: $\text{SE} = \sqrt{\frac{p(1-p)}{N}}$.
   - Halt simulations when $\text{SE} \le 0.005$ or cap at 50,000 runs.

### Manual by User
1. **Fit Base Model Parameters**:
   - Run offline parameter estimation:
     ```powershell
     python -m python.models.dixon_coles --fit --save-to-db
     ```
   - Verify fitted parameters are written to Supabase `model_versions`.

---

## Phase 7: Market Settlement & Edge Engine

### Automated by Claude
1. Implement First Vertical Slice: **Over/Under 2.5 Goals**.
2. Build Calibration Module (`python/calibration/calibrator.py`):
   - Out-of-sample Isotonic Regression and Platt scaling.
   - Compute Expected Calibration Error (ECE) and Brier Score.
3. Implement Expected Value Engine: $\text{EV} = p_{\text{calibrated}} \cdot \text{Odds}_{1\text{xbet}} - 1.0$.
4. Implement 10-point standard **NO-BET Gate**:
   - Reject if $\text{EV} < 0.03$, lineup unconfirmed, odds stale ($>15\text{m}$), or high MC uncertainty.
5. Create immutable writer to Supabase `model_predictions`.

### Manual by User
1. **Inspect First Generated Prediction**:
   - Run vertical slice predictor:
     ```powershell
     python -m python.engine.predict --market TOTAL_GOALS_2_5 --test
     ```
   - Inspect output JSON in terminal to confirm calibrated probability, 1xBet price, EV, and NO-BET status.

---

## Phase 8: Walk-Forward Validation & Backtester

### Automated by Claude
1. Build `python/backtesting/walk_forward.py`:
   - Temporal sliding window (24 months train, 3 months validation, 1 month step).
   - Strict point-in-time feature reconstruction ($\text{available\_at} \le T$).
   - Compute true empirical Brier Score, Log Loss, ECE, ROI, and Closing Line Value (CLV).
   - Completely purge hardcoded placeholder metrics (`brier: 0.1`).
2. Implement model comparison test suite comparing Dixon-Coles against baseline bookmaker implied probabilities.

### Manual by User
1. **Execute Walk-Forward Backtest**:
   - Run backtest script:
     ```powershell
     python -m python.backtesting.walk_forward --seasons 3
     ```
   - Review out-of-sample ROI and Brier score summary table printed to console.

---

## Phase 9: Background Worker Automation

### Automated by Claude
1. Create unified CLI runner `python/workers/runner.py` supporting modular worker commands:
   - `python -m python.workers.runner discovery`
   - `python -m python.workers.runner lineups`
   - `python -m python.workers.runner analyze`
   - `python -m python.workers.runner settle`
   - `python -m python.workers.runner evaluate`
2. Implement `evaluator_worker.py`: settles finished matches against actual scorelines, calculates profit/loss, and logs errors to `prediction_errors`.
3. Configure lightweight GitHub Actions workflow `.github/workflows/worker_cron.yml` to trigger non-intrusive polling.

### Manual by User
1. **Enable GitHub Actions Scheduling**:
   - Navigate to GitHub repository **Actions** tab.
   - Enable workflow `worker_cron.yml`.
2. **Trigger Initial Manual Worker Run**:
   - Click **Run workflow** on `worker_cron.yml` and monitor logs in GitHub UI.

---

## Phase 10: Production Hardening & Observability

### Automated by Claude
1. Implement database transaction locks for worker idempotency: prevent duplicate predictions or settlements on identical match snapshots.
2. Build data retention pruner: purge transient raw in-play tick data older than 14 days while keeping match summaries, odds snapshots, and predictions indefinitely.
3. Build health check endpoint `GET /api/engine/health` reporting database connectivity, quota remaining, and active worker statuses.

### Manual by User
- No manual actions required. All operations automated.

---

## Phase 11: Stealth Executive UI & Match Center

### Automated by Claude
1. Polish Next.js match center (`src/app/matches/[id]/page.tsx`):
   - Dynamic competition chips populated directly from Supabase `competitions`.
   - Render Fair Probability, Expected Value, 1xBet Line, and Market Consensus.
   - Render IST (UTC+5:30) timestamps for all kickoffs and update times.
   - Cleanse all UI components of internal algorithmic names (zero mention of Dixon-Coles, Elo, or API-Football).
2. Wire up on-demand Refresh button to trigger user-budgeted prediction refresh (reserving 1 credit from 50 user pool).

### Manual by User
1. **Verify UI in Browser**:
   - Open `http://localhost:3000`.
   - Inspect match cards and upcoming schedules.
   - Verify times match Indian Standard Time.
   - Click "Refresh" on a match and verify quota counter decreases by 1 in Supabase `provider_usage`.

---

## Phase 12: Reinforcement Learning & Contextual Bandit

### Automated by Claude
1. Implement offline Contextual Bandit policy (`python/rl/bandit_policy.py`).
2. Train policy strictly on historical paper-bet ledger with reward = realized flat-stake P&L and CLV bonus.
3. Implement safety constraint: policy cannot lower the 3% EV threshold or bypass lineup confirmation.
4. Keep RL policy in `RESEARCH` mode until 1,000 settled paper bets are recorded.

### Manual by User
1. **Inspect Bandit Weights**:
   - Run policy diagnostics:
     ```powershell
     python -m python.rl.bandit_policy --inspect
     ```
2. **Promotion Approval**:
   - RL policy will remain shadow/research until the user explicitly executes SQL to update `engine_settings.rl_enabled = true`.
