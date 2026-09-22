# FRONTEND DESIGN DIRECTION & INFORMATION ARCHITECTURE
# Football Analytics Terminal: Sofascore Architecture + Institutional Analytics

**Status**: APPROVED DESIGN SPECIFICATION  
**Primary Reference**: [Sofascore Football](https://www.sofascore.com/football)  
**Target Product Persona**: Institutional Football Quantitative Terminal & Paper Intelligence Platform  
**Design Reference Directive**:  
> **"Approved design reference: Sofascore football UX/information architecture, adapted into a premium football analytics terminal."**

---

## 1. Executive Design Philosophy

The objective is **NOT** to visually clone Sofascore or duplicate proprietary UI assets. Rather, Sofascore serves as the industry gold-standard reference for:
- Football-first mental models and navigation ergonomics.
- Match-centric information architecture.
- High information density without visual clutter.
- Progressive disclosure (fast matchday scanning $\to$ micro-level drill-down).
- Real-time match momentum and timeline visualization.
- Player roster, tactical grid, and event hierarchy.
- Desktop analytical workflows for power users.

### 1.1 The Hybrid Aesthetic
Our product blends four design disciplines:
1. **Sofascore Information Architecture**: Match cards, league grouping, live momentum, head-to-head tabs, pitch lineup grids, and event timelines.
2. **Institutional Analytics Terminal Aesthetic**: Clean Dark Slate palette (`#0B0F17` base, `#111827` surfaces, `#1F2937` borders), crisp monospaced numerical typography (`JetBrains Mono` / `Geist Mono`), subtle muted accents, and high data density.
3. **Modern SaaS Usability**: Linear / Stripe-style restrained border radiuses (`rounded-md`, `rounded-lg`), subtle translucent panels (`backdrop-blur-sm`), consistent keyboard navigation (`J`/`K` match traversal), and smooth transitions.
4. **Transparent Model & Provenance Presentation**: Every probability, EV, and decision code is fully decomposable into its mathematical origin (calibration version, simulation paths, data freshness, edge vs. 1xBet price).

### 1.2 Explicit Anti-Patterns (What We Avoid)
- **Zero Sportsbook Clutter**: No neon greens/yellows, no pulsing "BET NOW" buttons, no casino visual cues, and no promotional banners.
- **Zero Artificial Gamification**: No confetti animations, no "sure win" badges, and no tipster emojis.
- **Zero Synthetic Metrics**: No fake "99.9% confidence" badges, no simulated live ticks when the backend has not refreshed, and no placeholder odds.
- **Zero Decorative Fluff**: Every chart, table, and badge must answer a specific quantitative question.

---

## 2. Global Information Architecture & Navigation

The platform features a structured hierarchy designed for rapid switching between macro matchday surveillance and micro analytical deep-dives.

```
FOOTBALL ANALYTICS TERMINAL
├── 1. Dashboard (Command Center)
│   ├── Watchlist (Pinned priority fixtures)
│   ├── Live Match Center (Active fixtures, scoreline, in-play momentum)
│   ├── Upcoming Fixtures (T-60m lineup countdowns, eligible matches)
│   └── Model Signal Stream (Candidate edges, market divergences, NO-BET logs)
│
├── 2. Calendar & Fixtures
│   ├── Date Traversal (Past 7 days results / Next 7 days schedule)
│   └── Competition Registry Filter (EPL, La Liga, Serie A, UCL, etc.)
│
├── 3. Match Detail (Primary Product Experience)
│   ├── Match Header (Teams, score, elapsed time, IST kickoff, venue, ref)
│   ├── Consensus Model Summary (1X2 Probabilities, Fair Odds, Overround)
│   ├── Tri-Column Intelligence Matrix (Model vs. 1xBet Market vs. Live State)
│   ├── Probability & Momentum Timeline
│   └── Analytical Drill-down Tabs:
│       ├── Overview (H2H, Form EWMA, league standing)
│       ├── Model & De-vig (Poisson distribution, Dixon-Coles parameters, identifiability)
│       ├── Live State & Hazards (Possession, xG, shots on target, card intensity)
│       ├── Market & Odds History (1xBet tick history, closing line, margin trend)
│       ├── Lineups & Tactical Pitch (Verified starting XIs, tactical grid, subs)
│       ├── Simulation (Monte Carlo path distribution, standard error convergence)
│       └── Post-Match Settlement (CLV, realized P&L, error classification)
│
├── 4. Quantitative Intelligence & Models
│   ├── Model Registry (Active Champion vs. Challenger versions, parameters)
│   └── Calibration Suite (Isotonic / Platt curves, 10-bin ECE reliability diagrams)
│
├── 5. Backtesting & Walk-Forward Explorer
│   ├── Temporal Fold Matrix (36-month train / validate / test results)
│   └── Out-of-Sample Performance (Brier score, Log loss, ROI, drawdown)
│
├── 6. Prediction & Paper Ledger
│   ├── Settled Ledger (Immutable records of all past predictions & CLV)
│   └── Open Paper Bets (Active positions, unrealized P&L)
│
└── 7. System & Quota Health
    ├── API-Football Quota Meter (Worker 45 budget / User 50 reserve / Safety 5)
    ├── 1xBet Feed Connectivity Monitor
    └── Background Worker Status (Discovery, Lineups, Analysis, Evaluator)
```

---

## 3. Match Detail Page: The Core Experience

The Match Detail view is the institutional centerpiece of the application. It maps directly to Sofascore's match view while replacing consumer sports widgets with quantitative intelligence.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Premier League • Matchday 28                    Kickoff: 23 Sep 2026, 20:00 IST • LIVE 63'  │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  [Logo] ARSENAL                          1  -  0                       CHELSEA [Logo]       │
│                                                                                             │
│  MODEL PROBABILITY (Post-Calibration)                                                       │
│  Home: 58.4% (Fair 1.71)      Draw: 26.2% (Fair 3.82)      Away: 15.4% (Fair 6.49)        │
│  [█████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] │
├──────────────────────────────┬──────────────────────────────┬───────────────────────────────┤
│ MODEL INTELLIGENCE           │ MARKET (1xBet Execution)     │ IN-PLAY MATCH STATE           │
│                              │                              │                               │
│ Total Goals: Over 2.5        │ Current Price: 2.12          │ Score: 1 - 0 (63')            │
│ Model Calibrated: 54.8%      │ Implied Prob: 47.2%          │ Expected Goals (xG): 1.42-0.58│
│ 95% CI: [53.2% — 56.4%]      │ Fair De-vigged: 49.1%        │ Shots (On Target): 12(6) - 5(2)│
│ Simulation SE: ±0.003        │ Value Edge: +5.7%            │ Corners: 7 - 2                │
│ Decision: VALUE CANDIDATE    │ Expected Value (EV): +16.2%  │ Cards: 1 Yellow - 2 Yellow    │
│ Staking (Advisory): 0.5u     │ Status: ACTIVE LIQUIDITY     │ State Latency: 14s (Fresh)    │
├──────────────────────────────┴──────────────────────────────┴───────────────────────────────┤
│ PROBABILITY & MOMENTUM TIMELINE                                                             │
│ [ Interactive time-series showing in-play win probability drift & xG accumulation 0' -> 63']│
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  [Overview]  [Lineups & Pitch]  [Odds Movement]  [Monte Carlo]  [H2H / Form]  [Audit Trail] │
│                                                                                             │
│  Tactical Lineup Grid (Sofascore Pitch Style):                                              │
│  Arsenal (4-3-3 Confirmed 18:55 IST)            Chelsea (4-2-3-1 Confirmed 18:58 IST)       │
│  22 Starters Verified by Official Match Sheet • Zero Lookahead Leakage                      │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Two-Tier Information Density Principle

To serve both rapid decision-making and rigorous institutional research, all screens operate on two simultaneous layers:

### Level 1 — Rapid Scanning (The 5-Second Scan)
A user glancing at the dashboard or match list can immediately answer:
1. **Which matches are eligible?** (Allowlist league badge + senior men's verification).
2. **What is the live state?** (Elapsed minute, score, red cards, data freshness indicator).
3. **What is the lineup status?** (Confirmed green badge vs. T-minus countdown).
4. **Is there an actionable market divergence?** (Model probability vs. 1xBet price delta).
5. **What is the decision?** (`CANDIDATE` highlighted in muted emerald, `NO_BET` in neutral slate with single-word failure code: `EDGE_LOW`, `LINEUP_PENDING`, `STALE_ODDS`).

### Level 2 — Deep Analytical Drill-Down (Progressive Disclosure)
When clicking into any match or market card, the terminal exposes:
1. **Mathematical Provenance**: Model version (`dixon_coles_v1.4`), calibration curve type (Isotonic / Platt), and feature snapshot ID.
2. **Monte Carlo Convergence**: Total paths executed ($N = 25,000$), standard error ($\text{SE} \le 0.004$), and 95% credible intervals.
3. **Odds Movement**: Historical odds ticks from 1xBet, market overround over time, and closing line comparison.
4. **Competing Hazard Trajectory**: In-play scoring and disciplinary hazard curves conditioned on current scoreline and red cards.
5. **Audit Trail**: Timestamp of when data was generated at source vs. ingested into Supabase (`available_at`).

---

## 5. Analytical Odds & Decision Presentation

Odds are presented as financial instruments, strictly avoiding sportsbook gamification.

| Market Outcome | Current 1xBet Odds | Implied Prob | De-Vigged Fair Prob | Calibrated Model Prob | Value Edge | Expected Value (EV) | Decision Code | Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Over 2.5 Goals** | **2.12** | 47.2% | 49.1% | **54.8%** | **+5.7 pp** | **+16.2%** | `PASSED_ALL_GATES` | `CANDIDATE` |
| **Under 2.5 Goals** | **1.78** | 56.2% | 50.9% | **45.2%** | -5.7 pp | -19.5% | `NEGATIVE_EV` | `NO_BET` |
| **Match 1X2: Home** | **1.75** | 57.1% | 55.0% | **58.4%** | +3.4 pp | +2.2% | `EDGE_BELOW_THRESHOLD` | `NO_BET` |
| **Both Teams To Score** | **1.95** | 51.3% | 49.5% | **50.2%** | +0.7 pp | -2.1% | `NEGATIVE_EV` | `NO_BET` |

### The Model Transparency Card
When inspecting any selection, the UI displays the exact analytical derivation:
```
┌──────────────────────────────────────────────────────────────┐
│ SELECTION DERIVATION: OVER 2.5 GOALS                         │
│ Match: Arsenal vs Chelsea (ID: 39-2026-8812)                 │
├──────────────────────────────────────────────────────────────┤
│ • Raw Simulation Prob:     56.1% (35,000 Monte Carlo Paths)  │
│ • Model Version:           dixon_coles_v1.2 (ident: sum=1)   │
│ • Calibration Applied:     Isotonic Regression v2.1          │
│ • Calibrated Prob:         54.8% [95% CI: 53.2% - 56.4%]     │
│ • Target Bookmaker:        1xBet Fixed Odds (Price: 2.12)    │
│ • Devigged Market Prob:    49.1% (Shin Method, Overround 4.2%)│
│ • Edge vs. 1xBet:          +5.7 percentage points            │
│ • Expected Value:          (0.548 * 2.12) - 1.0 = +16.18%    │
│ • Data Freshness:          State: 14s ago | Odds: 32s ago    │
│ • Lineup Verification:     Official Starting XIs Confirmed   │
│ • Gate Status:             PASSED (Min Edge: 3.0% | EV > 0)  │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Real-Time Data Integrity & Staleness Semantics

The interface strictly communicates actual backend conditions. Under no circumstances will the frontend synthesize or simulate live activity.

### Concrete State Presentations

1. **Unconnected Provider**:
   - *Incorrect*: "1xBet Verified Feed" (mocked boolean).
   - *Correct*: `1xBet Feed: Offline / Geoblocked` (Neutral Slate Badge).

2. **Unavailable Market Odds**:
   - *Incorrect*: Rendering synthetic 1.90 / 1.90 lines.
   - *Correct*: `1xBet Odds Unavailable` $\to$ Market card disabled with message: *"No active market clearing price. Predictive engine abstaining."*

3. **Stale Match State**:
   - *Incorrect*: Pulsing green "LIVE" badge when no heartbeat has occurred for 5 minutes.
   - *Correct*: `Live State Delayed (Last synced 4m 12s ago)` with amber warning border.

4. **Lineup Pending Countdown**:
   - *Incorrect*: Displaying unverified hypothetical lineups as starters.
   - *Correct*: `Lineups Pending • Expected ~19:00 IST` $\to$ Prediction tabs display: *"Quantitative analysis unlocks at T-60m upon official team sheet verification."*

5. **Decision Layer Abstention**:
   - *Incorrect*: Forcing a bet recommendation with low confidence.
   - *Correct*: Large neutral badge `NO BET` accompanied by explicit reason tags: `[EDGE_BELOW_THRESHOLD: +1.2% < 3.0%]` or `[SOURCE_CONFLICT]`.

---

## 7. Purposeful Visual & Charting Language

Charts must convey quantitative insight, never aesthetic decoration.

1. **In-Play Win Probability Drift**:
   - Area chart showing Home / Draw / Away win probabilities across elapsed minutes (0' to 90').
   - Vertical markers denote discrete high-impact events (Goal 24', Yellow Card 41', Red Card 68').
2. **Model vs. Market Divergence**:
   - Step line comparing 1xBet de-vigged implied probability against calibrated model probability over time.
   - Shaded band represents the 95% model credible interval. Edge is highlighted only when the market price falls outside this interval.
3. **Expected Goals (xG) & Momentum Progression**:
   - Stepped xG accumulation curve (Arsenal cumulative xG vs Chelsea cumulative xG).
   - Bar chart below displaying 5-minute rolling shot intensity.
4. **Reliability / Calibration Diagrams**:
   - 10-bin scatter plot comparing predicted probability bins against empirical observed win rates with reference $y = x$ perfect calibration line.

---

## 8. Current Frontend Component Audit & Replacement Matrix

The codebase currently contains several placeholder components that contradict the backend contracts or display mock states. They will be systematically replaced during Phase 11:

| Current Component File | Current Status & Flaw | Target Replacement Architecture |
| :--- | :--- | :--- |
| `src/app/matches/[id]/page.tsx` | Visual scaffold; tabs render empty containers or mock cards. | Rebuild as complete Sofascore-style match terminal with Tri-Column layout and analytical tabs. |
| `src/components/match/LiveStatePanel.tsx` | Renders hardcoded in-play mock stats. | Connect to Supabase `match_events` and `matches` table with live latency badges. |
| `src/components/match/OddsPanel.tsx` | Placeholder odds; claims 1xBet support with static numbers. | Bind directly to `odds_snapshots` with Shin devigging and market overround metrics. |
| `src/components/match/ModelPanel.tsx` | Static probability numbers without uncertainty bounds. | Bind to `model_predictions` with 95% CI, Monte Carlo standard error, and calibration version. |
| `src/components/match/MarketTable.tsx` | Hardcoded market rows with generic "Bet" buttons. | Institutional tabular matrix with calculated EV, Edge, and 10-point NO-BET failure taxonomy. |
| `src/components/dashboard/EngineStatus.tsx` | Reads local `.cache/api_quota.json` file. | Connect to Supabase `provider_usage` and `worker_runs` to reflect authoritative atomic quota state. |
| `src/components/dashboard/MixpanelKpiStrip.tsx` | Displays static unverified aggregate KPIs. | Dynamically compute 30-day realized paper P&L, Brier score, and CLV from `paper_bet_settlements`. |
| `src/app/providers/page.tsx` | Claims provider feeds are "Verified" using hardcoded booleans. | Real reachability indicator; displays actual latency, daily requests consumed, and error logs. |

---

## 9. Design System Primitives & Foundation

Before building application screens, Phase 11 will establish a unified UI component library in `src/components/ui/terminal/`:

- **Typography**:
  - Display / Headers: `Inter` or `Geist Sans` (Tracking: `-0.02em`).
  - Numbers, Odds, EV, Probabilities: `JetBrains Mono` or `Geist Mono` (Tabular figures enabled `font-mono tabular-nums`).
- **Color Semantics (Dark Terminal)**:
  - Background Base: `#080C14` (Deep obsidian slate).
  - Surface Elevated: `#0F172A` (Slate 900).
  - Surface Border: `#1E293B` (Slate 800) / `#334155` (Slate 700 on hover).
  - Primary Text: `#F8FAFC` (Slate 50).
  - Muted Text: `#94A3B8` (Slate 400).
  - Positive Value / Candidate Edge: `#10B981` (Muted emerald, not neon).
  - Warning / Lineup Pending / Stale: `#F59E0B` (Warm amber).
  - Error / Quota Limit / Negative EV: `#EF4444` (Muted rose).
  - Neutral / NO-BET: `#64748B` (Slate 500).
- **Layout Grid**: 12-column responsive desktop grid with collapsible sidebars and sticky match surveillance headers.
- **Timezone**: All timestamps formatted via shared client hook `useIST(kickoff_utc)` outputting `DD MMM YYYY, hh:mm A IST`.
