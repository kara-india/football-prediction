# Phase 15 — Match Terminal odds and Champion decision incident log

Date: 2026-10-11
Branch inspected: `phase-15-advanced-statistical-models`
Diagnostic baseline: `56922faa877af13db9f2e79b9c2725a9e5be735d`
Fix branch: `fix/phase-15-live-odds-gate-diagnostics-20261011`

## Symptoms reproduced

- Real Madrid–Villarreal (ESPN event `401882848`) had a forecast, no returned 1xBet price, and Champion reason `LIVE_ONLY_DECISION_ENGINE` shortly before kickoff.
- Napoli–Frosinone (API-Football fixture `1550144`) was returned as `1H`, minute 19, 0–0, but had `odds1xBet: null`, `oddsUpdatedAt: null`, and Champion reason `STALE_ODDS`.
- The terminal showed one generic no-bet message, so users could not tell whether a market was missing, a timestamp was unknown, the model failed, or a value/confidence gate rejected a candidate.

A no-bet response is not proof that each downstream gate ran. The engine's early returns skipped the model and value calculations in these examples.

## External provider blocker confirmed during repair

The deployed `/api/providers/status` endpoint reported `authenticated: false`, `reachable: true`, with API-Football's error stating that the account is suspended. This is an external provider-account state, not a code defect that a repository change can reactivate. The user/account owner must restore API-Football access for its live odds, fixture details, statistics and lineups feeds to resume. ESPN can continue to provide real fixture/status information; the fallback must not synthesize missing 1xBet prices or price timestamps. PulseScore may return actual odds values but without a source timestamp those prices are not actionable and should fail Champion's freshness gate.

## Root causes found

1. **Champion was hard-coded to live mode.** `python/champion_service.py` returned `LIVE_ONLY_DECISION_ENGINE` for every `is_live=false` request, including eligible upcoming fixtures. Its `MatchState` and `NoBetGate` invocation also hard-coded `is_live=True`.
2. **Missing prices were conflated with missing freshness.** The service checked the timestamp before proving that a real supported market existed. A null or invalid timestamp mapped to an infinite age and could yield `STALE_ODDS` without actual age data.
3. **PulseScore freshness could be fabricated.** `src/lib/apiFootball.ts` used `new Date().toISOString()` when the upstream live-odds event had no source timestamp. That can make an un-timestamped price appear freshly updated.
4. **A timestamp could be mistaken for a market.** Odds extraction considered the timestamp when deciding whether the result object was non-empty, even when every actual price was missing.
5. **An in-play list fallback could use a pre-match endpoint.** `src/app/api/matches/live/route.ts` called The Odds API `/sports/upcoming/odds` as a live-price fallback. That endpoint must not be represented as live execution odds.
6. **ESPN IDs were not resolved to API-Football IDs for odds.** The ESPN-specific terminal path queried PulseScore by teams but did not resolve the same event to its API-Football fixture and request that fixture's official odds. The UI's match id is an ESPN event id, not interchangeable with API-Football fixture ids.
7. **Status coverage was incomplete.** API-Football terminal status detection omitted live states such as half-time (`HT`) and interruptions/suspensions.
8. **The UI obscured decision-stage outcomes.** It displayed a generic no-bet sentence and reason code but not which decision gates passed, failed, or were skipped.
9. **Basic fixture lookup was treated as though it contained live detail subresources.** Events, statistics, and lineups are separate API-Football endpoints; reading only `/fixtures?id=...` can leave the Champion input without the data its live-state and lineup gates require.
10. **Repeated terminal refreshes could exhaust the daily API quota.** The page polls live fixtures frequently while the detail handler performed multiple uncached requests for odds, predictions, H2H and other data.
11. **The active Champion artifact's validated holdout cutoff is stale.** The production artifact was refreshed on 2026-10-10, but its `validation.test_end` is still `2024-06-02`. `python/champion_service.py` correctly checks the validation cutoff (not only `trained_at`) and rejects artifacts older than `MAX_ARTIFACT_AGE_DAYS = 365`. Once real fresh odds are restored, this artifact will still hit `MODEL_ARTIFACT_STALE` until the training/validation pipeline is refreshed with newer real results and a new chronological holdout. Changing only the artifact timestamp or loosening this guard would hide stale evidence, not fix it.

## Changes made in the fix branch

- Champion now distinguishes an eligible live fixture from a confirmed future pre-match fixture. Finished, unknown, or otherwise unsupported states remain non-actionable.
- Odds freshness limits are mode-specific: 60 seconds live and 900 seconds pre-match, matching `NoBetGate`.
- Odds are validated before freshness. The response reason distinguishes missing live/pre-match markets, incomplete markets, missing/invalid timestamps, and genuinely stale prices. Provider errors such as a suspended API-Football account are propagated into the relevant gate detail with a concise, non-secret diagnostic.
- Odds extraction requires at least one actual decimal price greater than 1.0. Provider timestamps are normalized only when supplied and parseable; no source timestamp is synthesized.
- The live fixture list no longer promotes The Odds API's upcoming/pre-match prices to live odds.
- For ESPN-backed fixtures, the terminal first checks PulseScore only for in-play events; when needed, it resolves the event by exact home/away names and date to an API-Football fixture, then requests live or pre-match 1xBet odds from the correct endpoint.
- API-Football live-status handling includes `HT`, `BT`, `SUSP`, and `INT` in addition to the existing live statuses.
- The Terminal requests API-Football `/fixtures/events`, `/fixtures/statistics`, and `/fixtures/lineups` separately where needed. Live match state is now assembled from those provider responses; lineup requests are limited to in-play matches or fixtures within 90 minutes of kickoff.
- The Terminal exposes five grouped gate stages as `PASS`, `FAIL`, or `SKIPPED` with explanations. After the model runs, the candidate records also retain the NoBetGate's specific rejection reasons.
- Endpoint-level response caching is used for live odds, statistics/events, lineups, predictions and H2H, with longer TTLs for slow-changing data. The complete terminal response has a short cache so the 15-second UI polling does not repeat every upstream request.
- The pre-match Monte Carlo path no longer applies the learned in-play hazard correction.
- Near-kickoff pages refresh automatically every 15 seconds, as live terminals already did.

## Decision contract and safety

A BET outcome still requires a real supported 1xBet market, a parseable source update timestamp within the applicable freshness limit, the model and calibration stack to run, confidence at or above 55%, and all NoBetGate risk checks to pass. The existing 10-point gate remains authoritative, including lineup validation, player-minute certainty, uncertainty, calibration, edge/EV, and historical-sample requirements.

Missing odds or timestamps fail closed. No synthetic odds or synthetic "fresh" timestamps are used to make a wager actionable. If a provider has no eligible market, no bet is the correct outcome; the UI now exposes that reason rather than mislabeling it.

**Outstanding data-dependent launch blockers:** (1) restore the suspended API-Football account or configure an authorized provider that supplies exact-fixture 1xBet prices and source timestamps; (2) rebuild and chronologically validate the Champion artifact with recent real match results so `validation.test_end` falls within the supported age limit. Until both are met, a live BET is correctly prevented. The gate must not be weakened to manufacture a bet.

Forecast availability remains separate from bet eligibility: a pre-lineup forecast can be shown without authorizing a bet. When ESPN supplies no predictor/boxscore and API-Football is suspended, the terminal may have no trustworthy forecast or H2H data for that fixture; show it as unavailable rather than fabricating statistics.

## Verification checklist

Automated contract tests are added in `tests/test_champion_odds_gate_contract.py` for:
- live fixture with no real odds;
- real prices with no source timestamp;
- live (60-second) versus pre-match (900-second) freshness limits;
- upcoming pre-match requests reaching model readiness rather than the live-only guard;
- ineligible/finished fixture status remaining blocked.

Run from the repository root:

```bash
pip install -r python/requirements.txt
pip install -r python/requirements-dev.txt
PYTHONPATH=. pytest tests/test_champion_odds_gate_contract.py -q
ruff check python/
mypy python/ --ignore-missing-imports
npx tsc --noEmit
npm run lint
NEXT_TELEMETRY_DISABLED=1 npm run build
```

Live odds availability is provider-dependent and cannot be guaranteed for every fixture. The API-Football account-suspension issue is an external remediation item: restore the account or configure an authorized replacement provider before expecting API-Football prices, detailed statistics, and lineups to populate again. A successful build does not prove an upstream bookmaker market exists; verify terminal API payloads and the deployed gate diagnostics against real fixtures after deployment.
