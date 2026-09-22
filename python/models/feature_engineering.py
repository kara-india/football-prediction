from datetime import datetime

class FeatureEngineer:
    def compute_pre_match_features(self, match: dict, 
                                    home_team_stats: dict,
                                    away_team_stats: dict,
                                    home_players: list[dict],
                                    away_players: list[dict],
                                    h2h_matches: list[dict],
                                    referee_stats: dict,
                                    weather: dict = None) -> dict:
        features = {}
        features['home_form'] = home_team_stats.get('form', 0.0)
        features['away_form'] = away_team_stats.get('form', 0.0)
        return features
        
    def compute_live_features(self, match: dict,
                               live_state: dict,
                               home_team_stats: dict,
                               away_team_stats: dict) -> dict:
        features = {}
        features['minute'] = live_state.get('minute', 0)
        features['score_home'] = live_state.get('score_home', 0)
        features['score_away'] = live_state.get('score_away', 0)
        features['possession'] = live_state.get('possession', 0.5)
        features['shots'] = live_state.get('shots', 0)
        features['xg'] = live_state.get('xg', 0.0)
        return features
        
    def validate_no_lookahead(self, features: dict, prediction_timestamp: datetime) -> bool:
        for k, v in features.items():
            if isinstance(v, datetime) and v > prediction_timestamp:
                return False
            if isinstance(v, dict) and 'timestamp' in v:
                if v['timestamp'] > prediction_timestamp:
                    return False
        return True
