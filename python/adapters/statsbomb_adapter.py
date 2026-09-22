import pandas as pd
from typing import List, Dict

class StatsBombAdapter:
    def __init__(self):
        pass
        
    def get_available_competitions(self) -> List[Dict]:
        return []
        
    def get_matches(self, competition_id: int, season_id: int) -> List[Dict]:
        return []
        
    def get_match_events(self, match_id: int) -> pd.DataFrame:
        return pd.DataFrame()
        
    def get_shots(self, match_id: int) -> pd.DataFrame:
        return pd.DataFrame()
        
    def calculate_team_xg(self, match_id: int) -> Dict:
        return {"home_xg": 0.0, "away_xg": 0.0}
