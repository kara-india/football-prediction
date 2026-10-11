# Recovery status

Resume contract for any later session. `docs/PHASE_STATUS.md` is historical and must not be treated as proof that the product works.

- **HEAD this change is based on:** `dbc94dec76d0b1016d73eed777e3fb7285c43e6a`
- **Current phase:** `A0`
- **Current subtask:** `A0 complete in this commit. Next session starts at A1.1`
- **Do not push again until the next full letter-phase (A1) is done.** Vercel deploys `main`.

Product contract (do not reinterpret): EPL only; bet only after a real 11v11 snapshot; calibrated probability **> 0.70** plus a reliability bin of ≥80 settled cases in `[0.62, 0.85]`; positive de-vigged EV; stake = quarter-Kelly capped at 1% of bankroll; else `NO_BET`. API-Football is forbidden. RL may not lower the gate. Published exploration is forbidden.

## Phase board

| Phase | Status | Depends on | Next concrete subtask |
|---|---|---|---|
| A0 Provider seam, API-Football removed from runtime | **DONE** | — | none |
| A1 Historical PL corpus + team aliases | **NOT_STARTED** | A0 | A1.1 commit `data/football_data_uk/E0` CSVs for completed seasons and a loader that does not download in CI |
| A2 Champion artifact + calibrator + p≥0.70 reliability bins | **NOT_STARTED** | A1 | blocked |
| A3 Manual lineup snapshot writer (11+11, source_url, confirmed_at) | **NOT_STARTED** | A0 | can start in parallel with A1 after this commit |
| A4 Odds snapshot + de-vig + quarter-Kelly | **NOT_STARTED** | A0 | can start in parallel with A1; no key ⇒ `ODDS_UNAVAILABLE` |
| A5 Decision service wires champion λ into `AnalysisWorker` | **NOT_STARTED** | A2, A3, A4 | blocked |
| A6 Online learner actually updates Dixon-Coles; bandit stays shadow | **NOT_STARTED** | A2, A5 | blocked |
| A7 In-play remaining-time Poisson | **NOT_STARTED** | A5 | blocked |
| A8 UI reads `decision_opportunities` only | **NOT_STARTED** | A5 | blocked |
| A9 CI ban + decision tests | **PARTIAL** | A0 | A0 ban test is in `tests/test_api_football_removed.py`. Remaining decision tests wait for A5 |

## A0 subtasks

- [x] A0.1 `python/providers/match_protocol.py` types: Fixture, Score, Lineup, OddsSnapshot. No I/O.
- [x] A0.2 `python/providers/runtime_registry.py` allowlist: `football_data_org`, `football_data_uk`, `odds_api`, `manual_lineup`. `api-football` raises `ProviderNotAllowed`.
- [x] A0.3 `APIFootballAdapter._make_request` raises `APIFootballDisabled` after the existing missing-key and quota checks, before any HTTP. `base_url` is empty.
- [x] A0.4 `src/lib/feed.ts` `fetchFootball` returns `{ ok:false, reason:'API_FOOTBALL_REMOVED', status:410 }` and does not fetch.
- [x] A0.5 Scripts that called the retired host now exit 2: `inspect_candidate_fixtures.py`, `run_full_analysis_lanus.py`, `find_active_matches.py`, `check_match.py`, `inspect_japan_uruguay.py`, `scan_allowed_dates.py`.
- [x] A0.6 `tests/test_api_football_removed.py` fails if the retired API host string appears outside that test file.
- [ ] A0.7 **Left on purpose.** Workers (`collector_worker`, `lineup_watcher`, `lineup_gatekeeper`, `fixture_discovery`, `data_pipeline/ingestion`) still import `APIFootballAdapter`. Any real call now raises `APIFootballDisabled`. Replacing those call sites is A1/A3/A5, not a drive-by rewrite.

## Known blockers the next session must not rediscover

1. `AnalysisWorker.compute_starter_ratings` still defaults λ to 1.45 / 1.15. `DixonColesModel` is not imported there. `generate_forecasts` passes `historical_sample_size=0`, so the gate always adds `INSUFFICIENT_SAMPLE`. Do not "fix" that by passing a fake 500.
2. `python/main.py` `POST /analyze/{match_id}` returns `not_implemented`.
3. `python/learning/online_learner.py` is a no-op.
4. `OneXBetAdapter.get_match_odds` always raises `OddsUnavailableException`.
5. `PlayerGoalModel` still defaults `goals_per_90` to 0.1. Delete that default in A3, do not use it.
6. Walk-forward on PL (`docs/MODEL_BENCHMARK_RESULTS.md`): Brier 0.596 vs 0.667 uniform, accuracy 0.521. A 0.70 filter will rarely fire. That is expected.
7. `.github/workflows/bootstrap-champion.yml` checks out missing branch `phase-15-advanced-statistical-models` and missing `scripts/train_champion_artifact.py`, with an empty Supabase secret. Fix in A2. Do not commit service-role keys.
8. Free lineup API does not exist for this product. A3 is a manual `lineup_snapshots` row, not a scraper.
9. `engine_enabled` stays false.

## A1 instructions (start here)

1. Vendor football-data.co.uk `E0.csv` for seasons `2019/20` through the last **completed** season under `data/football_data_uk/`. Do not download during tests.
2. Add `python/providers/football_data_uk.py` implementing a historical loader only (not live fixtures).
3. Add `data/team_aliases.csv` mapping football-data.co.uk names. Unmapped name ⇒ caller must abstain. No fuzzy match.
4. Point-in-time rule: result visible at kickoff+3h. Closing odds (`B365C*`) are training labels only, never a live price.
5. Do not start A5 in the same commit as A1.

## Push rule

One push per completed letter-phase (A1, then A2, …). Do not push subtask checkpoints to `main` unless that letter-phase is done. This A0 commit is the first allowed push.
