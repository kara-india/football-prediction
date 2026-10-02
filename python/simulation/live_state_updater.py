from datetime import datetime
from typing import List
from .match_state import MatchState

class LiveStateUpdater:
    def parse_api_state(self, api_fixture: dict) -> MatchState:
        raise NotImplementedError("Live API state parsing is not implemented in this legacy adapter.")
    
    def is_state_stale(self, state: MatchState, fetched_at: datetime) -> bool:
        raise NotImplementedError("Live state staleness check is not implemented in this legacy adapter.")
    
    def detect_significant_events(self, old_state: MatchState, 
                                   new_state: MatchState) -> List[str]:
        return []
