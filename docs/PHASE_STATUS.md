# PHASE STATUS & RESUME CONTRACT
# Football Prediction Intelligence Platform

This document is the authoritative runtime state contract for development sessions in Antigravity. It is updated at the conclusion of every phase and read immediately when the user commands `START DEVELOPMENT`.

---

## Current Platform State

- **CURRENT PHASE**: `Phase 0 — Repository and Security Hardening`
- **STATUS**: `PENDING_START`
- **LAST COMPLETED PHASE**: `None` (Scaffold and Planning Phase Completed)
- **LAST VERIFIED GIT SHA**: `3914ef35b1ac89051f14b1c5e0f8b44bd4525cf3`
- **LAST VERIFIED SUPABASE STATE**: 
  - Project URL: `https://qqcxjjkgvqknesrtnwal.supabase.co`
  - Engine: PostgreSQL 17 (Healthy)
  - Tables: 27 tables active
  - Historical Matches: 13,403 rows present in `historical_matches`
  - Migration Status: Migration drift detected; baseline reconciliation required in Phase 1
  - RLS Status: Enabled, but multiple tables have permissive `FOR ALL USING (true)` policies
- **CURRENT DEPLOYMENT**: Local Next.js 14 development server running on `http://localhost:3000` (Dark Slate Mixpanel theme active)
- **BLOCKERS**:
  1. Leaked API-Football credential (`073534f7111a37868a403c5cd51d83fa`) in `README.md` and server routes requires rotation by user.
  2. Python runtime dependencies unpinned (`python/requirements.txt` missing).
  3. GitHub CI workflow swallows errors with `|| echo 'done'`.
  4. Background workers (`collector_worker.py`, etc.) are empty `pass` stubs.
- **MANUAL STEPS PENDING**:
  - [ ] User must log in to API-Sports dashboard and rotate the exposed API key (`073534...`).
  - [ ] User must set rotated `API_FOOTBALL_KEY` in GitHub Repository Secrets and local `.env.local`.
- **NEXT ACTION**: When the user enters `START DEVELOPMENT`, Claude Sonnet 4.6 Thinking will immediately begin **Phase 0: Task 0.1 (Secrets Scrubbing)** and **Task 0.2 (Python Dependency Pinning)**.

---

## Phase Progression Matrix

| Phase | Title | Criticality | Status | Started At | Completed At | Verification SHA |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 0** | Repository & Security Hardening | **P0** | `READY_TO_START` | — | — | — |
| **Phase 1** | Database & Migration Hardening | **P0** | `PENDING` | — | — | — |
| **Phase 2** | Quota Governance & Cost Safety | **P0** | `PENDING` | — | — | — |
| **Phase 3** | Zero-Cost Data Ingestion | **P1** | `PENDING` | — | — | — |
| **Phase 4** | Target Odds (1xBet) Engine | **P1** | `PENDING` | — | — | — |
| **Phase 5** | Lineup & Runtime Gatekeeper | **P1** | `PENDING` | — | — | — |
| **Phase 6** | Core Statistical & Monte Carlo | **P1** | `PENDING` | — | — | — |
| **Phase 7** | Market Settlement & Edge Engine | **P1** | `PENDING` | — | — | — |
| **Phase 8** | Walk-Forward Validation | **P1** | `PENDING` | — | — | — |
| **Phase 9** | Background Worker Automation | **P2** | `PENDING` | — | — | — |
| **Phase 10** | Production Hardening & Observability | **P2** | `PENDING` | — | — | — |
| **Phase 11** | Stealth Executive UI & Match Center | **P2** | `PENDING` | — | — | — |
| **Phase 12** | RL & Contextual Bandit Policy | **P3** | `PENDING` | — | — | — |

---

## Resume Protocol for Claude Sonnet 4.6 Thinking

When triggered by the command `START DEVELOPMENT`:
1. Check `CURRENT PHASE`. If `Phase 0`, inspect `docs/phases/phase_00_security_repo_hardening.md`.
2. Inspect git worktree: verify no uncommitted changes conflict with phase goals.
3. Verify environment variables in `.env.local`.
4. Implement tasks in parallel where permitted by the phase specification.
5. Execute phase test suite.
6. Commit progress: `git commit -m "feat(phase-0): complete repository and security hardening"`.
7. Update this document:
   - Set `LAST COMPLETED PHASE` to current phase.
   - Advance `CURRENT PHASE` to next phase.
   - Update `LAST VERIFIED GIT SHA`.
   - Update `STATUS`.
8. Check if manual steps are required. If so, output the checklist from `docs/DEPLOYMENT_MANUAL_STEPS.md` and pause.
