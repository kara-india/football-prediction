from dataclasses import dataclass

NO_BET_REASONS = [
    'INSUFFICIENT_DATA',
    'STALE_ODDS',
    'STALE_STATE',
    'MODEL_UNCALIBRATED',
    'HIGH_UNCERTAINTY',
    'LOW_SAMPLE',
    'MARKET_SUSPENDED',
    'LINEUP_UNCONFIRMED',
    'PLAYER_UNCERTAIN',
    'EDGE_TOO_SMALL',
    'SIMULATION_UNSTABLE',
    'SOURCE_CONFLICT',
    'PROVIDER_FAILURE',
    'NEGATIVE_EV',
    'ODDS_TOO_LOW',
    'ODDS_TOO_HIGH',
]

@dataclass
class BetCandidate:
    market: str
    selection: str
    line: float | None
    decimal_odds: float
    implied_probability: float
    raw_probability: float
    market_probability: float
    calibrated_probability: float
    probability_lower: float
    probability_upper: float
    expected_value: float
    simulation_count: int
    uncertainty: float
    model_confidence: float
    data_freshness_seconds: int
    odds_freshness_seconds: int
    no_bet_reasons: list[str]
    is_candidate: bool
    decision: str

class NoBetGate:
    MIN_EDGE = 0.03
    MAX_ODDS_FRESHNESS_LIVE = 120
    MAX_ODDS_FRESHNESS_PREMATCH = 1800
    MAX_DATA_FRESHNESS_LIVE = 120
    MAX_DATA_FRESHNESS_PREMATCH = 3600
    MIN_SIMULATION_COUNT = 10_000
    MAX_STD_ERROR = 0.01
    MIN_PROBABILITY = 0.05
    MAX_PROBABILITY = 0.95
    MIN_DECIMAL_ODDS = 1.10
    
    def evaluate(self,
                  market: str,
                  selection: str,
                  line: float | None,
                  decimal_odds: float,
                  raw_probability: float,
                  market_probability: float,
                  calibrated_probability: float,
                  probability_lower: float,
                  probability_upper: float,
                  simulation_count: int,
                  simulation_std_error: float,
                  data_freshness_seconds: int,
                  odds_freshness_seconds: int,
                  is_live: bool,
                  lineup_confirmed: bool,
                  is_market_suspended: bool,
                  model_calibrated: bool,
                  historical_sample_size: int,
                  provider_healthy: bool) -> BetCandidate:
        
        reasons = []
        
        if not provider_healthy:
            reasons.append('PROVIDER_FAILURE')
        if is_market_suspended:
            reasons.append('MARKET_SUSPENDED')
        if not lineup_confirmed and not is_live:
            reasons.append('LINEUP_UNCONFIRMED')
        if not model_calibrated:
            reasons.append('MODEL_UNCALIBRATED')
        if historical_sample_size < 100:
            reasons.append('LOW_SAMPLE')
        if is_live and odds_freshness_seconds > self.MAX_ODDS_FRESHNESS_LIVE:
            reasons.append('STALE_ODDS')
        if not is_live and odds_freshness_seconds > self.MAX_ODDS_FRESHNESS_PREMATCH:
            reasons.append('STALE_ODDS')
        if is_live and data_freshness_seconds > self.MAX_DATA_FRESHNESS_LIVE:
            reasons.append('STALE_STATE')
        if simulation_count < self.MIN_SIMULATION_COUNT:
            reasons.append('SIMULATION_UNSTABLE')
        if simulation_std_error > self.MAX_STD_ERROR:
            reasons.append('SIMULATION_UNSTABLE')
        if calibrated_probability < self.MIN_PROBABILITY:
            reasons.append('INSUFFICIENT_DATA')
        if decimal_odds < self.MIN_DECIMAL_ODDS:
            reasons.append('ODDS_TOO_LOW')
        
        ev = calibrated_probability * decimal_odds - 1
        if ev < 0:
            reasons.append('NEGATIVE_EV')
        elif ev < self.MIN_EDGE:
            reasons.append('EDGE_TOO_SMALL')
        
        uncertainty = probability_upper - probability_lower
        if uncertainty > 0.20:
            reasons.append('HIGH_UNCERTAINTY')
        
        is_candidate = len(reasons) == 0
        decision = 'BET_CANDIDATE' if is_candidate else 'NO_BET'
        
        return BetCandidate(
            market=market,
            selection=selection,
            line=line,
            decimal_odds=decimal_odds,
            implied_probability=1.0 / decimal_odds if decimal_odds > 0 else 0,
            raw_probability=raw_probability,
            market_probability=market_probability,
            calibrated_probability=calibrated_probability,
            probability_lower=probability_lower,
            probability_upper=probability_upper,
            expected_value=ev,
            simulation_count=simulation_count,
            uncertainty=uncertainty,
            model_confidence=1.0 - uncertainty,
            data_freshness_seconds=data_freshness_seconds,
            odds_freshness_seconds=odds_freshness_seconds,
            no_bet_reasons=reasons,
            is_candidate=is_candidate,
            decision=decision
        )
