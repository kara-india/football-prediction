# PHASE 4 — TARGET ODDS (1xBET) ENGINE & ANTI-FABRICATION

## 1. Goal
Implement a verified, production-grade odds integration targeting **1xBet** fixed-odds prices. Eliminate fake booleans (`is_1xbet_confirmed=True`) and empty lists. Enforce mathematical de-vigging, snapshot historical prices into Supabase `odds_snapshots`, and strictly enforce the **Anti-Fabrication Rule**: if a genuine 1xBet line cannot be retrieved, trigger `NO_BET` with reason `ODDS_UNAVAILABLE` rather than generating synthetic or mocked prices.

## 2. Criticality
**P1 — HIGH** (Expected value cannot be calculated without real market-clearing prices).

## 3. Prerequisites
- Phase 2 (Quota governance) and Phase 3 (Canonical fixtures) completed.
- Target bookmaker connectivity researched and verified.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 4.1 [Real 1xBet Provider Adapter]**: Overhaul `python/adapters/one_xbet_adapter.py`:
  - Implement genuine network reachability check to 1xBet API / endpoint.
  - Implement fixture matching by team names and kickoff time with similarity threshold $\ge 0.85$.
  - Parse supported canonical markets:
    - `MATCH_1X2` (Home, Draw, Away)
    - `DOUBLE_CHANCE` (1X, 12, X2)
    - `TOTAL_GOALS` (Over/Under 1.5, 2.5, 3.5)
    - `BTTS` (Both Teams To Score: Yes/No)
  - Normalize prices into `CanonicalOddsMarket` and `CanonicalOddsSelection`.
- **Task 4.2 [Margin Removal & De-Vigging Engine]**: Create `python/odds/devig.py`:
  - Calculate market overround / margin: $M = \sum \frac{1}{o_i} - 1.0$.
  - Implement Multiplicative (Proportional) devigging: $p_i = \frac{1 / o_i}{\sum (1 / o_j)}$.
  - Implement Shin's method for handling the favorite-longshot bias in 3-way markets (`MATCH_1X2`).
  - Calculate implied fair probabilities.
- **Task 4.3 [Odds Snapshot Persistence]**: Create `python/odds/snapshot_writer.py`:
  - Writes odds snapshots to Supabase `odds_snapshots` with composite identity:
    `match_id`, `bookmaker='1xbet'`, `market`, `period='FULL_TIME'`, `selection`, `line`, `decimal_odds`, `margin`, `source_timestamp`, `available_at`.
  - Enforces deduplication: identical odds within 60 seconds are not duplicated.

### Sequential Tasks (Follows 4.1 - 4.3)
- **Task 4.4 [Anti-Fabrication Verification]**: Ensure that when network is disconnected or a market is suspended, the adapter returns `OddsUnavailableException` and the system tags the match with `ODDS_STALE` or `MARKET_SUSPENDED`.
- **Task 4.5 [Odds Smoke Test]**: Execute a live pull against a scheduled match and confirm snapshot insertion into Supabase.

## 5. Files / Modules Affected
- `python/adapters/one_xbet_adapter.py`
- `python/adapters/odds_api_adapter.py`
- `python/odds/devig.py` [NEW]
- `python/odds/snapshot_writer.py` [NEW]
- `tests/test_odds_engine.py` [NEW]

## 6. Database Changes
- Ensure `odds_snapshots` table has unique index on `(match_id, bookmaker, canonical_market, selection, line, source_timestamp)`.

## 7. Tests Required
- `tests/test_odds_engine.py`:
  1. Test margin calculation on 1X2 market ($1.95, 3.40, 4.20 \implies M \approx 0.045$).
  2. Test Shin devigging produces probabilities summing to exactly $1.0000$.
  3. Verify that disconnected network yields `OddsUnavailableException` and never synthetic numbers.
  4. Test odds snapshot serialization to Supabase.

## 8. Acceptance Criteria
- [ ] 1xBet odds adapter makes real network calls or explicitly reports unavailable.
- [ ] No hard-coded `is_1xbet_confirmed = True` stubs remain.
- [ ] De-vigged fair probabilities sum to 1.0 within float precision ($\pm 10^{-6}$).
- [ ] Odds snapshots are persistently logged to Supabase for all analyzed fixtures.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Implement `python/odds/devig.py`, `snapshot_writer.py`, and update `one_xbet_adapter.py`.
  2. Run `pytest tests/test_odds_engine.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Run provider connection check from terminal:
     ```powershell
     python -m python.adapters.one_xbet_adapter --check-live
     ```
  2. Confirm console output reports real connection status (OK or Geo-Blocked/Unavailable).

## 11. Rollback Plan
- Revert adapter to previous branch state; ensure fallback `NO_BET: ODDS_UNAVAILABLE` remains active.

## 12. Risks
- Geolocation blocking on target bookmaker API endpoints. If direct access is blocked, adapter must safely surface `1XBET ODDS UNAVAILABLE` without crashing the application.

## 13. What Must NOT Be Considered Complete
- Any adapter that returns static test fixtures in production mode.
- Claiming 1xBet support without executing real HTTP requests.
