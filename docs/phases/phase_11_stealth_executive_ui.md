# PHASE 11 — STEALTH EXECUTIVE UI & MATCH INTELLIGENCE CENTER

## 1. Goal
Deliver the complete, production-grade Next.js frontend following the **Mixpanel Dark Slate** design language. Completely eliminate empty placeholder cards on the Match Detail page, ensure all match schedules and updates display in **Indian Standard Time (IST, UTC+5:30)**, dynamically populate competition filters from the Supabase registry, and rigorously enforce **Algorithmic Stealth**: completely sanitize all user-facing screens of internal model names (Dixon-Coles, Elo), scrapers, or third-party provider tags.

## 2. Criticality
**P2 — MEDIUM** (Transforms backend analytical intelligence into an executive user experience).

## 3. Prerequisites
- Phase 7 (Settlement & NO-BET), Phase 9 (Workers), and Phase 10 (Health check) operational.

## 4. Exact Tasks

### Parallelizable Subtasks
- **Task 11.1 [Dynamic Registry Filter]**: Update `src/components/dashboard/CompetitionFilter.tsx`:
  - Fetch enabled leagues dynamically from Supabase `competitions` where `is_enabled == true`.
  - Provide quick-select chips for top domestic leagues and international tournaments.
- **Task 11.2 [Match Detail Page Implementation]**: Rewrite `src/app/matches/[id]/page.tsx`:
  - **Match Header**: Team badges, canonical competition, venue, referee, kickoff in IST (`DD MMM, hh:mm A IST`), status badge (`LIVE`, `FT`, `Upcoming`).
  - **Lineup & Formation Card**: Displays confirmed starting XIs, tactical grid, and substitutes. If unconfirmed, shows countdown timer: "Lineups pending. Match analysis unlocks ~45-60m prior to kickoff."
  - **Market Intelligence Table**: Clean tabular view of `MATCH_1X2`, `TOTAL_GOALS (1.5, 2.5, 3.5)`, and `BTTS`.
  - **Probability & Value Panel**: Displays Fair Market Probability, Calibrated Model Probability, 95% Confidence Interval, Target 1xBet Decimal Odds, Expected Value ($\text{EV} = p \cdot o - 1$), and Recommended Action (`VALUE BET` vs `NO BET`).
  - **Decision Rationale Badge**: For `NO BET`, displays user-friendly explanations ("Minimum 3% edge not met", "Official lineups awaiting confirmation", "Market line suspended").
- **Task 11.3 [User-Reserved On-Demand Refresh]**: Wire up the "Refresh Match Intelligence" button:
  - Invokes `POST /api/matches/[id]/refresh`.
  - Atomically reserves 1 credit from the 50-request user pool via `reserve_api_quota(is_user=true)`.
  - Fetches latest odds, triggers instantaneous re-simulation, and updates UI state.
- **Task 11.4 [Algorithmic IP Sanitization Audit]**: Create `scripts/audit_ui_strings.py`:
  - Scans all files in `src/app/` and `src/components/`.
  - Verifies that terms such as `Dixon-Coles`, `Elo`, `Poisson`, `API-Football`, `Scraper`, or internal formula representations are strictly absent from client-side bundles.

### Sequential Tasks (Follows 11.1 - 11.4)
- **Task 11.5 [IST Timestamp Formatting Verification]**: Verify across all dashboard and detail pages that times match local Indian Standard Time (UTC+5:30) with explicit timezone suffix.
- **Task 11.6 [End-to-End Browser Walkthrough]**: Conduct full manual visual check on `http://localhost:3000` across desktop and mobile viewport widths.

## 5. Files / Modules Affected
- `src/app/matches/[id]/page.tsx`
- `src/components/dashboard/CompetitionFilter.tsx`
- `src/components/matches/MatchHeader.tsx` [NEW]
- `src/components/matches/MarketTable.tsx` [NEW]
- `src/components/matches/LineupView.tsx` [NEW]
- `src/components/matches/ValueEdgeBadge.tsx` [NEW]
- `src/app/api/matches/[id]/refresh/route.ts` [NEW]
- `scripts/audit_ui_strings.py` [NEW]

## 6. Database Changes
- No schema changes required (reads from established Supabase schema).

## 7. Tests Required
- `scripts/audit_ui_strings.py`: Regex search across `src/` for forbidden IP words; fails build if found.
- `tests/test_ist_formatting.ts`: Unit test asserting UTC timestamps are formatted correctly to IST with 12-hour AM/PM notation.

## 8. Acceptance Criteria
- [ ] Match Detail page renders full market table, confirmed lineups, probabilities, and EV with zero empty placeholders.
- [ ] All timestamps display explicitly in Indian Standard Time (`IST`).
- [ ] Zero internal algorithm names, vendor titles, or scraping libraries appear anywhere in the UI.
- [ ] User "Refresh" button respects the 50-request user daily quota cap.

## 9. Deployment Method & Automated Actions
- **Automated by Claude**:
  1. Build Match Detail components and dynamic competition filters.
  2. Implement on-demand refresh server route.
  3. Execute UI IP audit script `python scripts/audit_ui_strings.py`.

## 10. Manual Steps Required After Deployment
- **User Must Do**:
  1. Open `http://localhost:3000` in browser.
  2. Click into any upcoming fixture.
  3. Verify lineup countdown message or confirmed XI view.
  4. Verify times are in IST.

## 11. Rollback Plan
- Revert Git commit for frontend components if build errors occur in Next.js bundle.

## 12. Risks
- Client-side hydration mismatches with server-side rendered dates. Mitigated by using a client-side date formatting hook (`useFormattedIST`).

## 13. What Must NOT Be Considered Complete
- Any UI displaying internal model names or raw provider JSON.
- A match detail page showing "Work in progress" or blank cards.
