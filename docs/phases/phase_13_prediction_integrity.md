# Phase 13 — Prediction Integrity & Runtime Truthfulness

**Status:** COMPLETE (implementation complete; external CI execution unavailable from this session)
**Verification basis:** Static repository audit + regression tests added; GitHub Actions reported no workflow run for the PR head.

## Objective
Eliminate production paths that can fabricate odds, calibration, freshness, sample sizes, comparison statistics, or provider credentials.

## Completed
- Removed synthetic 1xBet odds fallback from python/workers/analysis_worker.py.
- Removed synthetic isotonic calibration bootstrap.
- Missing odds now produce explicit ODDS_UNAVAILABLE and force NO_BET.
- Missing validated calibration now produces MODEL_UNCALIBRATED and force NO_BET.
- Prediction snapshots persist the actual Monte Carlo path count.
- API-Football refuses outbound calls when API_FOOTBALL_KEY is not configured.
- Walk-forward evaluation no longer substitutes odds or hard-coded p-values.
- Model comparison no longer manufactures a statistical p-value or winner without paired predictions.
- Fixed Dixon-Coles profile-likelihood state restoration so the selected xi and its fitted parameters remain aligned.
- Fixed the CI workflow to execute the tracked root tests/ suite.

## Regression Coverage
`tests/test_prediction_integrity.py` covers missing API credential rejection, no synthetic odds/calibration, actual simulation-count provenance, Dixon-Coles xi-fit restoration, and no fabricated walk-forward comparison p-values.

## Known remaining work
- Persist lineup versions/hashes in Supabase.
- Persist counterfactual decision opportunities in Supabase.
- Replace process-local learner residual state with durable versioned state.
- Implement genuine live-state parsing/event detection.
- Make quota governance fail closed when the central DB governor is unavailable.
