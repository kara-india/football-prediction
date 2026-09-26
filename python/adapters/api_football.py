import time
import logging
import os
import requests
from requests.adapters import HTTPAdapter
from functools import lru_cache
from typing import List, Dict, Optional, Any
from ..data_pipeline.cache import DataCache

from .quota_manager import CentralQuotaManager, QuotaExceededError

class APIError(Exception):
    pass

class DataNotAvailableError(Exception):
    pass

class APIFootballAdapter:
    def __init__(self, api_key: Optional[str] = None, cache: DataCache = None, quota_manager: Optional[CentralQuotaManager] = None):
        self.base_url = 'https://v3.football.api-sports.io'
        self.api_key = api_key or os.environ.get("API_FOOTBALL_KEY")
        self.headers = {'x-apisports-key': self.api_key} if self.api_key else {}
        self.cache = cache or DataCache()
        self.quota_manager = quota_manager or CentralQuotaManager()
        
        self.logger = logging.getLogger("APIFootball")
        handler = logging.FileHandler("requests.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Do not hide retries inside the HTTP adapter: every external attempt must
        # consume an explicit centralized quota reservation.
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(max_retries=0))

    @property
    def quota_remaining(self) -> int:
        status = self.quota_manager.get_status()
        if not status.get("available"):
            return 0
        return int(status.get("remaining_worker", 0))
        
    def _make_request(self, endpoint: str, params: Dict = None, ttl: int = 60, is_user: bool = False) -> Any:
        cache_key = f"{endpoint}_{params}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
            
        # Reserve exactly once for this actual outbound HTTP attempt.
        self.quota_manager.reserve(is_user=is_user, cost=1)

        if not self.api_key:
            raise APIError("API_FOOTBALL_KEY is not configured; refusing external API call.")

        url = f"{self.base_url}/{endpoint}"
        self.logger.info(f"Request: {url} {params}")
        
        response = self.session.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            raise APIError(f"API Error {response.status_code}: {response.text}")
            
        data = response.json()
        
        if 'errors' in data and data['errors']:
            err = data['errors']
            if isinstance(err, dict) and 'rateLimit' in err:
                raise QuotaExceededError("Rate limit reached")
            raise APIError(f"API returned errors: {err}")
        
        result = data.get('response', [])
        self.cache.set(cache_key, result, ttl)
        return result

    def health_check(self) -> dict:
        data = self._make_request('status', ttl=0)
        return data

    def get_fixtures(self, league_id: int, season: int, date: str = None, live: bool = False, status: str = None) -> List[Dict]:
        params = {"league": league_id, "season": season}
        if date: params["date"] = date
        if live: params["live"] = "all"
        if status: params["status"] = status
        return self._make_request('fixtures', params, ttl=300)
        
    def get_fixture(self, fixture_id: int) -> Dict:
        params = {"id": fixture_id, "statistics": "true", "events": "true", "lineups": "true"}
        res = self._make_request('fixtures', params, ttl=300)
        if not res: raise DataNotAvailableError(f"Fixture {fixture_id} not found")
        return res[0]

    def get_live_fixtures(self, league_ids: List[int]) -> List[Dict]:
        if not league_ids:
            return []
        params = {"live": "-".join(map(str, league_ids))}
        return self._make_request('fixtures', params, ttl=30)

    def get_fixture_lineups(self, fixture_id: int) -> List[Dict]:
        res = self._make_request('fixtures/lineups', {"fixture": fixture_id}, ttl=600)
        return res

    def get_fixture_events(self, fixture_id: int) -> List[Dict]:
        return self._make_request('fixtures/events', {"fixture": fixture_id}, ttl=300)

    def get_fixture_statistics(self, fixture_id: int) -> Dict:
        res = self._make_request('fixtures/statistics', {"fixture": fixture_id}, ttl=300)
        return res[0] if res else {}

    def get_teams(self, league_id: int, season: int) -> List[Dict]:
        return self._make_request('teams', {"league": league_id, "season": season}, ttl=86400)

    def get_team(self, team_id: int) -> Dict:
        res = self._make_request('teams', {"id": team_id}, ttl=86400)
        return res[0] if res else {}

    def get_players(self, team_id: int, season: int, page: int = 1) -> List[Dict]:
        return self._make_request('players', {"team": team_id, "season": season, "page": page}, ttl=86400)

    def get_player_statistics(self, player_id: int, season: int, league_id: int = None) -> Dict:
        params = {"id": player_id, "season": season}
        if league_id: params["league"] = league_id
        res = self._make_request('players', params, ttl=3600)
        return res[0] if res else {}

    def get_injuries(self, league_id: int = None, team_id: int = None, fixture_id: int = None) -> List[Dict]:
        params = {}
        if league_id: params["league"] = league_id
        if team_id: params["team"] = team_id
        if fixture_id: params["fixture"] = fixture_id
        return self._make_request('injuries', params, ttl=3600)

    def get_standings(self, league_id: int, season: int) -> List[Dict]:
        return self._make_request('standings', {"league": league_id, "season": season}, ttl=1800)

    def get_h2h(self, team1_id: int, team2_id: int, last: int = 10) -> List[Dict]:
        return self._make_request('fixtures/headtohead', {"h2h": f"{team1_id}-{team2_id}", "last": last}, ttl=86400)

    def get_odds(self, fixture_id: int = None, league_id: int = None, bookmaker_id: int = 6) -> List[Dict]:
        params = {"bookmaker": bookmaker_id}
        if fixture_id: params["fixture"] = fixture_id
        if league_id: params["league"] = league_id
        return self._make_request('odds', params, ttl=60)
