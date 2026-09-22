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

[![Supabase](https://img.shields.io/badge/Supabase-Live%20%26%20Deployed-3ECF8E?logo=supabase&logoColor=white)](#-database--supabase-status)
[![API-Football](https://img.shields.io/badge/API--Football-Connected%20(100%20req%2Fday)-blue)](#-data-sources--api-keys)
[![Tests](https://img.shields.io/badge/tests-97%20passed-brightgreen)](#-tests--verification)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![Target Bookmaker](https://img.shields.io/badge/1xBet-Exclusive%20Target-orange)](#-target-bookmaker)

</div>

---

> **This is NOT a tipster service or an LLM probability generator.**  
> This is a personal analytical engine that applies statistical modelling, Monte Carlo simulation, and rigorous probability calibration to identify 1xBet prices where the model has a measurable, evidence-based edge — and stays silent (**NO BET**) when it doesn't.

---

## ⚡ Live Status & Verification

| Component | Status | Details |
|---|---|---|
| **Supabase Database** | 🟢 **Live & Deployed** | All 27 tables, indexes, constraints & RLS policies created on `qqcxjjkgvqknesrtnwal.supabase.co` |
| **Competition Registry** | 🟢 **Seeded (19 leagues)** | EPL, Serie A, La Liga, Bundesliga, Ligue 1, UCL, World Cup, etc. |
| **Market Definitions** | 🟢 **Seeded (12 markets)** | 1X2, Double Chance, Over/Under 1.5–4.5, BTTS, Cards, Anytime Goalscorer, Assists |
| **Engine Settings** | 🟢 **Seeded (11 flags)** | Master safety gates (`engine_enabled=false`, `learning_enabled=false`, `rl_enabled=false`) |
| **API-Football Key** | 🟢 **Configured & Validated** | Verified live via API-Sports status endpoint with active quota |
| **Automated Tests** | 🟢 **97 / 97 Passed** | Full suite passed across models, Monte Carlo, calibration, and no-lookahead assertions |

---

## 🧠 Core Philosophy

Most football betting tools fail for one of three reasons:

1. They confuse **hit rate** with **edge** — winning 55% of bets at 1.80 odds is still a net loss.
2. They let an algorithm or human **manually assign feature weights** with zero empirical grounding.
3. They **force a recommendation** on every match even when data is stale, lineups are missing, or uncertainty is massive.

This platform enforces strict statistical discipline:

| ❌ What this system never does | ✅ What it does instead |
|---|---|
| Assign arbitrary feature weights | Derive all weights from walk-forward validated statistical distributions |
| Claim a bet is "guaranteed", "lock", or "safe" | Output **NO BET** whenever statistical gates or uncertainty thresholds fail |
| Use LLMs to invent numerical probabilities | LLMs only provide diagnostics and explanations; pure math drives probabilities |
| Treat bookmaker odds as ground truth | Measure raw model vs. de-vigged market, calibrate, and compare against 1xBet price |
| Rely on small-sample winning streaks | Track Brier score, log loss, ECE, CLV, and ROI over rolling out-of-sample periods |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEXT.JS 14 DASHBOARD                              │
│   Live Matches │ Upcoming (Lineup-Confirmed) │ Prediction History │ Analytics│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / SSR
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                            SUPABASE (PostgreSQL)                            │
│    27 Normalized Tables · Indexes · RLS Security · Real-time State & Ledger  │
└──────────┬──────────────────────────────────────────────────┬───────────────┘
           │                                                  │
┌──────────▼──────────────┐                        ┌──────────▼───────────────┐
│     DATA INGESTION      │                        │      PYTHON ENGINE       │
│                         │                        │                          │
│ API-Football v3         │                        │ ┌─ Dynamic Elo Baseline  │
│ (1xBet Odds Feed)       │────── Priority ───────▶│ ├─ Dixon-Coles Poisson   │
│                         │        Budget          │ ├─ Negative Binomial     │
│ football-data.co.uk     │      (P0 -> P3)        │ ├─ Hierarchical Player   │
│ (Historical free CSV)   │                        │ ├─ Path-Dependent MC     │
│                         │                        │ ├─ Isotonic Calibration  │
│ StatsBomb Open Data     │                        │ ├─ Kelly & EV Calculator │
│ (xG & Shot Coordinates) │                        │ └─ 15-Gate NO-BET Filter │
└─────────────────────────┘                        └──────────────────────────┘
                                                                 │
┌────────────────────────────────────────────────────────────────▼────────────┐
│                        SCHEDULED WORKERS & ACTIONS                          │
│     15-min Live Collector  │  Daily Match Evaluator  │  Weekly Model Learner│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Analytical Components

### 📐 Statistical Models
* **Dynamic Elo Baseline**: Real-time team strength ratings incorporating home advantage and goal margin weighting.
* **Dixon-Coles Model**: Bivariate Poisson model with low-score coupling parameter ($\tau$) adjusting for 0-0, 1-0, 0-1, and 1-1 dependencies.
* **Negative Binomial Models**: Count-market models for over-dispersed distributions (match cards, team cards, corners, fouls).
* **Hierarchical Player Model**: Empirical Bayes shrinkage for player anytime goalscorer and assist probabilities adjusted for confirmed lineup status and expected minutes.
* **EWMA Form Engine**: Exponentially weighted moving average of team attacking and defensive performance.

### 🎲 Path-Dependent Monte Carlo Simulator
Unlike naive simulators that linearly project match goal rates, our engine models **score-state and time-dependent hazard rates**:
* Simulating from **0-0 at 75'** produces a radically different distribution than **2-0 at 75'** or **0-2 at 75'**.
* Factors in trailing-team urgency, red card team suppression, and empirical late-match goal acceleration.
* Adaptive convergence: runs in batches from 10,000 to 500,000 simulations until standard error falls below threshold ($\text{SE} < 0.005$).

### 🚦 The 15-Gate NO-BET Engine
A candidate must pass all validation checks before being displayed as an actionable opportunity:
```
[1] INSUFFICIENT_DATA      [6] LOW_SAMPLE             [11] SIMULATION_UNSTABLE
[2] STALE_ODDS             [7] MARKET_SUSPENDED       [12] SOURCE_CONFLICT
[3] STALE_STATE            [8] LINEUP_UNCONFIRMED     [13] PROVIDER_FAILURE
[4] MODEL_UNCALIBRATED     [9] PLAYER_UNCERTAIN       [14] NEGATIVE_EV
[5] HIGH_UNCERTAINTY      [10] EDGE_TOO_SMALL         [15] ODDS_OUT_OF_BOUNDS
```

### 🎯 1xBet Target Markets
Odds are ingested and normalized specifically for 1xBet:
* **1X2** (Match Winner)
* **Double Chance** (1X, 12, X2)
* **Totals** (Over/Under 1.5, 2.5, 3.5, 4.5)
* **Both Teams to Score (BTTS)**
* **Next Goal** (Live)
* **Total & Team Cards**
* **Anytime Goalscorer & Player Assist** (Lineup-gated)

---

## 🚀 Quick Start

### 1. Repository Setup
```bash
# Clone the repository
git clone https://github.com/kara-india/football-prediction.git
cd football-prediction

# Install Node dependencies
npm install

# Install Python requirements
pip install -r python/requirements.txt
```

### 2. Environment Configuration
The database schema and API keys are already configured in `.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://qqcxjjkgvqknesrtnwal.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_MWK1XOnTtdc4MsagVnYHHw_qJUNnqsh
API_FOOTBALL_KEY=073534f7111a37868a403c5cd51d83fa
NEXT_PUBLIC_APP_URL=http://localhost:3000
PYTHON_ENGINE_URL=http://localhost:8001
```

### 3. Verify Database Connectivity
Confirm the live Supabase tables and seeded registry:
```bash
python -c "
import urllib.request, json
url = 'https://qqcxjjkgvqknesrtnwal.supabase.co/rest/v1/competitions?select=name,league_id'
headers = {
    'apikey': 'sb_publishable_MWK1XOnTtdc4MsagVnYHHw_qJUNnqsh',
    'Authorization': 'Bearer sb_publishable_MWK1XOnTtdc4MsagVnYHHw_qJUNnqsh'
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
    print(f'Connected to Supabase! {len(data)} competitions registered.')
"
```

### 4. Run the Full Test Suite
Verify that all 97 analytical and simulation unit tests pass:
```bash
python -m pytest tests/ -v
```

### 5. Launch the Dashboard
```bash
npm run dev
# Open http://localhost:3000 in your browser
```

### 6. Run the Python Engine (Optional Local Mode)
```bash
python python/main.py
# Engine runs at http://localhost:8001
```

---

## 🔄 Background Automation & Engine Settings

The platform features background workers orchestrated via GitHub Actions or local CLI:

| Worker | Schedule | Purpose |
|---|---|---|
| `collector.yml` | Every 15 minutes | Pulls live score states & 1xBet odds for eligible matches |
| `evaluator.yml` | Daily at 03:00 UTC | Settles paper bets against final scores, records CLV, and classifies errors |
| `learner.yml` | Weekly (Mondays) | Refits Dixon-Coles parameters and evaluates Challenger models |

### Engine Master Switches (`engine_settings` table)
By default, the platform runs in safe observation mode:
* `engine_enabled`: Master switch (`true` / `false`)
* `paper_betting_enabled`: Automatically logs qualifying EV edges to paper ledger
* `learning_enabled`: Allows incremental model weight updates
* `rl_enabled`: Contextual bandit decision layer (remains disabled until $\ge 500$ settled bets)

To activate paper betting or the engine, update the setting via the dashboard or Supabase SQL:
```sql
UPDATE engine_settings SET value = 'true' WHERE key = 'engine_enabled';
UPDATE engine_settings SET value = 'true' WHERE key = 'paper_betting_enabled';
```

---

## 🧪 Tests & Verification

The repository enforces strict mathematical correctness through automated tests:

* `test_odds_conversion.py`: Decimal odds, de-vigging equations, implied probabilities, and Kelly stakes.
* `test_settlement.py`: Push/void logic for whole-ball totals, 1X2, BTTS, and double chance settlements.
* `test_monte_carlo.py`: Stateful path simulation and verification that score state (e.g. 2-0 vs 0-0 at 75') alters future probability distributions.
* `test_no_lookahead.py`: Strict temporal validation proving that features, lineups, and odds generated at timestamp $T$ cannot access data timestamped $> T$.
* `test_dixon_coles.py` & `test_elo.py`: Probability matrix closure, conservation of Elo rating points, and $\tau$ parameter adjustments.

---

## 📁 Repository Structure

```
football-prediction/
├── src/                        # Next.js 14 frontend application
│   ├── app/                    # App Router pages (/matches, /predictions, /analytics)
│   ├── components/             # Reusable UI, Odds Panel, Monte Carlo distributions
│   └── lib/                    # Supabase clients, TypeScript types, constants
├── python/                     # Core numerical prediction engine
│   ├── adapters/               # API-Football, football-data.co.uk, StatsBomb
│   ├── models/                 # Elo, Dixon-Coles, Negative Binomial, Player models
│   ├── simulation/             # Path-dependent Monte Carlo simulation engine
│   ├── calibration/            # Probability calibration, EV, NO-BET gate, settlement
│   ├── providers/              # 1xBet odds provider abstraction & stale detector
│   ├── backtesting/            # Historical replay, walk-forward, CLV tracker
│   ├── learning/               # Online learner, evaluator, Champion/Challenger
│   ├── rl/                     # Contextual bandit decision layer (disabled)
│   └── workers/                # Collector, evaluator, and learner background tasks
├── supabase/                   # Database schemas, seed scripts, and verification
├── tests/                      # 97 unit & integration tests
├── .github/workflows/          # CI/CD and automated background worker workflows
└── docs/                       # Comprehensive architectural and statistical documentation
```

---

## 📜 License

MIT License — Built for personal research, statistical analysis, and algorithmic betting intelligence.

<div align="center">

**Built with discipline. Validated with evidence. Silent when uncertain.**  
*The best bet is often no bet.*

</div>
