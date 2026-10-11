# Recovery status

Resume contract for any later session. `docs/PHASE_STATUS.md` is historical and must not be treated as proof that the product works.

- **HEAD this change is based on:** `dbc94dec76d0b1016d73eed777e3fb7285c43e6a`
- **Current phase:** `A1 complete; A1.5 provider bridge in progress`
- **Current subtask:** `A1.5 on-demand fixture/odds flows and durable shared cache/quota ledger implemented; provider responses still need live validation`
- **Tests run:** `tests/test_api_football_removed.py` (3 passed), `tests/test_football_data_uk_history.py` (2 passed), and `tests/test_dixon_coles.py` (7 passed); benchmark regenerated from vendored data.
- **Next parallel phases:** A3 manual lineup contract and A4 live odds/Kelly can proceed from A0 interfaces. A2 champion fitting depends on this A1 corpus.
- **Push policy:** One push per completed letter-phase. The current change is based on A0 and is not based on `main`; Vercel production deploys from `main`.

Product contract (do not reinterpret): EPL only; bet only after a real 11v11 snapshot; calibrated probability **> 0.70** plus a reliability bin of ≥80 settled cases in `[0.62, 0.85]`; positive de-vigged EV; stake = quarter-Kelly capped at 1% of bankroll; else `NO_BET`. API-Football is forbidden. RL may not lower the gate. Published exploration is forbidden.

## Phase board

| Phase | Status | Depends on | Next concrete subtask |
|---|---|---|---|
| A0 Provider seam, API-Football removed from runtime | **DONE** | — | none |
| A1 Historical PL corpus + team aliases | **DONE** | A0 | Vendored 2019/20–2025/26 E0 CSVs; local-only point-in-time loader; exact provider aliases; regenerated walk-forward report |
| A1.5 football-data.org + Odds API client wiring | **IN PROGRESS — implementation, Supabase migration, and Vercel provider config applied; live payload validation remains** | A0 | Redeploy preview/production, then validate fixture and onexbet payloads with explicit user actions |
| A2 Champion artifact + calibrator + p≥0.70 reliability bins | **NOT_STARTED** | A1 | A2.1 implement `scripts/train_champion_artifact.py`; use the A1 corpus |
| A3 Manual lineup snapshot writer (11+11, source_url, confirmed_at) | **NOT_STARTED** | A0 | can proceed in parallel with A2; operator-entered only |
| A4 Odds snapshot + de-vig + quarter-Kelly | **NOT_STARTED** | A0 | can proceed in parallel with A2; no key ⇒ `ODDS_UNAVAILABLE` |
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
6. Walk-forward diagnostic (`docs/MODEL_BENCHMARK_RESULTS.md`): Brier 0.602 vs 0.667 uniform, accuracy 0.509. In the distinct-fixture view, raw p≥0.70 occurred 184/1,710 times (77.7% hit rate) with mean CLV −0.60%. These probabilities are uncalibrated and do not prove the live reliability gate.
7. `.github/workflows/bootstrap-champion.yml` checks out missing branch `phase-15-advanced-statistical-models` and missing `scripts/train_champion_artifact.py`, with an empty Supabase secret. Fix in A2. Do not commit service-role keys.
8. Free lineup API does not exist for this product. A3 is a manual `lineup_snapshots` row, not a scraper.
9. `engine_enabled` stays false.

## A1 completed scope

- Vendored seven completed seasons (2,660 rows) through 2025/26. No current-season file was included.
- `python/providers/football_data_uk.py` reads only local files. Results are available at kickoff + 3h; `as_of` must be timezone-aware. Opening/closing Bet365 prices are separate fields; close prices remain historical labels.
- `data/team_aliases.csv` resolves exact names from football-data.co.uk, football-data.org, and FPL (including FPL short codes). Unknown names resolve to `None`; the decision path must abstain.
- `scripts/run_historical_walkforward.py` reads the vendored corpus, respects the +3h result availability at each fold boundary, and writes per-fold raw p≥0.70 count, hit rate, mean opening odds, and opening-vs-close CLV into `docs/MODEL_BENCHMARK_RESULTS.md`.
- Benchmark diagnostic: 7,790 overlapping fold predictions across 41 folds. The distinct-fixture view keeps the latest eligible prediction per fixture: 184/1,710 raw top-outcome probabilities were ≥0.70, hit rate 77.7%, mean CLV −0.60%. These probabilities are uncalibrated and do not satisfy the live gate.
- Verification performed: three API-Football removal tests, two A1 loader tests, and seven existing Dixon-Coles tests passed. The benchmark script completed and generated its report. No broad CI suite was run.

## A1.5 local progress (not verified)

- Next.js fixture client now uses `FOOTBALL_DATA_ORG_TOKEN` only in the `X-Auth-Token` header. Upcoming, in-progress, and detail routes have been switched to football-data.org v4 response shapes.
- Python football-data.org client and The Odds API v4 client are implemented locally. The odds adapter requests only the EPL, EU region, exact `onexbet` bookmaker, and supported v1 markets; no bookmaker fallback is present. The Odds API documents its `apiKey` as a query parameter, so the odds adapter follows that API contract.
- The provided credentials are in ignored `.env.local`; `.env.example` contains variable names only. They were not added to Git.
- Fixture API calls now occur only through `POST /api/matches/sync`, triggered by the Match Intelligence Sync Fixtures button. Listing and detail screens read the shared snapshot; no other route calls football-data.org. Shared fixtures are reused for 10 minutes.
- Odds are requested only when an eligible synced EPL fixture terminal is opened. The API uses the quota-free The Odds API event directory to find the match, then requests only the specific event's 1xBet `h2h` and `totals` markets. Supabase shares cached odds across browsers (60 seconds in-play; 5 minutes pre-match), records provider requests and quota headers, and locks concurrent duplicate fetches.
- PulseScore documentation was reviewed. Its API includes event/score/markets and 1xBet bookmaker endpoints, but it is an odds feed and does not establish confirmed starting XIs. No PulseScore integration or PulseScore key variable exists in this worktree's code or `.env.local`; it cannot be treated as configured here.
- Supabase migration `014_provider_cache_and_usage.sql` was applied to project `qqcxjjkgvqknesrtnwal`; read-only schema inspection confirmed the four cache, quota, log, and lock tables. RLS is enabled; `anon`/`authenticated` have no access and `service_role` has explicit grants. The security advisor reports informational “RLS enabled, no policy” notices, expected for service-role-only tables.
- Vercel metadata lists Supabase service-key and Odds API entries for production/preview. The first preview runtime check still reported shared cache and Odds API as unavailable; I updated `ODDS_API_KEY` from the user-provided local value and added support for `SUPABASE_SECRET_KEY` as well as the legacy service-role variable. A fresh preview must confirm these settings are visible at runtime before any provider call.
- I added the user-provided football-data.org token as a sensitive `FOOTBALL_DATA_ORG_TOKEN` for production/preview; the preview confirmed it is present. Vercel metadata also confirms `PULSESCORE_API_KEY` is configured for production/preview, but PulseScore is not wired into A1.5. No credential values are committed or printed.
- `.env.local` currently has neither Supabase server key; local provider calls therefore fail closed. Analysis still returns unavailable until A5.
- Provider response behavior has not been checked with live requests. No provider calls were made during this implementation.
- UI labels for provider, operating mode, and odds have been corrected locally; UI build and provider integration remain unverified.

## Next instructions

1. Redeploy preview to verify the Supabase and Odds API credentials, then complete A1.5 provider validation with explicit sync/match-terminal actions. Configure a Supabase server key locally only if local live validation is needed.
2. A2.1: implement `scripts/train_champion_artifact.py`; fit before the calibration window, calibrate only on that next window, and refuse output without ≥1,000 training matches and a nonempty p≥0.70 reliability bin.
3. A3 and A4 can proceed in parallel after A0; do not start A5 before A2, A3, and A4 exist.
4. Do not use the raw 77.6% diagnostic as calibrated reliability evidence. Do not relax the confidence gate to generate bets.

## Push rule

One push per completed letter-phase (A1, then A2, …). Do not push subtask checkpoints to `main` unless that letter-phase is done. A1 is ready to update the existing A0 recovery PR branch; production deploys from `main`.
