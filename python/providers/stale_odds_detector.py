import datetime

class StaleOddsDetector:
    MAX_AGE_LIVE_SECONDS = 120
    MAX_AGE_PREMATCH_SECONDS = 1800
    
    def get_staleness_seconds(self, odds_timestamp: datetime.datetime) -> int:
        now = datetime.datetime.now(datetime.timezone.utc)
        if odds_timestamp.tzinfo is None:
            odds_timestamp = odds_timestamp.replace(tzinfo=datetime.timezone.utc)
        return int((now - odds_timestamp).total_seconds())

    def is_stale(self, odds_timestamp: datetime.datetime, is_live: bool) -> bool:
        age = self.get_staleness_seconds(odds_timestamp)
        if is_live:
            return age > self.MAX_AGE_LIVE_SECONDS
        return age > self.MAX_AGE_PREMATCH_SECONDS

    def check_odds_snapshot(self, snapshot: dict) -> bool:
        ts = snapshot.get("timestamp")
        if not ts:
            return True
        is_live = snapshot.get("is_live", False)
        return self.is_stale(ts, is_live)
