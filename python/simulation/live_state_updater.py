from datetime import datetime
from typing import List
from .match_state import MatchState

class LiveStateUpdater:
    def parse_api_state(self, api_fixture: dict) -> MatchState:
        pass
    
    def is_state_stale(self, state: MatchState, fetched_at: datetime) -> bool:
        pass
    
    def detect_significant_events(self, old_state: MatchState, 
                                   new_state: MatchState) -> List[str]:
        return []
