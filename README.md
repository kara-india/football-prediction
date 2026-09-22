<div align="center">

```
███████╗ ██████╗  ██████╗ ████████╗██████╗  █████╗ ██╗     ██╗
██╔════╝██╔═══██╗██╔═══██╗╚══██╔══╝██╔══██╗██╔══██╗██║     ██║
█████╗  ██║   ██║██║   ██║   ██║   ██████╔╝███████║██║     ██║
██╔══╝  ██║   ██║██║   ██║   ██║   ██╔══██╗██╔══██║██║     ██║
██║     ╚██████╔╝╚██████╔╝   ██║   ██████╔╝██║  ██║███████╗███████╗
╚═╝      ╚═════╝  ╚═════╝    ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
```

# ⚽ Football Prediction Intelligence Platform

**A production-quality statistical betting-intelligence system for 1xBet markets.**  
*Probabilities from math. Decisions from evidence. Bets from discipline.*

[![CI](https://github.com/kara-india/football-prediction/actions/workflows/ci.yml/badge.svg)](https://github.com/kara-india/football-prediction/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-97%20passed-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#)

</div>

---

> **This is NOT a tipster service.**  
> This is a personal analytical engine that applies statistical modelling, Monte Carlo simulation, and rigorous calibration to identify 1xBet prices where the model has a measurable, evidence-based edge — and stays silent when it doesn't.

---

## 🧠 Philosophy

Most football betting tools fail for one of three reasons:

1. They confuse **hit rate** with **edge** — winning 55% of bets at 1.80 odds is still a loss.
2. They let an algorithm (or human) **manually assign weights** to features with no empirical grounding.
3. They **force a recommendation** even when the data is incomplete, the odds are stale, or the model is uncertain.

This system is built to avoid all three.

| ❌ What this system never does | ✅ What it does instead |
|---|---|
| Assign arbitrary feature weights | Derive all weights from walk-forward validated data |
| Claim a bet is "guaranteed" or "safe" | Say **NO BET** when evidence is insufficient |
| Use LLM to invent probabilities | LLM explains results only — math produces probabilities |
| Treat bookmaker odds as truth | Measure model vs. market, calibrate, then decide |
| Use one good day as validation | Track Brier score, log loss, ECE, CLV, ROI over hundreds of predictions |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS DASHBOARD                            │
│  Live Matches │ Upcoming (lineup confirmed) │ Predictions │ Analytics│
└───────────────────────────┬─────────────────────────────────────────┘
                            │ API Routes
┌───────────────────────────▼─────────────────────────────────────────┐
│                      SUPABASE (PostgreSQL)                          │
│  27 tables · RLS policies · Real-time snapshots · Paper bet ledger  │
└──────┬──────────────────────────────────────────┬───────────────────┘
       │                                          │
┌──────▼──────────┐                    ┌──────────▼──────────────────┐
│  DATA PROVIDERS │                    │     PYTHON ENGINE           │
│                 │                    │                             │
│ API-Football    │                    │ ┌─ Elo Rating System        │
│ (1xBet odds)    │──── ingestion ────▶│ ├─ Dixon-Coles Poisson      │
│                 │                    │ ├─ Neg. Binomial (counts)   │
│ football-data   │                    │ ├─ Hierarchical Player Model│
│ .co.uk (free)   │                    │ ├─ Monte Carlo Simulator    │
│                 │                    │ ├─ Probability Calibration  │
│ StatsBomb Open  │                    │ ├─ EV Calculator            │
│ Data (free)     │                    │ └─ NO-BET Gate              │
└─────────────────┘                    └──────────────────────────────┘
                                                    │
┌───────────────────────────────────────────────────▼─────────────────┐
│                    GITHUB ACTIONS (free compute)                    │
│  Collector (15min) │ Evaluator (daily) │ Learner (weekly)           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Core Components

### 📐 Statistical Models

| Model | Purpose |
|-------|---------|
| **ELO Rating** | Team strength baseline, home advantage |
| **Dixon-Coles** | Bivariate Poisson with score-dependency correction (τ) |
| **Negative Binomial** | Cards, corners, fouls (over-dispersed counts) |
| **Hierarchical Player Model** | Anytime goalscorer / assist probabilities — Poisson, minutes-adjusted, shrinkage to team mean |
| **EWMA Form** | Exponentially-weighted recent form — no arbitrary "last N" lookback |
| **Market Anchor** | Compares de-vigged 1xBet implied probability vs. raw model probability |

### 🎲 Monte Carlo Engine

The simulator is **stateful and path-dependent**. It does not linearly extrapolate the current scoring rate.

```
Current State: 0-2 at 75'  ──▶  Sims: 50,000+  ──▶  Distribution over all outcomes
Current State: 2-0 at 75'  ──▶  Sims: 50,000+  ──▶  Completely different distribution
```

- Adaptive convergence: runs until standard error < 0.005 (max 500,000 sims)
- Score-state dependent intensities (teams losing press harder; red cards reduce attack)
- Reproducible seeds for debugging and audit

### 🚦 NO-BET Gate

**15 explicit rejection reasons.** A candidate must pass all of them:

```
INSUFFICIENT_DATA    STALE_ODDS          STALE_STATE
MODEL_UNCALIBRATED   HIGH_UNCERTAINTY    LOW_SAMPLE
MARKET_SUSPENDED     LINEUP_UNCONFIRMED  PLAYER_UNCERTAIN
EDGE_TOO_SMALL       SIMULATION_UNSTABLE SOURCE_CONFLICT
PROVIDER_FAILURE     NEGATIVE_EV         ODDS_TOO_LOW
```

The system strongly prefers **NO BET** over forcing a recommendation.

### 📊 Calibration

A model that wins 60% of bets at 60% predicted probability is not calibrated — it's just right.  
A model where **every predicted 60% event occurs 60% of the time** is calibrated.

Tracked metrics for every market and model version:

- **Brier Score** — mean squared error of probabilities
- **Log Loss** — information-theoretic sharpness
- **ECE** — Expected Calibration Error (reliability by bucket)
- **CLV** — Closing Line Value (were we ahead of the market?)
- **ROI** — paper P&L per unit staked

---

## 🗓️ Competition Universe

**12 domestic leagues** (EPL, Serie A, La Liga, Bundesliga, Ligue 1, Primeira Liga, Eredivisie, Serie A Brasil, Liga Profesional, Belgian First A)  
**2 European cups** (Champions League, Europa League)  
**Senior men's internationals** (World Cup, Euros, Nations League, Copa América, AFCON, AFC Asian Cup, CONCACAF, qualifiers, friendlies)

> Women's football, U23/U21/U19, reserve teams, and non-allowlisted competitions are **automatically excluded**.

---

## 🎯 Supported 1xBet Markets (initial)

`1X2` · `Double Chance` · `Over/Under 1.5/2.5/3.5/4.5` · `BTTS` · `Next Goal` · `Total Cards` · `Team Cards` · `Anytime Goalscorer` · `Player Assist`

Architecture supports future: `Asian Handicap` · `Corners` · `Fouls` · `Offsides` · `Player Shots` · `First-half markets`

---

## 🤖 Reinforcement Learning (disabled in V1)

A **LinUCB contextual bandit** sits at the decision layer, learning *when to act* — not *what probability to assign*.

```
RL layer learns:  WHEN TO BET / WHEN TO ABSTAIN
RL layer never:   Sets goal probabilities · Overrides NO-BET gate → BET
Activates when:   rl_enabled = true  AND  settled_bets ≥ 500
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Database | Supabase (PostgreSQL) with RLS |
| Python Engine | FastAPI, NumPy, SciPy, Pandas, scikit-learn, XGBoost |
| Scheduling | GitHub Actions (free tier) |
| Primary data | API-Football free tier + football-data.co.uk + StatsBomb Open |
| Odds target | 1xBet (via API-Football bookmaker_id=6) |

---

## 🚀 Quick Start

### Prerequisites

- Node.js ≥ 20
- Python 3.11+
- Supabase account (free tier works)
- API-Football key (free tier: 100 req/day)

### Setup

```bash
# 1. Clone
git clone https://github.com/kara-india/football-prediction.git
cd football-prediction

# 2. Install JS dependencies
npm install

# 3. Install Python dependencies
pip install -r python/requirements.txt

# 4. Configure environment
cp .env.example .env.local
# Fill in your keys in .env.local

# 5. Apply database schema
export SUPABASE_SERVICE_ROLE_KEY=your_key_here
python scripts/apply_migrations.py

# 6. Start the dashboard
npm run dev
```

### Environment Variables

```env
# Public (browser-safe)
NEXT_PUBLIC_SUPABASE_URL=https://qqcxjjkgvqknesrtnwal.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...

# Server-only secrets — NEVER expose to browser
SUPABASE_SERVICE_ROLE_KEY=          # Supabase dashboard → Settings → API
API_FOOTBALL_KEY=                   # api-sports.io free tier
ODDS_API_KEY=                       # optional — The Odds API
NEXT_PUBLIC_APP_URL=http://localhost:3000
PYTHON_ENGINE_URL=http://localhost:8001
```

### Run the Python engine locally

```bash
python python/main.py
# FastAPI server at http://localhost:8001
```

### Run tests

```bash
# Python tests (97 pass)
python -m pytest tests/ -v

# TypeScript check
npm run typecheck

# Lint
npm run lint
```

---

## 🔄 Background Engine

Enable the background engine from the dashboard or by updating `engine_settings` in Supabase:

```sql
UPDATE engine_settings SET value = 'true' WHERE key = 'engine_enabled';
UPDATE engine_settings SET value = 'true' WHERE key = 'paper_betting_enabled';
```

GitHub Actions will automatically run:

| Workflow | Schedule | Purpose |
|----------|---------|---------|
| `collector.yml` | Every 15 minutes | Fetch live state, 1xBet odds, analyze eligible matches |
| `evaluator.yml` | Daily 3 AM UTC | Settle paper bets, classify errors, compute metrics |
| `learner.yml` | Monday 4 AM UTC | Incremental model updates (requires `learning_enabled=true`) |

Required GitHub Secrets:
```
SUPABASE_URL · SUPABASE_SERVICE_ROLE_KEY · API_FOOTBALL_KEY
```

---

## 📈 Model Lifecycle

```
Historical Data Import
        │
        ▼
  Dixon-Coles Fit  ──────▶  Walk-forward Validation
        │                           │
        ▼                           ▼
  CHALLENGER model          Brier / LogLoss / ECE
        │                           │
        ▼                    Better than CHAMPION?
  Paper predictions                 │
        │                    YES ──▶ Promote
        ▼                    NO  ──▶ Retire quietly
  Settle & measure
        │
        ▼
  Online parameter updates
```

> A model is promoted to CHAMPION only when walk-forward validation demonstrates improvement on **Brier score AND log loss**. Not based on one good week.

---

## ⚠️ Honest Limitations

- **No historical data fitted yet** — models are implemented and unit-tested but require the data import + walk-forward step before predictions are meaningful
- **1xBet live odds on API-Football free tier** — prematch confirmed; live coverage unverified
- **Score-state intensity multipliers** — initialized from literature estimates; must be calibrated against real data before live use
- **No real money betting** — this is a **paper bet only** system by design

---

## 📁 Project Structure

```
football-prediction/
├── src/                        # Next.js frontend
│   ├── app/                    # App Router pages + API routes
│   ├── components/             # Dashboard, match, analytics components
│   └── lib/                    # Supabase clients, utilities, constants
├── python/                     # Python prediction engine
│   ├── adapters/               # API-Football, football-data.co.uk, StatsBomb
│   ├── models/                 # Elo, Dixon-Coles, NB, player model
│   ├── simulation/             # Monte Carlo engine
│   ├── calibration/            # Calibrator, EV, NO-BET gate, settlement
│   ├── providers/              # 1xBet odds provider abstraction
│   ├── backtesting/            # Historical replayer, walk-forward, CLV
│   ├── learning/               # Online learner, evaluator
│   ├── rl/                     # RL/contextual bandit (disabled)
│   └── workers/                # Background worker scripts
├── supabase/                   # SQL migrations (27 tables)
├── tests/                      # 97 passing tests
├── .github/workflows/          # GitHub Actions (collector, evaluator, learner, CI)
└── docs/                       # Architecture, operations, model design, RL guide
```

---

## 📜 License

MIT — use it, study it, don't bet the mortgage on it.

---

<div align="center">

**Built with discipline. Validated with evidence. Silent when uncertain.**

*The best bet is often no bet.*

</div>
