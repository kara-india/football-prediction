# MASTER DEVELOPMENT PLAN
# Football Prediction Intelligence Platform — Phased, Criticality-Driven Architecture

**Author**: Gemini 3.8 Flash High (Principal Planning & Architecture Agent)  
**Target Execution Agent**: Claude Sonnet 4.6 Thinking  
**Repository**: `https://github.com/kara-india/football-prediction.git`  
**Current Baseline Git SHA**: `4a7d8234873264b9bb477ca65987b5c234d62b88`  
**Date**: September 23, 2026  
**Status**: SPECIFICATION COMPLETE — READY FOR EXECUTION (`START DEVELOPMENT`)  
**Approved Design Reference**: **Sofascore football UX/information architecture, adapted into a premium football analytics terminal.**

---

## 1. Executive Summary

This Master Development Plan establishes the complete engineering, statistical, operational, and UX roadmap for the **Football Prediction Intelligence Platform**.

### 1.1 Core Mission
The platform is a personal, quantitative betting-intelligence system. It is **NOT** an LLM tipster or a heuristic sentiment aggregator. The numerical prediction engine is grounded strictly in mathematical and statistical modeling (bivariate Poisson/Dixon-Coles, dynamic Elo ratings, multi-dimensional EWMA form, negative binomial event counts, and path-dependent Monte Carlo simulation). The platform continuously evaluates competitive football fixtures, ingests market-clearing odds from target bookmaker **1xBet**, evaluates out-of-sample expected value ($\text{EV} = p \cdot o - 1$), computes standard errors and probability confidence intervals, enforces a rigorous **NO-BET / ABSTAIN** gate, logs all predictions immutably to a ledger, tracks paper bets, settles outcomes against closing odds, and continually learns from prediction errors via automated walk-forward validation and safe challenger promotion.

### 1.2 Non-Negotiable Operational & Design Constraints
1. **₹0.00 External Data Cost**: The platform must operate indefinitely within free tiers (API-Football free tier capped at 100 requests/day, open research datasets, historical football-data.co.uk archives, and Supabase free tier).
2. **Deterministic Anti-Fabrication Rule**: The system must never fabricate odds, fake health checks, generate synthetic probabilities, or simulate non-converged Monte Carlo paths. If data is absent or stale, the engine surfaces `NO_BET` with standard failure taxonomy (`ODDS_STALE`, `LINEUP_UNCONFIRMED`, `INSUFFICIENT_SAMPLE`).
3. **No Lookahead Invariant**: For any evaluation or backtest as-of timestamp $T$, all features, rosters, injuries, and odds must satisfy:
   $$\text{available\_at} \le T$$
4. **Approved Design Reference**: **Sofascore football UX/information architecture, adapted into a premium football analytics terminal**. The interface combines Sofascore's match-centric hierarchy and high information density with an institutional dark slate aesthetic (`#0B0F17`), clean SaaS typography, and transparent mathematical provenance. Sportsbook neon styling, gambling gamification, and decorative non-analytical charts are strictly forbidden.
5. **Authoritative Central State**: Supabase (PostgreSQL 17) is the single source of truth for all quotas, match fixtures, odds snapshots, features, predictions, settlements, and engine settings. Local filesystem caches (`.cache`, `request_budget.json`) are forbidden from holding authoritative state. The browser reads persisted backend state; zero browser polling loops are permitted.
6. **Core Learning Architecture**:
   $$\text{predict} \longrightarrow \text{observe} \longrightarrow \text{evaluate} \longrightarrow \text{learn} \longrightarrow \text{validate} \longrightarrow \text{promote} \longrightarrow \text{future prediction}$$
7. **Core Lineup Architecture**:
   $$\text{detect confirmed XI} \longrightarrow \text{rebuild features} \longrightarrow \text{rerun analysis} \longrightarrow \text{recalibrate} \longrightarrow \text{simulate} \longrightarrow \text{reconcile odds} \longrightarrow \text{apply NO-BET gate} \longrightarrow \text{persist immutable snapshot}$$

### 1.3 Continuous Learning & Lineup-Triggered Prediction Contract
Full specification documented in `docs/CONTINUAL_LEARNING_ARCHITECTURE.md`.
1. **Multi-Checkpoint Forecasting**: For every eligible match, the system creates versioned, immutable prediction checkpoints:
   - `INITIAL` ($T-48\text{h}$): Base team strength, historical form, early odds.
   - `LINEUP_CONFIRMED` (~$T-60\text{m}$): Triggered as a first-class system event when official 11 vs 11 team sheets arrive. Reruns model, recalibrates, resimulates, and logs Lineup Information Value ($\Delta p, \Delta \text{Brier}$).
   - `LINEUP_V2` (Optional): Captured if late team-sheet amendments occur.
   - `FINAL_PREMATCH` ($T-5\text{m}$): Closing line reconciliation.
   - `LIVE`: In-play continuous hazard states.
2. **Every Eligible Match**: Every allowlisted fixture is forecasted and stored, even when the final output is `NO_BET`, ensuring downstream learning datasets are free from selection bias.
3. **Decoupled Autonomous Execution**: The background engine continuously discovers, monitors lineups, recalculates predictions, settles matches, and updates challengers without requiring any browser session.
4. **Layered Learning Structure**:
   - *Layer 1 (Base Models)*: Dixon-Coles, Elo, count models (scheduled batch retraining).
   - *Layer 2 (Calibration)*: Brier, LogLoss, ECE tracking and temperature scaling.
   - *Layer 3 (Online Correction)*: Team and lineup residual adaptation with L2 shrinkage.
   - *Layer 4 (Decision Policy / RL)*: Contextual bandit selecting between `ABSTAIN` and market candidates, strictly subordinated to statistical safety gates.

---

## 2. Current Codebase Audit & Reality Classification

An exhaustive inspection of Git commit `ffcc8ac76294e57b24666306707941a935c51034` reveals that the repository is a **partially implemented research scaffold**. Many files contain stubbed methods, hard-coded assertions, or security vulnerabilities that contradict claims made in the documentation.

### 2.1 Module Classification Table

| Component / File | Current Classification | Reality & Critical Gaps |
| :--- | :--- | :--- |
| `README.md` | **Architecturally Unsafe** | Leaked active API-Football key (`073534...`). Claims models and workers are operational when workers are empty stubs. |
| `src/app/api/matches/live/route.ts` | **P0 Security Exposure** | Contains hardcoded API-Football key fallback on line 41. Bypasses central quota. |
| `src/app/api/matches/upcoming/route.ts` | **P0 Security Exposure** | Contains hardcoded API-Football key fallback on line 42. Bypasses central quota. |
| `python/requirements.txt` | **Missing / Broken CI** | File is absent in repository root and `python/`. Breaks clean virtual environments and CI workflows. |
| `.github/workflows/ci.yml` | **Architecturally Unsafe** | Swallows errors using `\|\| echo 'lint check done'` and `\|\| echo 'type check done'`. Failed builds appear green. |
| `supabase/migrations/` | **Migration Drift** | 4 migration files exist, but Supabase Postgres 17 has 27 active tables not fully mapped to git history. |
| Supabase RLS Policies | **Security Vulnerability** | Multiple sensitive tables (`model_predictions`, `paper_bets`, `learning_runs`) have `FOR ALL USING (true)`. |
| `src/lib/quotaGuard.ts` | **Architecturally Unsafe** | Manages quota via local `.cache/api_quota.json`. Not shared across serverless runtimes. |
| `python/adapters/api_football.py` | **Partially Implemented** | Good retry and parsing structure, but tracks quota locally in memory (`self.quota_remaining = 100`). |
| `python/adapters/odds_api_adapter.py` | **Stubbed / Fake** | Returns empty lists for odds. Claims `is_1xbet_confirmed=True` via hardcoded boolean without network calls. |
| `python/models/dixon_coles.py` | **Mathematically Unsafe** | Unstable optimization parameters; hardcoded decay parameter $\xi$; unregularized attack/defense parameters. |
| `python/models/elo.py` | **Partially Implemented** | Standard Elo functional, but lacks temporal K-factor optimization, margin weighting, or league hierarchy. |
| `python/models/form.py` | **Mathematically Unsafe** | Single global EWMA with fixed $\alpha=0.3$. Does not separate attacking, defensive, shot, or discipline form. |
| `python/models/count_models.py` | **Mathematically Unsafe** | Shares single global negative binomial parameter across cards, corners, and fouls. |
| `python/models/player_model.py` | **Stubbed / Leakage Risk** | Uses season aggregate rates ($\text{goals\_per\_90} \cdot \text{mins}$). Vulnerable to severe lookahead leakage. |
| `python/simulation/live_state_updater.py`| **Stubbed** | Methods like `parse_api_state()`, `is_state_stale()`, and `detect_significant_events()` return mocks. |
| `python/simulation/monte_carlo.py` | **Stubbed / Fake** | Fixed simulation loops, hardcoded standard error ($0.0$), dummy convergence check. No card/corner hazards. |
| `python/simulation/vectorized_mc.py` | **Partially Implemented** | Partial vectorization; incomplete state transitions and market extraction. |
| `python/calibration/calibrator.py` | **Partially Implemented** | Basic isotonic regression present, but fits on same training fold. Missing Platt, Beta, and ECE tracking. |
| `python/backtesting/walk_forward.py` | **Stubbed / Fake Metrics** | Hardcoded return values: `brier: 0.1`, `log_loss: 0.2`, `p_value: 0.04`, `winner: challenger`. |
| `python/workers/collector_worker.py` | **Stubbed** | Method bodies consist of `pass`. Zero ingestion functionality. |
| `python/workers/evaluator_worker.py` | **Stubbed** | Method bodies consist of `pass`. Zero prediction settlement or error classification. |
| `python/workers/learner_worker.py` | **Stubbed** | Method bodies consist of `pass`. Zero parameter updates or champion comparison. |
| `src/app/matches/[id]/page.tsx` | **Placeholder UI** | Visual tabs exist, but `MarketTable`, `OddsPanel`, and `ModelPanel` render mock or empty components. |

---

## 3. Contradiction Resolution Matrix

| Contradiction Identified | Source of Contradiction | Resolution & Single Source of Truth |
| :--- | :--- | :--- |
| **API Key Hardcoding vs Env Security** | `README.md` & Next.js routes contain raw key `073534...` | Rotate key immediately. Enforce `process.env.API_FOOTBALL_KEY` server-side only. Zero fallback. Fail loudly with 500 if unset. |
| **Worker Automation vs Empty Stubs** | Docs state workers run every 15m; code has `pass` | Acknowledge workers are unbuilt. Build concrete CLI commands and orchestrators in Phase 9. |
| **1xBet Support vs Stub Adapter** | UI claims 1xBet verified; adapter returns `[]` | Never return synthetic odds. Surface `1XBET ODDS UNAVAILABLE` and trigger `NO_BET` until a verified zero-cost feed is connected. |
| **Quota State Fragmentation** | `.cache/api_quota.json` vs Python memory vs Supabase | Supabase `provider_usage` table is the sole source of truth. Implement atomic quota reservation via PostgreSQL function `reserve_api_quota()`. |
| **Backtester Reality vs Fake Metrics** | `walk_forward.py` hardcodes `brier: 0.1` | Completely excise fake metrics. Build real temporal cross-validation with true out-of-sample Brier, Log Loss, and CLV. |
| **Lookahead Leakage vs Player Stats** | `player_model.py` uses season aggregate stats | Enforce temporal point-in-time snapshotting. Player stats must be computed strictly as of kickoff timestamp $T$. |
| **Sportsbook UI vs Institutional Terminal** | Traditional green "Bet" buttons & gambling jargon | Transition to Sofascore-style quantitative terminal: show Model vs Market delta, EV, 95% CI, and NO-BET reasons. |

---

## 4. Prioritization Taxonomy (P0 / P1 / P2 / P3)

The platform must be implemented strictly following this criticality hierarchy. No P1 or P2 feature may be tackled while P0 defects exist.

```mermaid
graph TD
    P0["P0: Security, Dependencies, Quota, Data Contracts & Anti-Fabrication"] --> P1["P1: Core Ingestion, Replay, Statistical Models, Calibration & NO-BET"]
    P1 --> P2["P2: Production Workers, Evaluation, Sofascore Terminal UI & Champion/Challenger"]
    P2 --> P3["P3: Reinforcement Learning, Contextual Bandits & Advanced Research"]
```

### P0 — Stop-The-Line Foundations
- **Security & Secret Scrubbing**: Rotate compromised credentials; purge hardcoded fallbacks; enforce server-only service role keys.
- **Reproducible Python Runtime**: Pinned `python/requirements.txt` and `python/requirements-dev.txt`.
- **CI Integrity**: Eliminate `|| echo 'done'`; enforce hard failure on lint, type, and test regressions.
- **Supabase Baseline Reconciliation**: Unify migrations 001–004 with Postgres 17 catalog; lock down RLS on sensitive prediction/learning tables.
- **Unified Quota Governance**: Atomic PostgreSQL quota reservation; strict daily cap of 95 requests (50 reserved for user manual queries, 45 for workers).
- **Anti-Fabrication & Data Contracts**: Enforce canonical schemas (`CanonicalMatch`, `CanonicalOddsMarket`, etc.); purge all synthetic mock data.

### P1 — Core Engine & Trustworthy Vertical Slice
- **Data Ingestion**: Zero-cost historical ingestion (13,403 matches + football-data.co.uk past 5 years); bulk API-Football fixture discovery.
- **1xBet Provider Research & Normalization**: Real reachability tests; strict odds normalization; fallback to `ODDS_UNAVAILABLE`.
- **Historical Replay Framework**: Point-in-time state reconstruction as-of minute $T$; strict $\text{available\_at} \le T$ invariant.
- **Statistical Model Stack**: Hardened Dixon-Coles (identifiability, decay $\xi$, home advantage); calibrated Elo; multi-dimensional EWMA form; negative binomial count models.
- **First Vertical Slice**: Full end-to-end execution of **Over/Under 2.5 Goals** market (features $\to$ model $\to$ calibration $\to$ 1xBet EV $\to$ NO-BET $\to$ prediction $\to$ settlement $\to$ Brier).
- **Rigorous Calibration**: Out-of-sample Isotonic and Platt scaling; ECE calculation; reliability diagrams.
- **Standardized NO-BET Gate**: 10-point standard taxonomy (`NEGATIVE_EV`, `LINEUP_UNCONFIRMED`, `ODDS_STALE`, etc.).

### P2 — Production Intelligence, Workers & Sofascore UI
- **Live Path-Dependent Monte Carlo**: Vectorized competing event hazards; true convergence with standard error tracking; in-play score-state transitions.
- **Player & Specialist Markets**: Anytime goalscorer; assist models; cards and corners distributions with shrinkage for sparse data.
- **Background Worker Automation**: Discovery, live state updater, odds collector, prediction runner, evaluator, and learner workers.
- **Prediction Ledger & Settlement**: Immutable prediction storage; automated settlement upon FT; CLV tracking; error taxonomy classification.
- **Champion / Challenger Framework**: Supabase model registry; out-of-sample promotion gates based on Brier, ECE, and CLV.
- **Sofascore-Inspired Terminal UI**: Full match-centric architecture, Tri-Column Match Detail, momentum timeline, pitch lineup grid, and complete mathematical transparency.

### P3 — Adaptive Learning & Advanced Research
- **Contextual Bandit / RL Policy**: Off-policy evaluation on settled predictions; reward based on realized paper P&L and CLV; strict guardrails against exploration instability.
- **Counterfactual Logging**: Tracking unselected actions to assess opportunity cost of abstention.

---

## 5. End-to-End System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   NEXT.JS 14 QUANTITATIVE TERMINAL                      │
│   (Sofascore Architecture • Dark Slate Palette • IST Timings • No-Bet)  │
│   • Watchlist / Dashboard  • Match Detail (Tri-Column)  • Model Ledger  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTPS / Server Actions
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS SERVER / API ROUTES                      │
│   • Read-Only Analytics APIs  • User-Reserved On-Demand Analysis (50 req)│
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Service Role / Session Token
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       SUPABASE (POSTGRESQL 17)                          │
│   • Canonical Fixtures & Rosters  • Historical Odds (1xBet)             │
│   • Point-in-Time Features        • Immutable Prediction Ledger         │
│   • Paper-Bet Settlement Ledger   • Model Registry (Champion/Challenger)│
│   • Atomic Quota Governor (PL/pgSQL reserve_api_quota function)         │
└────────────────────────────────────▲────────────────────────────────────┘
                                     │
      ┌──────────────────────────────┴──────────────────────────────┐
      │                                                             │
┌─────┴───────────────────────────────┐     ┌───────────────────────┴─────┐
│      PYTHON INGESTION & WORKERS     │     │   PYTHON PREDICTION ENGINE  │
│ • Discovery Worker (Bulk Fixtures)  │     │ • Feature Store (No-Look)   │
│ • Lineup Watcher (T-60m Gatekeeper) │     │ • Dixon-Coles + Dynamic Elo │
│ • 1xBet Odds Scraper / API Adapter  │     │ • Multi-Dimensional Form    │
│ • Settlement & Evaluator Worker     │     │ • Vectorized Monte Carlo    │
│ • Automated Learner & Promoted Reg  │     │ • Calibration & NO-BET Gate │
└─────▲───────────────────────────────┘     └─────────────────────────────┘
      │
      ├──────────────────────────────┬──────────────────────────────┐
      ▼                              ▼                              ▼
┌───────────────┐              ┌───────────────┐              ┌───────────┐
│  API-FOOTBALL │              │ 1xBET ENGINE  │              │ OPEN DATA │
│ (Max 45/day)  │              │ (Target Book) │              │ (Past 5Y) │
└───────────────┘              └───────────────┘              └───────────┘
```

---

## 6. Phased Implementation Roadmap (Phase 0 to Phase 12)

```mermaid
gantt
    title Platform Implementation Sequence
    dateFormat  YYYY-MM-DD
    section P0 Foundation
    Phase 00: Security & Repo Hardening      :p0, 2026-09-24, 1d
    Phase 01: Database & Migration Hardening :p1, after p0, 2d
    Phase 02: Quota Governance & Cost Safety  :p2, after p1, 1d
    section P1 Core Engine
    Phase 03: Zero-Cost Data Ingestion       :p3, after p2, 2d
    Phase 04: Target Odds (1xBet) Engine     :p4, after p3, 2d
    Phase 05: Lineup & Runtime Gatekeeper    :p5, after p4, 1d
    Phase 06: Core Statistical & Monte Carlo :p6, after p5, 3d
    Phase 07: Market Settlement & Edge Engine:p7, after p6, 2d
    Phase 08: Walk-Forward Validation        :p8, after p7, 2d
    section P2 Operations & Sofascore UI
    Phase 09: Background Worker Automation   :p9, after p8, 2d
    Phase 10: Production Hardening & Observ. :p10, after p9, 2d
    Phase 11: Sofascore-Inspired Terminal UI :p11, after p10, 2d
    section P3 Active Learning
    Phase 12: RL & Contextual Bandit Policy  :p12, after p11, 3d
```

---

## 7. Frontend Information Architecture & Terminal UX Reference (Sofascore Integration)

> **Approved Design Reference Directive**:  
> **"Approved design reference: Sofascore football UX/information architecture, adapted into a premium football analytics terminal."**

### 7.1 Target Navigation Hierarchy
```
FOOTBALL ANALYTICS TERMINAL
├── Dashboard (Watchlist • Live Matches • Upcoming Matches • Model Signals)
├── Calendar & Fixtures (Historical Exploration • Next 7 Days • Registry Filter)
├── Match Detail (Primary Product Experience):
│   ├── Match Header (Teams, score, elapsed minute, IST kickoff, venue, referee)
│   ├── Model Consensus Probability (Home / Draw / Away calibrated win curves)
│   ├── Tri-Column Intelligence Matrix (Model vs. 1xBet Market vs. In-Play State)
│   ├── Probability & Momentum Timeline (Time-series drift 0' to 90')
│   └── Tabular Drill-Downs:
│       ├── Overview (H2H, Form EWMA, league context)
│       ├── Model (Poisson marginals, Dixon-Coles parameters, identifiability)
│       ├── Live State (Possession, xG, shot intensity, card hazard)
│       ├── Odds History (1xBet price ticks, margin evolution, CLV)
│       ├── Lineups (Confirmed starting XIs, tactical pitch grid, substitutes)
│       ├── Simulation (Monte Carlo path distributions, standard error convergence)
│       └── Settlement (Post-match settlement, closing line, error classification)
├── Models & Calibration (Registry • Isotonic / Platt Curves • ECE Reliability)
├── Backtesting & Replay (Walk-Forward Temporal Matrix • Brier • ROI • Drawdown)
├── Prediction & Paper Ledger (Settled Predictions • Open Paper Positions)
└── System Health (API Quota Meter: 50 User / 45 Worker / 5 Buffer • Feeds)
```

### 7.2 Two-Tier Information Density
- **Level 1 — Rapid Scanning (5-Second Scan)**: Matchday surveillance answering: What matches matter? Which are live? What does the model estimate? What markets diverge from 1xBet prices? Which matches have unconfirmed lineups or stale odds?
- **Level 2 — Deep Analytical Drill-Down (Progressive Disclosure)**: Comprehensive model decomposition exposing raw simulation counts, calibration versions, credible intervals, standard errors, tactical pitch formations, and source timestamps.

### 7.3 Model Transparency Card (Mandatory Specification)
Every prediction card must expose its mathematical derivation without inventing numbers:
```
OVER 2.5 GOALS
• Model Calibrated Prob:     54.8% [95% CI: 53.2% — 56.4%]
• Market Implied (1xBet):    47.2% (Decimal: 2.12)
• Devigged Fair Market:      49.1% (Shin Method, Overround 4.2%)
• Model-Market Divergence:   +5.7 percentage points
• Expected Value (EV):       +16.18%
• Calibration Version:       Isotonic Regression v2.1
• Simulation Paths:          35,000 (Standard Error: ±0.003)
• Data Freshness:            State: 14s ago | Odds: 32s ago
• Decision:                  CANDIDATE (Min Edge: 3.0% | Lineups Confirmed)
```

### 7.4 Real-Time State Integrity & Staleness Rules
- If odds are missing $\to$ Display `1xBet Odds Unavailable` (Never fabricate numbers).
- If provider is unverified $\to$ Display `Provider Offline` (Never claim "Verified Feed").
- If live match has no heartbeat for $> 120\text{s}$ $\to$ Display `Live Data Stale (Last update 3m 42s ago)`.
- If lineup is unannounced $\to$ Display `Lineups Pending • Expected ~T-60m` and attach `NO_BET: LINEUP_UNCONFIRMED`.

---

## 8. Quota Governance & Cost Safety Architecture

To guarantee strictly **₹0.00 external data cost**, the platform implements a multi-tier defense:

```mermaid
flowchart TD
    Req[Incoming Ingestion / Analysis Request] --> Check{Caller Type?}
    Check -- "Automated Background Worker" --> WorkerBudget{Worker Quota Available?<br/>Max 45/day}
    Check -- "User On-Demand Query" --> UserBudget{User Quota Available?<br/>Reserved 50/day}
    WorkerBudget -- Yes --> Reserve[Atomic PL/pgSQL Reservation]
    WorkerBudget -- No --> Abstain[Worker Sleeps / Skips Deep Fetch]
    UserBudget -- Yes --> Reserve
    UserBudget -- No --> Surface[UI: Daily Quota Exhausted, Refresh at 00:00 UTC]
    Reserve --> Exec[Execute Provider API Call]
    Exec --> Settle[Record Response Status & Quota Consumed]
```

### 8.1 Daily Request Allocation (100 Free Tier API-Football)
- **User On-Demand Reserve**: 50 requests/day. Dedicated strictly to interactive user actions on the web client (manual match analysis, latest odds refresh).
- **Background Worker Budget**: 45 requests/day. Dedicated to bulk discovery (1 req), T-60m lineup polling (~25 req), and live state checks (~19 req).
- **Hard Safety Buffer**: 5 requests/day. Never consumed under any circumstances; prevents accidental overage fees.

---

## 9. Mathematical & Statistical Engine Roadmap

### 9.1 First Vertical Slice: Over/Under 2.5 Goals
To ensure end-to-end mathematical rigor before expanding across all 9 markets, the platform will implement a single vertical slice:
1. **Data**: 5 years of historical goal counts per team (home/away splits).
2. **Features**: Point-in-time attack rating, defense rating, EWMA goal form, rest days.
3. **Model**: Bivariate Poisson model with Dixon-Coles low-score correction parameter $\tau$:
   $$P(X=x, Y=y) = \tau_{\lambda, \mu}(x, y) \frac{\lambda^x e^{-\lambda}}{x!} \frac{\mu^y e^{-\mu}}{y!}$$
   Subject to identifiability constraint: $\frac{1}{N}\sum_{i=1}^N \alpha_i = 1$.
4. **Calibration**: Isotonic regression trained strictly on preceding temporal validation window.
5. **Odds & EV**: Ingest 1xBet Over/Under 2.5 lines; remove margin; compute $\text{EV} = p \cdot o_{1\text{xbet}} - 1$.
6. **Decision**: Enforce edge threshold ($\ge 3\%$) and NO-BET checks.
7. **Settlement**: Automated validation against actual scorelines; calculate Brier score and CLV.

### 9.2 Expansion Markets
Once the vertical slice is validated, the same architecture expands to:
- Wave 2: Match 1X2, Both Teams To Score (BTTS), Over/Under 1.5, 3.5, 4.5.
- Wave 3: Total Cards (Negative Binomial), Team Cards, Next Goal (In-Play Hazard).
- Wave 4: Anytime Goalscorer, Player Assists (Hierarchical Poisson with player minutes expectation).

---

## 10. Operational Protocol for Antigravity & Claude

When the user enters **`START DEVELOPMENT`**, the executing agent (Claude Sonnet 4.6 Thinking) must execute the following deterministic protocol:

1. **Load State**: Read `docs/MASTER_DEVELOPMENT_PLAN.md`, `docs/FRONTEND_DESIGN_DIRECTION.md`, and `docs/PHASE_STATUS.md`.
2. **Verify Environment**: Inspect git status and Supabase connectivity. Verify current git commit against `LAST_VERIFIED_GIT_SHA`.
3. **Target Earliest Incomplete Phase**: Identify the first phase with status `PENDING` or `IN_PROGRESS` (Phase 0).
4. **Inspect Phase Document**: Read `docs/phases/phase_XX_...md`.
5. **Parallel Agent Execution**: For parallelizable subtasks within that phase, spawn dedicated subagents.
6. **Run Phase Tests**: Execute the mandated automated test suite.
7. **Commit & Push**: Commit with standard semantic prefix (`feat(phase-XX): ...`).
8. **Surface Manual Steps**: Display the exact manual instructions from `docs/DEPLOYMENT_MANUAL_STEPS.md`.
9. **Pause at Phase Boundary**: If manual actions (e.g., API key rotation) are required, halt and await user confirmation. Never proceed blindly past unfulfilled prerequisites.

---

## 11. Traceability Invariant

Every prediction output by this platform must satisfy full end-to-end auditability:

$$\begin{aligned}
\text{Raw Data} &\longrightarrow \text{Point-in-Time Features } (\text{available\_at} \le T) \\
&\longrightarrow \text{Statistical Model } (\text{Versioned Parameters}) \\
&\longrightarrow \text{Out-of-Sample Calibration } (\text{Isotonic / Platt}) \\
&\longrightarrow \text{1xBet Real Odds } (\text{Timestamped Snapshot}) \\
&\longrightarrow \text{Expected Value Calculation } (\text{EV} = p \cdot o - 1) \\
&\longrightarrow \text{NO-BET Evaluation } (\text{10-Point Taxonomy Gate}) \\
&\longrightarrow \text{Immutable Prediction Record} \\
&\longrightarrow \text{Post-Match Settlement } (\text{CLV \& P\&L Calculation}) \\
&\longrightarrow \text{Error Classification \& Walk-Forward Retraining}
\end{aligned}$$
