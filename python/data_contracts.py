"""
Canonical Data Contracts & Schemas
Authoritative Python dataclasses representing normalized domain entities.
Adheres strictly to docs/DATA_CONTRACTS.md.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class CanonicalMatch:
    """Represents the static and scheduled attributes of a fixture."""
    match_id: str                      # Canonical UUID or deterministic string
    provider_id: str                   # E.g., "api-football", "football-data-uk"
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


@dataclass(frozen=True)
class CanonicalMatchState:
    """Represents in-play continuous state at instantaneous minute T."""
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


@dataclass(frozen=True)
class CanonicalEvent:
    """Atomic in-play event triggering Monte Carlo state transitions."""
    event_id: str
    match_id: str
    minute: int
    added_time: int
    event_type: str                    # "GOAL", "OWN_GOAL", "PENALTY", "YELLOW_CARD", "RED_CARD", "SUBSTITUTION", "CORNER", "FOUL", "VAR"
    event_detail: Optional[str]
    team_id: int
    player_id: Optional[int]
    player_name: Optional[str]
    secondary_player_id: Optional[int]
    secondary_player_name: Optional[str]
    source_timestamp: datetime
    available_at: datetime


@dataclass(frozen=True)
class CanonicalOddsSelection:
    selection: str                     # "Home", "Draw", "Away", "Over", "Under", "Yes", "No"
    line: Optional[float]              # E.g. 2.5
    decimal_odds: float                # 1xBet execution price
    implied_prob: float                # 1 / decimal_odds
    devigged_prob: Optional[float]     # Margin-removed fair market probability
    is_suspended: bool = False
    player_id: Optional[int] = None


@dataclass(frozen=True)
class CanonicalOddsMarket:
    match_id: str
    bookmaker: str                     # Strictly "1xbet" for execution
    canonical_market: str              # E.g. "MATCH_1X2", "TOTAL_GOALS", "BTTS"
    period: str                        # "FULL_TIME", "FIRST_HALF", "SECOND_HALF"
    is_live: bool
    selections: List[CanonicalOddsSelection]
    market_margin: float               # Sum of implied probs - 1.0
    source_timestamp: datetime
    available_at: datetime


@dataclass(frozen=True)
class CanonicalPrediction:
    prediction_id: str
    match_id: str
    market: str
    selection: str
    line: Optional[float]
    odds_at_prediction: float
    raw_model_prob: float
    calibrated_prob: float
    prob_lower_bound: float
    prob_upper_bound: float
    expected_value: float              # (calibrated_prob * odds) - 1.0
    recommended_action: str            # "BET" or "NO_BET"
    no_bet_reasons: List[str]          # Empty if BET
    data_quality_score: float          # 0.0 - 1.0
    model_version: str
    calibration_version: str
    simulation_version: str
    feature_snapshot_id: str
    prediction_timestamp: datetime


@dataclass(frozen=True)
class CanonicalSettlement:
    prediction_id: str
    match_id: str
    market: str
    selection: str
    odds_at_prediction: float
    actual_outcome: str                # "WON", "LOST", "PUSH", "VOID" (or "WIN", "LOSS")
    profit_loss: float                 # Normalized PnL per 1.0 unit stake
    settled_at: datetime
    line: Optional[float] = None
    closing_odds: Optional[float] = None
    clv: Optional[float] = None        # (odds_at_prediction / closing_odds) - 1.0
    actual_home_goals: Optional[int] = None
    actual_away_goals: Optional[int] = None
    actual_cards: Optional[int] = None
    actual_corners: Optional[int] = None
    brier_score_contribution: Optional[float] = None
    error_classification: Optional[str] = None

    @property
    def outcome(self) -> str:
        """Alias for actual_outcome."""
        return self.actual_outcome

    @property
    def closing_odds_1xbet(self) -> Optional[float]:
        """Alias for closing_odds."""
        return self.closing_odds

    @property
    def actual_score_home(self) -> Optional[int]:
        """Alias for actual_home_goals."""
        return self.actual_home_goals

    @property
    def actual_score_away(self) -> Optional[int]:
        """Alias for actual_away_goals."""
        return self.actual_away_goals


from enum import Enum


class ErrorCategory(str, Enum):
    """Authoritative 11-category post-settlement error taxonomy."""
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
    """Outcome evaluation and causal error classification record generated post-settlement."""
    error_id: str
    prediction_id: str
    match_id: str
    brier_contribution: float
    log_loss_contribution: float
    calibration_residual: float
    scoreline_error: int               # Absolute goal difference error
    ev_realization: float              # Realized PnL - Expected Value
    clv: Optional[float]
    primary_category: ErrorCategory
    secondary_category: Optional[ErrorCategory] = None
    evidence_notes: str = ""
    goal_count_residual: Optional[float] = None
    prediction_stage: Optional[str] = "FINAL_PREMATCH"
