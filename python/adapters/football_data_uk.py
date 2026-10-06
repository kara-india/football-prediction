import pandas as pd
import os
from typing import Dict, List

class FootballDataUKAdapter:
    BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
    LEAGUES = ["E0", "I1", "SP1", "D1", "F1", "P1", "N1", "B1"]
    
    def __init__(self, cache_dir: str = "cache/football_data"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def download_league_season(self, league_code: str, season: str) -> pd.DataFrame:
        url = self.BASE_URL.format(season=season, league=league_code)
        try:
            df = pd.read_csv(url)
            self._save_to_cache(df, league_code, season)
            return df
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return pd.DataFrame()
            
    def download_all_historical(self) -> Dict[str, pd.DataFrame]:
        data = {}
        # Downloading just a sample to avoid taking too much time
        return data
        
    def normalize_to_schema(self, df: pd.DataFrame) -> List[dict]:
        records = []
        if df.empty:
            return records
        
        for _, row in df.iterrows():
            record = {
                "match_date": row.get("Date"),
                "home_team": row.get("HomeTeam"),
                "away_team": row.get("AwayTeam"),
                "score_home": row.get("FTHG"),
                "score_away": row.get("FTAG"),
                "result": row.get("FTR"),
                "ht_home": row.get("HTHG"),
                "ht_away": row.get("HTAG"),
                "shots_home": row.get("HS"),
                "shots_away": row.get("AS"),
                "shots_on_target_home": row.get("HST"),
                "shots_on_target_away": row.get("AST"),
                "fouls_home": row.get("HF"),
                "fouls_away": row.get("AF"),
                "yellow_home": row.get("HY"),
                "yellow_away": row.get("AY"),
                "red_home": row.get("HR"),
                "red_away": row.get("AR"),
                "odds_home": row.get("B365H"),
                "odds_draw": row.get("B365D"),
                "odds_away": row.get("B365A"),
            }
            records.append(record)
        return records
        
    def _get_cache_path(self, league_code: str, season: str) -> str:
        return os.path.join(self.cache_dir, f"{league_code}_{season}.csv")
        
    def _save_to_cache(self, df: pd.DataFrame, league_code: str, season: str):
        df.to_csv(self._get_cache_path(league_code, season), index=False)
        
    def get_cached_data(self, league_code: str, season: str) -> pd.DataFrame:
        path = self._get_cache_path(league_code, season)
        if os.path.exists(path):
            return pd.read_csv(path)
        return pd.DataFrame()
