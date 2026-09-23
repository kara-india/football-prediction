# SYSTEM ARCHITECTURE & COMPONENT SPECIFICATION
# Football Prediction Intelligence Platform

**Primary Architecture Target**: High-Throughput Quantitative Prediction Terminal  
**Approved UX Reference**: Sofascore Football Information Architecture + Institutional Dark Slate Terminal  
**Database**: Supabase (PostgreSQL 17)  
**Target Bookmaker**: 1xBet Fixed Odds  
**Operational Cost**: Strictly ₹0.00 External Data Cost  

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NEXT.JS 14 WEB APPLICATION                           │
│   (Sofascore Football IA • Dark Slate Theme • IST Timings • Institutional)  │
│   • Matchday Command Center (Live, Watchlist, Upcoming, Model Signals)      │
│   • Match Detail Terminal (Tri-Column Matrix: Model vs Market vs In-Play)   │
│   • Model Registry, Backtest Explorer & Settled Paper-Bet Ledger            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS / Read-Only Client Queries
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NEXT.JS SERVER LAYER                               │
│   • Read-Only Analytics APIs (`/api/matches`, `/api/predictions`)            │
│   • On-Demand Match Intelligence Refresh (`POST /api/matches/[id]/refresh`)  │
│   • Central Quota Verification (Consumes from 50-Request User Pool)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Service Role Connection
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SUPABASE (POSTGRESQL 17)                              │
│   • Canonical Schema (competitions, matches, lineups, match_events)         │
│   • Target Odds Snapshots (1xBet prices, devigged probs, margins)           │
│   • Immutable Prediction Ledger (model_predictions, paper_bets)             │
│   • Settlement & Learning State (prediction_results, prediction_errors)     │
│   • Atomic Quota Governor (Stored Procedure: reserve_api_quota)             │
│   • Row-Level Security: Strict Public Read / Privileged Server Write       │
└──────────────────────────────────────▲──────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┴─────────────────────────────┐
         │                                                           │
┌────────┴─────────────────────────────┐     ┌───────────────────────┴────────┐
│     PYTHON INGESTION & WORKERS       │     │    PYTHON ANALYTICAL ENGINE    │
│ • Daily Bulk Discovery (04:00 UTC)   │     │ • Point-in-Time Feature Store  │
│ • Lineup Watcher (T-60m Gatekeeper)  │     │ • Identifiable Dixon-Coles     │
│ • 1xBet Odds Scraper / API Adapter   │     │ • Multi-Dimensional EWMA Form  │
│ • Evaluator & Error Classifier       │     │ • Vectorized Hazard Simulation │
│ • Automated Challenger Retraining    │     │ • Out-of-Sample Calibration    │
│ • Unified Runner (`workers.runner`)  │     │ • 10-Point NO-BET Gatekeeper   │
└────────▲─────────────────────────────┘     └────────────────────────────────┘
         │
         ├─────────────────────────────┬─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐          ┌──────────────────┐          ┌─────────────────┐
│   API-FOOTBALL   │          │   1xBET ENGINE   │          │    OPEN DATA    │
│ (Max 45 req/day) │          │  (Target Book)   │          │  (5-Year CSVs)  │
└──────────────────┘          └──────────────────┘          └─────────────────┘
```

---

## 2. Information Architecture & UX Hierarchy (Sofascore Integration)

> **Approved Design Reference Directive**:  
> **"Approved design reference: Sofascore football UX/information architecture, adapted into a premium football analytics terminal."**

### 2.1 Navigation Architecture
- **Dashboard**:
  - *Watchlist*: High-priority tracked fixtures.
  - *Live Matches*: Real-time score, minute, momentum, and card intensity.
  - *Upcoming Matches*: Allowlist leagues, countdown to T-60m lineup confirmation.
  - *Model Signals*: Fixtures exhibiting significant model vs. market divergence.
- **Calendar**: Past 7-day result exploration and upcoming 7-day fixture roadmap.
- **Match Detail (Institutional Centerpiece)**:
  - *Match Header*: Canonical competition, team badges, score, status, IST kickoff, referee, venue.
  - *Consensus Probability Bar*: Calibrated win/draw/loss distribution with credible intervals.
  - *Tri-Column Matrix*:
    - **Model Intelligence**: Calibrated probabilities, simulation count, standard error.
    - **Market (1xBet)**: Current price, implied probability, devigged fair price, EV, value edge.
    - **Live State**: Score, minute, xG progression, shots on target, red cards, state latency.
  - *Probability & Momentum Timeline*: Time-series showing in-play win probability drift ($0'$ to $90'$).
  - *Drill-Down Tabs*: Overview, Model Parameters, Live State, Odds History, Lineups (Pitch Grid), Monte Carlo Distribution, and Settlement Audit.
- **Models & Calibration**: Registry of active Champion models, parameter diagnostics, and reliability curves.
- **Backtesting Explorer**: Out-of-sample walk-forward evaluation across temporal folds.
- **Prediction Ledger**: Immutable audit log of all predictions, paper stakes, closing line value (CLV), and realized profit/loss.
- **System Health**: Central quota meter (User 50 / Worker 45 / Buffer 5) and worker execution logs.

---

## 3. Data Integrity & Anti-Fabrication Principles

1. **No Synthetic Data**: The platform never fabricates odds, health flags, or simulation metrics. If a bookmaker line or live feed is absent, the engine surfaces `NO_BET` with standard failure taxonomy (`ODDS_UNAVAILABLE`, `LINEUP_UNCONFIRMED`, `INSUFFICIENT_SAMPLE`).
2. **Point-in-Time Provenance**: Every feature carries an `available_at` timestamp. In all historical backtests and live evaluations, no data generated after time $T$ may enter the feature vector:
   $$\text{available\_at} \le T$$
3. **Decoupled Architecture**: The backend engine runs autonomously in Python and writes to Supabase. The Next.js frontend reads persisted state and does not run continuous polling loops.
4. **Authoritative Quota Governance**: API-Football credits are strictly capped at 95/day via atomic PostgreSQL row locking (`reserve_api_quota`), ensuring ₹0 external data cost.

---

## 4. Continual Learning & Multi-Checkpoint Lifecycle

The platform implements an autonomous, prequential intelligence lifecycle (predict → observe → evaluate → learn → validate → promote → future prediction). Full specification is documented in `docs/CONTINUAL_LEARNING_ARCHITECTURE.md`.

### 4.1 Multi-Checkpoint Forecasting
Every eligible match produces immutable, versioned prediction checkpoints:
- **Checkpoint A (`INITIAL`)**: Generated at $T-48\text{h}$ from team strength, form, historical data, and early odds.
- **Checkpoint B (`LINEUP_CONFIRMED` / `LINEUP_V1`)**: Triggered immediately upon receipt and verification of official 11 vs 11 starting lineups (~$T-60\text{m}$). Reruns full feature generation, Dixon-Coles model, recalibration, and 10,000-path Monte Carlo.
- **Checkpoint B2 (`LINEUP_V2`)**: Versioned revision snapshot created if official starting XI changes before kickoff (e.g., warm-up injury).
- **Checkpoint C (`FINAL_PREMATCH`)**: Generated at $T-5\text{m}$ reconciling closing odds and final line movements.
- **Checkpoint D (`LIVE`)**: In-play state snapshots triggered by match events.

### 4.2 Lineup Trigger Event Loop
```text
LINEUP_NOT_FOUND → LINEUP_DETECTED → LINEUP_VALIDATED → LINEUP_CHANGED
       ↓
LINEUP_FEATURES_REBUILT → MODEL_RECALCULATED → CALIBRATION_APPLIED
       ↓
SIMULATION_EXECUTED → ODDS_RECONCILED → EV_CALCULATED → NO_BET_GATE
       ↓
PREDICTION_SNAPSHOT_STORED
```

### 4.3 Quota-Aware Targeted Lineup Polling
- Polling is restricted strictly to fixtures inside the prediction horizon entering the $[T-60\text{m}, T-40\text{m}]$ window.
- Polling halts immediately once 11 vs 11 starters are confirmed, preserving the daily 45-call worker budget.

---

## 5. Layered Learning Hierarchy & RL Subordination

Learning is strictly partitioned into 4 layers to prevent unconstrained model degradation:
- **Layer 1: Base Statistical Models** (Dixon-Coles, Elo, Poisson/Negative Binomial): Retrained on scheduled batches or major dataset updates.
- **Layer 2: Calibration & Uncertainty Monitoring** (Isotonic regression, Platt scaling, Brier/ECE tracking): Continuous rolling window evaluation.
- **Layer 3: Online Residual & Drift Correction** (Recent team adjustments, lineup impacts): Regularized fast adaptation with shrinkage.
- **Layer 4: Contextual Bandit / RL Decision Policy** (Action selection: `ABSTAIN`, `BET`): Determines staking and market participation.

> [!IMPORTANT]
> **RL Subordination Principle**: Reinforcement learning never overrides statistical safety or data quality gates. If any gate fails (`LINEUP_UNCONFIRMED`, `ODDS_STALE`, `INSUFFICIENT_DATA`), the platform strictly outputs `NO_BET` regardless of policy action propensity.

