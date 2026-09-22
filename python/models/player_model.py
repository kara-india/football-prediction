import math

class PlayerGoalModel:
    def predict_anytime_goalscorer(self,
                                    player_id: int,
                                    team_id: int,
                                    opponent_id: int,
                                    is_home: bool,
                                    expected_minutes: float,
                                    is_starter: bool,
                                    team_expected_goals: float,
                                    player_stats: dict,
                                    team_stats: dict) -> float:
        
        p90 = player_stats.get('goals_per_90', 0.1)
        team_p90 = team_stats.get('goals_per_90', 1.0)
        
        attack_scalar = team_expected_goals / max(team_p90, 0.1)
        lam = p90 * (expected_minutes / 90.0) * attack_scalar
        
        return 1.0 - math.exp(-lam)
        
    def predict_assist(self,
                        player_id: int,
                        team_id: int,
                        opponent_id: int,
                        is_home: bool,
                        expected_minutes: float,
                        is_starter: bool,
                        team_expected_goals: float,
                        player_stats: dict,
                        team_stats: dict) -> float:
                        
        p90 = player_stats.get('assists_per_90', 0.1)
        team_p90 = team_stats.get('goals_per_90', 1.0)
        
        attack_scalar = team_expected_goals / max(team_p90, 0.1)
        lam = p90 * (expected_minutes / 90.0) * attack_scalar
        
        return 1.0 - math.exp(-lam)

class HierarchicalPlayerStrength:
    def estimate_player_attack(self, player_stats: dict, team_stats: dict, 
                                league_stats: dict) -> float:
        mins = player_stats.get('minutes', 0)
        goals = player_stats.get('goals', 0)
        
        team_p90 = team_stats.get('goals_per_90', league_stats.get('goals_per_90', 1.0))
        
        prior_mean = team_p90 / 10.0
        prior_weight = 900.0
        
        posterior = (goals + prior_mean * (prior_weight / 90.0)) / ((mins + prior_weight) / 90.0)
        return posterior
        
    def estimate_player_assist(self, player_stats: dict, team_stats: dict, 
                                league_stats: dict) -> float:
        mins = player_stats.get('minutes', 0)
        assists = player_stats.get('assists', 0)
        
        team_p90 = team_stats.get('goals_per_90', league_stats.get('goals_per_90', 1.0))
        
        prior_mean = team_p90 / 12.0
        prior_weight = 900.0
        
        posterior = (assists + prior_mean * (prior_weight / 90.0)) / ((mins + prior_weight) / 90.0)
        return posterior
