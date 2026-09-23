# PHASE 11 — SOFASCORE-INSPIRED TERMINAL UI & MATCH INTELLIGENCE CENTER

## 1. Goal
Deliver the complete, production-grade Next.js frontend following the **Sofascore Football UX and Information Architecture**, adapted into an institutional quantitative analytics terminal. Completely eliminate placeholder cards on the Match Detail page, ensure all match schedules and updates display in **Indian Standard Time (IST, UTC+5:30)**, dynamically populate competition filters from the Supabase registry, establish reusable terminal design primitives, and enforce **Model Transparency**: expose the full analytical derivation of every probability without ever inventing numbers or using sportsbook gamification.

> **Approved Design Reference Directive**:  
> **"Approved design reference: Sofascore football UX/information architecture, adapted into a premium football analytics terminal."**

## 2. Criticality
**P2 — MEDIUM** (Transforms backend analytical intelligence into an institutional-grade user experience).

## 3. Prerequisites
- Phase 7 (Settlement & NO-BET), Phase 9 (Workers), and Phase 10 (Health check) operational.
- Verified backend data contracts (`docs/DATA_CONTRACTS.md`) and design direction (`docs/FRONTEND_DESIGN_DIRECTION.md`).

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 11.1 [Terminal Design System Primitives]**: Create `src/components/ui/terminal/`:
  - `TerminalCard.tsx`: Restrained slate surfaces (`#0F172A`), subtle borders (`#1E293B`), zero neon.
  - `DataFreshnessBadge.tsx`: Displays exact seconds elapsed since data generation (`14s ago`, `Stale: 4m ago`).
  - `ModelProbabilityBar.tsx`: Calibrated win/draw/loss distribution with 95% confidence intervals.
  - `ValueEdgeIndicator.tsx`: Muted emerald indicator for positive EV ($> 3\%$), neutral slate for NO-BET.
  - `TacticalPitchGrid.tsx`: Sofascore-style 2D formation visualizer for confirmed starting XIs.
- **Task 11.2 [Match Detail Page Architecture]**: Rewrite `src/app/matches/[id]/page.tsx`:
  - **Match Header**: Team logos, canonical league, referee, venue, kickoff in IST (`DD MMM YYYY, hh:mm A IST`), status badge (`LIVE`, `FT`, `Upcoming`).
  - **Tri-Column Intelligence Matrix**:
    - *Column 1 (Model)*: Calibrated probabilities, raw simulation counts ($N=35,000$), standard error ($\pm 0.003$).
    - *Column 2 (Market)*: 1xBet fixed decimal odds, devigged fair price (Shin), margin overround.
    - *Column 3 (Live State)*: Elapsed minute, score, xG accumulation, shots on target, card intensity.
  - **Probability & Momentum Timeline**: Time-series showing in-play win probability drift ($0'$ to $90'$).
  - **Analytical Drill-Down Tabs**: Overview, Model & De-vig, Live State & Hazards, Odds History, Lineups (Pitch Grid), Simulation, and Settlement Audit.
- **Task 11.3 [Multi-Checkpoint & Lineup Delta Card]**: Create `src/components/match/MultiCheckpointTimeline.tsx`:
  - Visualizes the full prediction lifecycle across milestones:
    - *Initial Analysis* (T-48h): Base model probabilities and initial market comparison.
    - *Lineup Confirmed* (T-60m): Post-lineup model probabilities, starting XI ratings, and probability delta ($\Delta p$).
    - *Current Pre-Match* (T-5m): Final model probabilities, closing odds, EV, and decision.
    - *Post-Match Settlement*: Actual score, settlement result, forecast error magnitude, and error taxonomy classification.
  - Transparently highlights Lineup Information Value: displays whether lineup arrival shifted probability toward or away from market.
- **Task 11.4 [Model Improvement & Learning Dashboard]**: Create `src/app/models/page.tsx`:
  - **Champion vs Challenger Matrix**: Live comparison of active champion vs experimental challengers on rolling out-of-sample holdouts (Brier, LogLoss, ECE, CLV).
  - **Lineup Information Value (LIV) Telemetry**: Empirical accuracy before lineups vs after lineups segmented by competition and market.
  - **Error Taxonomy Distribution**: Breakdown of settled prediction errors across the 11 standard causal categories.
  - **Abstention Audit**: Demonstrates value preserved by NO-BET safety gates on volatile fixtures.
- **Task 11.5 [Dashboard & Watchlist Terminal]**: Rewrite `src/app/page.tsx`:
  - Group matches by Sofascore-style league groupings with collapsible accordion headers.
  - Prioritize fixtures into: Live Matches, Priority Watchlist, Model Candidates, and Upcoming (T-60m).
  - Dynamic competition chips populated directly from Supabase `competitions` table.
- **Task 11.6 [User-Budgeted On-Demand Refresh]**: Wire up the "Refresh Match Intelligence" action:
  - Invokes `POST /api/matches/[id]/refresh`.
  - Atomically reserves 1 credit from the 50-request user pool via `reserve_api_quota(is_user=true)`.
  - If user budget exhausted, renders informative notice: *"Daily live refresh quota reached. Resets at 00:00 UTC."*
- **Task 11.7 [Component Replacement & Sanitization Audit]**:
  - Replace legacy stubbed components: `LiveStatePanel.tsx`, `OddsPanel.tsx`, `ModelPanel.tsx`, `MarketTable.tsx`, and `EngineStatus.tsx`.
  - Execute audit script `scripts/audit_ui_strings.py` to ensure zero hardcoded fake statistics or sportsbook betting cues exist.

### Sequential Tasks (Follows 11.1 - 11.6)
- **Task 11.7 [Real-Time Staleness & Error State Testing]**: Verify that when odds are missing, UI shows `1xBet Odds Unavailable` (never fake odds); when lineups are unconfirmed, UI shows countdown timer and attaches `NO_BET`.
- **Task 11.8 [IST Verification & Visual Walkthrough]**: Verify that all kickoff times across dashboard and match detail match Indian Standard Time (UTC+5:30) with explicit `IST` label.

## 5. Files / Modules Affected
- `src/app/matches/[id]/page.tsx`
- `src/app/page.tsx`
- `src/components/ui/terminal/TerminalCard.tsx` [NEW]
- `src/components/ui/terminal/TacticalPitchGrid.tsx` [NEW]
- `src/components/ui/terminal/DataFreshnessBadge.tsx` [NEW]
- `src/components/match/ModelTransparencyCard.tsx` [NEW]
- `src/components/match/TriColumnMatrix.tsx` [NEW]
- `src/components/match/ProbabilityTimeline.tsx` [NEW]
- `src/components/match/LiveStatePanel.tsx` [REPLACE]
- `src/components/match/OddsPanel.tsx` [REPLACE]
- `src/components/match/ModelPanel.tsx` [REPLACE]
- `src/components/match/MarketTable.tsx` [REPLACE]
- `src/components/dashboard/EngineStatus.tsx` [REPLACE]
- `scripts/audit_ui_strings.py` [NEW]
- `tests/test_ui_contracts.ts` [NEW]

## 6. Database Changes
- No schema changes required (consumes established Supabase schema).

## 7. Tests Required
- `scripts/audit_ui_strings.py`: Scans client bundles; fails if prohibited sportsbook phrases or hardcoded fake statistics are detected.
- `tests/test_ui_contracts.ts`: Unit test asserting UTC timestamps are formatted correctly to IST with 12-hour AM/PM notation.
- `tests/test_staleness_states.tsx`: Verifies component rendering for stale data, missing odds, and unconfirmed lineups.

## 8. Acceptance Criteria
- [ ] Match Detail page reflects Sofascore information architecture with Tri-Column intelligence matrix and tactical pitch grid.
- [ ] Every prediction displays its complete mathematical derivation (simulation count, calibration version, 1xBet price, EV, and decision code).
- [ ] UI strictly reflects backend reality: displays `Odds Unavailable` or `Stale State` when data is missing; never fabricates numbers.
- [ ] All timestamps display in Indian Standard Time (`IST`).
- [ ] Zero sportsbook neon styling, betting confetti, or gamification elements.
- [ ] User "Refresh" button respects the 50-request user daily quota cap.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Build terminal design system primitives and Sofascore-style match components.
  2. Implement Model Transparency Card and Tri-Column Matrix.
  3. Execute UI IP audit script `python scripts/audit_ui_strings.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Open `http://localhost:3000` in browser.
  2. Click into any upcoming fixture.
  3. Verify lineup countdown message or confirmed XI tactical pitch view.
  4. Verify times are in IST.

## 11. Rollback Plan
- Revert Git commit for frontend components if build errors occur in Next.js bundle.

## 12. Risks
- Client-side hydration mismatches with server-side rendered dates. Mitigated by using a client-side date formatting hook (`useFormattedIST`).

## 13. What Must NOT Be Considered Complete
- Any UI displaying internal scraping libraries or raw unparsed JSON.
- A match detail page showing "Work in progress", empty tabs, or hardcoded mock odds.
- Any betting-style slip or gamified "Bet Now" interface.
