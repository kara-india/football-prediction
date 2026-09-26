# Phase 14 — Durable State & Temporal Learning Foundation

Status: IMPLEMENTED — runtime integration remains the next step.

Implemented:
- Supabase tables for lineup snapshots, decision opportunities, and durable learning state.
- RLS enabled with service-role-only access for these internal tables.
- Foreign keys and operational indexes for match/time, market/time, settlement, and action queries.
- Deterministic lineup fingerprint/version helper with regression tests.
- Supabase migration applied and verified against the live project.

Next runtime integration:
- LineupWatcher must write/read lineup_snapshots and derive V1/V2 from persisted hashes.
- AnalysisWorker must persist eligible decision opportunities with behavior-policy metadata.
- Online learner must read/write learning_state transactionally.

This phase deliberately does not claim those runtime integrations are complete yet.
