from dataclasses import dataclass

@dataclass
class MatchState:
    minute: int
    added_time: int
    score_home: int
    score_away: int
    period: str  # 'first_half', 'second_half', 'extra_time'
    
    # Live stats
    possession_home: float  # 0-100
    shots_home: int
    shots_away: int
    shots_on_target_home: int
    shots_on_target_away: int
    xg_home: float
    xg_away: float
    corners_home: int
    corners_away: int
    fouls_home: int
    fouls_away: int
    yellow_cards_home: int
    yellow_cards_away: int
    red_cards_home: int
    red_cards_away: int
    offsides_home: int
    offsides_away: int
    substitutions_home: int
    substitutions_away: int
    
    # Key flags
    is_live: bool
    lineup_confirmed: bool
    
    @property
    def score_difference(self) -> int:
        return self.score_home - self.score_away
    
    @property
    def total_goals(self) -> int:
        return self.score_home + self.score_away
    
    @property
    def remaining_minutes(self) -> float:
        if self.period == 'first_half':
            return max(0, 45 - self.minute + self.added_time)
        elif self.period == 'second_half':
            return max(0, 90 - self.minute + self.added_time)
        return 0.0
