import pandas as pd
from datetime import date

class FormCalculator:
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        
    def calculate_ewma_form(self, results: list[dict], metric: str) -> float:
        if not results:
            return 0.0
            
        sorted_results = sorted(results, key=lambda x: x['date'], reverse=True)
        ewma = 0.0
        weight_sum = 0.0
        current_weight = 1.0
        
        for r in sorted_results:
            val = r.get(metric, 0.0)
            mult = r.get('weight', 1.0)
            ewma += val * current_weight * mult
            weight_sum += current_weight * mult
            current_weight *= (1.0 - self.alpha)
            
        return ewma / max(weight_sum, 1e-9)
        
    def calculate_team_attack_strength(self, team_matches: pd.DataFrame, 
                                        league_avg_goals: float) -> float:
        if len(team_matches) == 0:
            return 1.0
        avg = team_matches['goals_scored'].mean()
        return avg / max(league_avg_goals, 1e-9)
        
    def calculate_team_defense_strength(self, team_matches: pd.DataFrame,
                                         league_avg_goals: float) -> float:
        if len(team_matches) == 0:
            return 1.0
        avg = team_matches['goals_conceded'].mean()
        return avg / max(league_avg_goals, 1e-9)
        
    def get_rest_days(self, last_match_date: date, current_date: date) -> int:
        return (current_date - last_match_date).days
