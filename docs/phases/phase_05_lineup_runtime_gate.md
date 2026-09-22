# PHASE 5 — LINEUP & RUNTIME GATEKEEPER

## 1. Goal
Implement a robust runtime gatekeeper that monitors upcoming matches within 60 minutes of kickoff ($T-60\text{m}$), fetches official starting XIs and formations via API-Football using an economical single-request strategy, populates the canonical `lineups` table, and enforces the mandatory pre-match **Lineup Gate**: any match without confirmed starting lineups is strictly tagged with `NO_BET: LINEUP_UNCONFIRMED` while displaying an informative UI message.

## 2. Criticality
**P1 — HIGH** (Fundamental to preventing prediction error from unexpected benching of key players).

## 3. Prerequisites
- Phase 2 (Quota governance) and Phase 3 (Fixture ingestion) completed.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 5.1 [Lineup Ingestion Engine]**: Create `python/workers/lineup_gatekeeper.py`:
  - Queries Supabase for matches where `status == 'NS'`, `is_eligible == true`, `lineup_confirmed == false`, and `kickoff_utc BETWEEN NOW() AND NOW() + INTERVAL '60 minutes'`.
  - Sorts by kickoff proximity.
  - For each candidate match, reserves 1 worker API credit via `reserve_api_quota()`.
  - Calls API-Football `/fixtures/lineups?fixture={id}`.
  - Validates payload: checks that exactly 11 starters are present for both home and away teams.
  - If valid: inserts starters and substitutes into `lineups` table and sets `matches.lineup_confirmed = true` and `matches.lineup_confirmed_at = NOW()`.
- **Task 5.2 [Competition Allowlist Gate]**: Create `python/engine/competition_gate.py`:
  - Enforces the 10-league allowlist + major tournaments (EPL, La Liga, Bundesliga, Serie A, Ligue 1, Portugal, Netherlands, Belgium, Argentina, Brazil, Champions League, Europa League, World Cup, Euro, Copa America, AFCON, AFC Asian Cup, Senior Men's Friendlies).
  - Rejects women's, youth (U21/U19/U17), reserve, and lower division matches (`is_eligible = false`).
- **Task 5.3 [UI Status Messaging Engine]**: Create `src/lib/matchStatus.ts`:
  - Returns human-readable UI status for upcoming matches:
    - If `kickoff > NOW() + 60m`: "Upcoming • Analysis unlocks at T-60m once official lineups are announced."
    - If `kickoff <= NOW() + 60m` and unconfirmed: "Awaiting confirmed lineups from match officials."
    - If confirmed: "Lineups confirmed • Real-time intelligence active."

### Sequential Tasks (Follows 5.1 - 5.3)
- **Task 5.4 [Lineup Gate Enforcement Test]**: Verify that the prediction engine halts and attaches `LINEUP_UNCONFIRMED` whenever a fixture has `lineup_confirmed == false`.
- **Task 5.5 [Quota Economy Verification]**: Confirm that lineup polling never makes redundant calls for fixtures that already have `lineup_confirmed == true`.

## 5. Files / Modules Affected
- `python/workers/lineup_gatekeeper.py` [NEW]
- `python/engine/competition_gate.py` [NEW]
- `src/lib/matchStatus.ts` [NEW]
- `src/components/matches/MatchCard.tsx`
- `tests/test_lineup_gate.py` [NEW]

## 6. Database Changes
- Index on `matches(status, is_eligible, kickoff_utc, lineup_confirmed)`.

## 7. Tests Required
- `tests/test_lineup_gate.py`:
  1. Test fixture allowlist filters out youth/women/lower-tier matches.
  2. Test lineup payload validation: accepts 11 vs 11; rejects empty/partial lineup.
  3. Verify prediction engine rejects candidate bet when `lineup_confirmed == false`.
  4. Verify no API calls are triggered if kickoff is $> 65\text{ minutes}$ away.

## 8. Acceptance Criteria
- [ ] Official lineups populated in Supabase `lineups` table with verified player IDs and formations.
- [ ] Upcoming fixtures with unconfirmed lineups display clear countdown messaging in UI.
- [ ] Prediction engine refuses to output a `BET` recommendation prior to lineup verification.
- [ ] Lineup polling consumes at most 1 API credit per eligible match.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Build `lineup_gatekeeper.py`, `competition_gate.py`, and `matchStatus.ts`.
  2. Run `pytest tests/test_lineup_gate.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Test the lineup watcher manually on a fixture scheduled within the hour:
     ```powershell
     python -m python.workers.lineup_gatekeeper --run-once
     ```
  2. Verify Supabase `lineups` table receives 22 starter rows and `matches.lineup_confirmed` flips to `true`.

## 11. Rollback Plan
- Disable worker lineup polling in `engine_settings.lineup_polling_enabled = false` if API rate limits are approached.

## 12. Risks
- Delay in official team sheet publication (some leagues publish at T-45m instead of T-60m). The worker handles this by retrying every 10 minutes until T-15m.

## 13. What Must NOT Be Considered Complete
- Assuming expected or predicted lineups are "confirmed".
- Producing betting predictions when official team sheets have not been verified.
