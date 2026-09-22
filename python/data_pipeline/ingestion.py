from typing import List, Dict
from ..adapters.api_football import APIFootballAdapter

class DataIngestionPipeline:
    def __init__(self, api_adapter: APIFootballAdapter = None):
        self.api = api_adapter or APIFootballAdapter()

    def ingest_competition_fixtures(self, league_id: int, season: int) -> int:
        fixtures = self.api.get_fixtures(league_id, season)
        return len(fixtures)

    def ingest_live_matches(self, allowed_league_ids: List[int]) -> int:
        fixtures = self.api.get_live_fixtures(allowed_league_ids)
        return len(fixtures)

    def ingest_fixture_deep(self, fixture_id: int) -> Dict:
        fixture = self.api.get_fixture(fixture_id)
        return fixture

    def ingest_team_data(self, team_id: int) -> Dict:
        return self.api.get_team(team_id)

    def ingest_player_stats(self, player_id: int, season: int) -> Dict:
        return self.api.get_player_statistics(player_id, season)

    def ingest_h2h(self, home_team_id: int, away_team_id: int) -> List[Dict]:
        return self.api.get_h2h(home_team_id, away_team_id)

    def check_lineup_confirmation(self, fixture_id: int) -> bool:
        lineups = self.api.get_fixture_lineups(fixture_id)
        if not lineups:
            return False
        for lineup in lineups:
            starters = lineup.get("startXI", [])
            if not starters:
                return False
        return True

    def sync_competitions(self) -> int:
        return 0
