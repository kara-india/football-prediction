CANONICAL_MARKETS = {
    '1x2': {'description': 'Match Result', 'selections': ['1', 'X', '2'], 'settlement_type': 'binary'},
    'double_chance': {'description': 'Double Chance', 'selections': ['1X', '12', 'X2'], 'settlement_type': 'binary'},
    'over_under_15': {'description': 'Goals Over/Under 1.5', 'selections': ['over', 'under'], 'line': 1.5, 'settlement_type': 'binary'},
    'over_under_25': {'description': 'Goals Over/Under 2.5', 'selections': ['over', 'under'], 'line': 2.5, 'settlement_type': 'binary'},
    'over_under_35': {'description': 'Goals Over/Under 3.5', 'selections': ['over', 'under'], 'line': 3.5, 'settlement_type': 'binary'},
    'over_under_45': {'description': 'Goals Over/Under 4.5', 'selections': ['over', 'under'], 'line': 4.5, 'settlement_type': 'binary'},
    'btts': {'description': 'Both Teams to Score', 'selections': ['yes', 'no'], 'settlement_type': 'binary'},
    'next_goal': {'description': 'Next Goal', 'selections': ['1', 'no_goal', '2'], 'settlement_type': 'binary'},
    'total_cards': {'description': 'Total Cards Over/Under', 'selections': ['over', 'under'], 'settlement_type': 'binary'},
    'team_cards': {'description': 'Team Cards', 'selections': ['over', 'under'], 'settlement_type': 'binary'},
    'anytime_goalscorer': {'description': 'Anytime Goalscorer', 'selections': ['yes'], 'settlement_type': 'binary'},
    'player_assist': {'description': 'Player Assist', 'selections': ['yes'], 'settlement_type': 'binary'},
}

MARKET_NAME_MAPPING = {
    'Match Winner': '1x2',
    'Double Chance': 'double_chance',
    'Both Teams Score': 'btts'
}

def normalize_market_name(raw_name: str) -> str | None:
    return MARKET_NAME_MAPPING.get(raw_name)

def implied_probability(decimal_odds: float) -> float:
    return 1.0 / decimal_odds if decimal_odds > 0 else 0.0

def de_vig(odds_list: list[float]) -> list[float]:
    raw_probs = [implied_probability(o) for o in odds_list]
    total_prob = sum(raw_probs)
    if total_prob == 0:
        return []
    return [p / total_prob for p in raw_probs]

def decimal_to_fractional(decimal_odds: float) -> str:
    from fractions import Fraction
    if decimal_odds <= 1.0:
        return "0/1"
    f = Fraction(decimal_odds - 1.0).limit_denominator(100)
    return f"{f.numerator}/{f.denominator}"

def calculate_margin(odds_list: list[float]) -> float:
    return sum([implied_probability(o) for o in odds_list]) - 1.0

def validate_market(canonical_market: str, selection: str) -> bool:
    if canonical_market not in CANONICAL_MARKETS:
        return False
    return selection in CANONICAL_MARKETS[canonical_market]['selections']
