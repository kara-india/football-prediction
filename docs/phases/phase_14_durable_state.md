# PHASE 14 SPECIFICATION & EXECUTION CONTRACT
# Durable State Foundation & Transactional Lineup Ledgers

## 1. Architectural Mandate
In strict prequential sports intelligence, process restarts, network timeouts, or worker crashes must NEVER destroy state or fabricate inferences.
Phase 14 converts transient in-memory dictionaries into auditable, durable PostgreSQL ledgers backed by deterministic SHA-256 fingerprinting.

---

## 2. Implemented Schema Migrations

### Migration 011: `lineup_snapshots` (`supabase/migrations/011_lineup_snapshots.sql`)
- **Table**: `lineup_snapshots`
- **Fields**:
  - `id`: BIGSERIAL PRIMARY KEY
  - `fixture_id`: INTEGER NOT NULL (API-Football fixture ID)
  - `snapshot_version`: INTEGER NOT NULL DEFAULT 1 (1 = initial confirmed XI; 2+ = late pre-kickoff changes)
  - `lineup_fingerprint`: TEXT NOT NULL (Deterministic SHA-256 hex string of sorted starter player IDs)
  - `stage`: TEXT NOT NULL (`LINEUP_CONFIRMED`, `LINEUP_V2`, `LINEUP_V3`)
  - `detected_at`: TIMESTAMPTZ NOT NULL DEFAULT NOW()
  - `home_starters`, `away_starters`: JSONB NOT NULL
  - `is_immutable`: BOOLEAN NOT NULL DEFAULT FALSE (Locked after kickoff)
- **Constraints**: UNIQUE(`fixture_id`, `snapshot_version`)
- **Row-Level Security**: Service role write; Anon read-only for immutable records.

### Migration 012: `decision_opportunities` (`supabase/migrations/012_decision_opportunities.sql`)
- **Table**: `decision_opportunities`
- **Purpose**: Persists every model opportunity, including NO-BET decisions, to eradicate survivor/selection bias during offline policy evaluation (OPE) and continual learning.
- **Fields**:
  - `fixture_id`, `prediction_stage`, `market`, `selection`
  - `raw_probability`, `calibrated_probability`, `model_version`, `feature_snapshot_id`
  - `provider_odds`, `implied_probability`, `devigged_probability`, `overround`
  - `expected_value`, `no_bet_reasons`, `gate_decision` (`BET_CANDIDATE`, `NO_BET`, `ABSTAIN`)
  - `behavior_policy_name`, `behavior_propensity` (For Doubly Robust & IPS off-policy evaluation)
  - `actual_outcome`, `settled_at`, `settlement_source`

### Migration 013: `learning_state` (`supabase/migrations/013_learning_state.sql`)
- **Table**: `learning_state`
- **Purpose**: Transactional online learner checkpointing.
- **Fields**: `learner_name`, `learner_version`, `state_json`, `training_sample_count`, `last_fixture_id`, `status`.

---

## 3. Worker Integration (`LineupWatcherWorker`)
- `_compute_lineup_fingerprint(starter_ids: List[int]) -> str`: Deterministic SHA-256 hash of sorted player IDs. Order-invariant.
- `_get_latest_lineup_snapshot(fixture_id)`: Fetches latest version from Supabase.
- `_resolve_lineup_stage_and_version(fixture_id, current_fp)`:
  - If no prior snapshot: Returns `("LINEUP_CONFIRMED", 1)`.
  - If fingerprint matches prior snapshot: Returns `("ALREADY_PERSISTED", -1)` (Zero redundant work).
  - If fingerprint differs: Returns `("LINEUP_V2", next_version)`.
- **Worker Restart Idempotency**: Verified in `tests/test_phase14_durable_state.py`.
