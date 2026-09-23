# DATA CONTRACTS & CANONICAL SCHEMAS
## Football Prediction Intelligence Platform

This document defines the authoritative, canonical data structures and contracts for the platform. Every external provider (API-Football, 1xBet, historical CSVs, open research datasets) must be normalized into these structures before being consumed by any feature engineer, statistical model, Monte Carlo simulation, or database layer.

---

## 1. Core Principles
1. **Provider Independence**: Models and feature engines consume ONLY canonical objects, never raw provider JSON.
2. **Temporal Provenance**: Every entity and feature carries:
   - `source`: Identifier of the origin system.
   - `source_timestamp`: Timestamp when the data was generated at source (UTC).
   - `available_at`: Timestamp when the platform received and validated the data (UTC).
   - **No-Lookahead Invariant**: Any model evaluated as-of time $T$ must strictly satisfy:
     $$\text{available\_at} \le T$$
3. **Data Quality Scoring**: Data entities carry a quality score (0.0 to 1.0) and reliability tier (`HIGH`, `MEDIUM`, `LOW`).

---

## 2. Canonical Match Models

### 2.1 `CanonicalMatch`
Represents the static and scheduled attributes of a fixture.
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class CanonicalMatch:
    match_id: str                      # Canonical UUID or deterministic hash
    provider_id: str                   # E.g., "api-football"
    provider_fixture_id: int           # Raw provider fixture ID
    competition_id: int                # Canonical competition ID from database
    competition_name: str
    season: int                        # E.g., 2024
    round: str                         # E.g., "Regular Season - 5"
    kickoff_utc: datetime
    venue_name: Optional[str]
    referee: Optional[str]
    home_team_id: int                  # Canonical team ID
    home_team_name: str
    away_team_id: int                  # Canonical team ID
    away_team_name: str
    status: str                        # "NS" (Not Started), "LIVE", "HT", "FT", "PST" (Postponed)
    is_eligible: bool                  # Passed 10-league allowlist & senior men's gate
    source_timestamp: datetime
    available_at: datetime
```

### 2.2 `CanonicalMatchState`
Represents the in-play continuous state of a match at any instantaneous minute $T$.
```python
@dataclass(frozen=True)
class CanonicalMatchState:
    match_id: str
    minute: int                        # Elapsed regular time (0 - 90+)
    added_time: int                    # Extra injury time in current half
    period: str                        # "PREMATCH", "1H", "HT", "2H", "ET", "FT"
    score_home: int
    score_away: int
    possession_home: Optional[float]   # 0.0 - 100.0
    possession_away: Optional[float]
    shots_home: int
    shots_away: int
    shots_on_target_home: int
    shots_on_target_away: int
    xg_home: Optional[float]
    xg_away: Optional[float]
    corners_home: int
    corners_away: int
    fouls_home: int
    fouls_away: int
    yellow_cards_home: int
    yellow_cards_away: int
    red_cards_home: int
    red_cards_away: int
    lineup_confirmed: bool             # True when official 11 starters verified
    is_stale: bool                     # True if latency > 120s without heartbeat
    source_timestamp: datetime
    available_at: datetime
```

### 2.3 `CanonicalEvent`
Atomic in-play events that trigger state transitions in the hazard/Monte Carlo engine.
```python
@dataclass(frozen=True)
class CanonicalEvent:
    event_id: str
    match_id: str
    minute: int
    added_time: int
    event_type: str                    # "GOAL", "OWN_GOAL", "PENALTY", "YELLOW_CARD",
                                       # "RED_CARD", "SUBSTITUTION", "CORNER", "FOUL", "VAR"
    event_detail: Optional[str]        # E.g., "Normal Goal", "Second Yellow", "Tactical"
    team_id: int
    player_id: Optional[int]
    player_name: Optional[str]
    secondary_player_id: Optional[int] # Assist or subbed-off player
    secondary_player_name: Optional[str]
    source_timestamp: datetime
    available_at: datetime
```

---

## 3. Canonical Odds Models

### 3.1 Market Identity & Composite Key
Odds identity in the database and engine must distinguish live/pre-match, periods, lines, and player entities to prevent collision:
$$\text{OddsKey} = (\text{match\_id}, \text{bookmaker}, \text{canonical\_market}, \text{period}, \text{selection}, \text{line}, \text{player\_id})$$

### 3.2 Canonical Market Universe
1. `MATCH_1X2`: Match winner (`Home`, `Draw`, `Away`).
2. `DOUBLE_CHANCE`: `1X`, `12`, `X2`.
3. `TOTAL_GOALS`: Over/Under with discrete lines `1.5`, `2.5`, `3.5`, `4.5`.
4. `BTTS`: Both Teams To Score (`Yes`, `No`).
5. `NEXT_GOAL`: In-play next team to score (`Home`, `None`, `Away`).
6. `TOTAL_CARDS`: Over/Under with line `3.5`, `4.5`, `5.5`.
7. `TEAM_CARDS`: Over/Under per team.
8. `PLAYER_GOALSCORER_ANYTIME`: Player to score in 90 minutes.
9. `PLAYER_ASSIST`: Player to register official assist.

### 3.3 `CanonicalOddsMarket` & `CanonicalOddsSelection`
```python
@dataclass(frozen=True)
class CanonicalOddsSelection:
    selection: str                     # E.g., "Home", "Over", "Yes", "Player:Erling Haaland"
    line: Optional[float]              # E.g., 2.5
    decimal_odds: float                # 1xBet execution price (e.g., 1.95)
    implied_prob: float                # 1 / decimal_odds
    devigged_prob: Optional[float]     # Margin-removed fair market probability
    is_suspended: bool
    player_id: Optional[int]

@dataclass(frozen=True)
class CanonicalOddsMarket:
    match_id: str
    bookmaker: str                     # Strictly "1xbet" for execution
    canonical_market: str              # E.g., "MATCH_1X2", "TOTAL_GOALS_2_5"
    period: str                        # "FULL_TIME", "FIRST_HALF", "SECOND_HALF"
    is_live: bool
    selections: list[CanonicalOddsSelection]
    market_margin: float               # Sum of implied probs - 1.0
    source_timestamp: datetime
    available_at: datetime
```

---

## 4. Canonical Prediction & Decision Models

### 4.1 `CanonicalPrediction`
Produced by the analytical engine. Immutable once stored.
```python
@dataclass(frozen=True)
class CanonicalPrediction:
    prediction_id: str                 # UUID
    match_id: str
    market: str                        # Canonical market ID
    selection: str                     # Target outcome
    line: Optional[float]
    odds_at_prediction: float          # 1xBet price at decision time
    raw_model_prob: float              # Direct simulation or statistical output
    calibrated_prob: float             # Post-isotonic/Platt calibrated probability
    prob_lower_bound: float            # 95% Credible / Confidence interval lower
    prob_upper_bound: float            # 95% Credible / Confidence interval upper
    expected_value: float              # (calibrated_prob * odds) - 1.0
    recommended_action: str            # "BET" or "NO_BET"
    no_bet_reasons: list[str]          # Empty if action is "BET"
    data_quality_score: float          # 0.0 - 1.0
    model_version: str                 # E.g., "dixon_coles_v1.2"
    calibration_version: str
    simulation_version: str
    feature_snapshot_id: str
    prediction_timestamp: datetime
```

### 4.2 Standard NO-BET Taxonomy
When `recommended_action == "NO_BET"`, one or more standard failure codes must be attached:
1. `NEGATIVE_EV`: Expected value $\le 0.0$.
2. `EDGE_BELOW_THRESHOLD`: Edge positive but $< \tau_{\text{min}}$ (e.g. $< 0.03$).
3. `LINEUP_UNCONFIRMED`: Starting XIs not yet verified by official team sheet.
4. `ODDS_STALE`: 1xBet price timestamp $> 15\text{ minutes}$ old (pre-match) or $> 60\text{s}$ (live).
5. `MARKET_SUSPENDED`: 1xBet has locked or taken down the market line.
6. `HIGH_UNCERTAINTY`: Monte Carlo standard error $> 0.02$ or credible interval too wide.
7. `MODEL_UNCALIBRATED`: Insufficient out-of-sample data in this odds/league regime.
8. `SOURCE_CONFLICT`: Discrepancy between match event feeds or lineup rosters.
9. `PLAYER_MINUTES_UNCERTAIN`: Player is not a confirmed starter or returning from injury.
10. `INSUFFICIENT_SAMPLE`: Historical sample size $< 200$ matches for specific competition context.

---

## 5. Settlement & Audit Contracts

### 5.1 `CanonicalSettlement`
```python
@dataclass(frozen=True)
class CanonicalSettlement:
    prediction_id: str
    match_id: str
    outcome: str                       # "WON", "LOST", "VOID", "PUSH"
    settled_at: datetime
    actual_score_home: int
    actual_score_away: int
    closing_odds_1xbet: Optional[float]
    clv: Optional[float]               # (odds_at_prediction / closing_odds_1xbet) - 1.0
    profit_loss: float                 # Calculated on 1.0 unit flat stake
    error_classification: Optional[str]# One of 11 standard error taxonomy categories

### 5.2 `CanonicalPredictionCheckpoint`
Immutable prediction ledger snapshot representing a distinct forecast milestone.
```python
from enum import Enum

class PredictionStage(str, Enum):
    INITIAL = "INITIAL"                      # T-48h early forecast
    LINEUP_CONFIRMED = "LINEUP_CONFIRMED"    # T-60m official XI forecast
    LINEUP_V2 = "LINEUP_V2"                  # Late revision snapshot
    FINAL_PREMATCH = "FINAL_PREMATCH"        # T-5m closing market snapshot
    LIVE = "LIVE"                            # In-play continuous snapshot

@dataclass(frozen=True)
class CanonicalPredictionCheckpoint:
    prediction_id: str
    match_id: str
    prediction_stage: PredictionStage
    prediction_timestamp: datetime
    prediction_generated_at: datetime
    model_version: str
    calibration_version: str
    feature_version: str
    dataset_version: str
    market: str
    selection: str
    line: Optional[float]
    raw_probability: float
    calibrated_probability: float
    prob_lower_bound: float
    prob_upper_bound: float
    odds_1xbet: Optional[float]
    implied_probability: Optional[float]
    fair_probability: Optional[float]
    edge: Optional[float]
    ev: Optional[float]
    simulation_version: str
    simulation_count: int
    simulation_error: float
    lineup_version: int
    lineup_available_at: Optional[datetime]
    lineup_quality: str                # "VERIFIED_11_VS_11", "ESTIMATED", "UNKNOWN"
    source_freshness_seconds: int
    source_quality_score: float
    source_conflicts: list[str]
    decision: str                      # "BET", "NO_BET", "ABSTAIN"
    decision_reason: str
    git_sha: str
```

### 5.3 `CanonicalForecastError`
Outcome evaluation and causal error classification record generated post-settlement.
```python
class ErrorCategory(str, Enum):
    TEAM_STRENGTH_MISS = "TEAM_STRENGTH_MISS"
    LINEUP_MISASSESSMENT = "LINEUP_MISASSESSMENT"
    PLAYER_PROJECTION_ERROR = "PLAYER_PROJECTION_ERROR"
    TACTICAL_MISMATCH = "TACTICAL_MISMATCH"
    LIVE_STATE_ERROR = "LIVE_STATE_ERROR"
    ODDS_STALENESS = "ODDS_STALENESS"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    DATA_MISSING = "DATA_MISSING"
    CALIBRATION_ERROR = "CALIBRATION_ERROR"
    PARAMETER_DRIFT = "PARAMETER_DRIFT"
    RANDOM_VARIANCE = "RANDOM_VARIANCE"

@dataclass(frozen=True)
class CanonicalForecastError:
    error_id: str
    prediction_id: str
    match_id: str
    prediction_stage: PredictionStage
    brier_contribution: float
    log_loss_contribution: float
    calibration_residual: float
    goal_count_residual: float
    scoreline_error: int               # Absolute goal difference error
    ev_realization: float
    clv: Optional[float]
    primary_category: ErrorCategory
    secondary_category: Optional[ErrorCategory]
    evidence_notes: str
```

### 5.4 `CanonicalDecisionRecord` (RL & Contextual Bandit Dataset)
Preserves every candidate decision opportunity (including ABSTAIN) for unbiased offline policy evaluation.
```python
@dataclass(frozen=True)
class CanonicalDecisionRecord:
    decision_id: str
    match_id: str
    timestamp: datetime
    market: str
    selection: str
    line: Optional[float]
    context_features: Dict[str, float]
    model_probability: float
    calibrated_probability: float
    probability_interval: Tuple[float, float]
    odds: float
    fair_probability: float
    edge: float
    ev: float
    data_quality_tier: str
    lineup_state: str
    available_actions: list[str]       # E.g. ["ABSTAIN", "BET"]
    chosen_action: str
    action_propensity: float           # P(chosen_action | context) for IPS/DR evaluation
    actual_outcome: Optional[int]      # 1 (win) or 0 (loss)
    realized_return: Optional[float]
    counterfactual_return: Optional[float]
    policy_version: str
```
```
