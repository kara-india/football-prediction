import math
from datetime import date
from typing import Any

class EloSystem:
    DEFAULT_RATING = 1500.0
    K_FACTOR = 32.0
    HOME_ADVANTAGE = 100.0
    
    def __init__(self, ratings: dict[int, float] = None):
        self.ratings = ratings or {}
    
    def get_rating(self, team_id: int) -> float:
        return self.ratings.get(team_id, self.DEFAULT_RATING)
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))
    
    def update(self, home_id: int, away_id: int, home_goals: int, away_goals: int, weight: float = 1.0) -> tuple[float, float]:
        r_home = self.get_rating(home_id)
        r_away = self.get_rating(away_id)
        
        expected_home = self.expected_score(r_home + self.HOME_ADVANTAGE, r_away)
        expected_away = self.expected_score(r_away, r_home + self.HOME_ADVANTAGE)
        
        if home_goals > away_goals:
            actual_home = 1.0
            actual_away = 0.0
        elif home_goals < away_goals:
            actual_home = 0.0
            actual_away = 1.0
        else:
            actual_home = 0.5
            actual_away = 0.5
            
        new_home = r_home + self.K_FACTOR * weight * (actual_home - expected_home)
        new_away = r_away + self.K_FACTOR * weight * (actual_away - expected_away)
        
        self.ratings[home_id] = new_home
        self.ratings[away_id] = new_away
        
        return new_home, new_away
    
    def predict_1x2(self, home_id: int, away_id: int) -> tuple[float, float, float]:
        r_home = self.get_rating(home_id)
        r_away = self.get_rating(away_id)
        
        expected_home = self.expected_score(r_home + self.HOME_ADVANTAGE, r_away)
        
        prob_draw = 0.25 * math.exp(-0.5 * ((expected_home - 0.5) / 0.15) ** 2)
        
        prob_home = expected_home * (1 - prob_draw)
        prob_away = (1 - expected_home) * (1 - prob_draw)
        
        total = prob_home + prob_draw + prob_away
        return prob_home / total, prob_draw / total, prob_away / total
    
    def bulk_update_from_history(self, matches: list[dict]) -> None:
        sorted_matches = sorted(matches, key=lambda x: x.get('date', ''))
        for m in sorted_matches:
            self.update(m['home_id'], m['away_id'], m['home_goals'], m['away_goals'], m.get('weight', 1.0))
            
    def serialize(self) -> dict:
        return {'ratings': self.ratings, 'k_factor': self.K_FACTOR, 'home_advantage': self.HOME_ADVANTAGE}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EloSystem':
        sys = cls(data.get('ratings', {}))
        sys.K_FACTOR = data.get('k_factor', 32.0)
        sys.HOME_ADVANTAGE = data.get('home_advantage', 100.0)
        return sys
