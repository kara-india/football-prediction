"""
Point-in-Time Historical State Reconstructor & No-Lookahead Invariant Engine
Strictly enforces temporal boundaries: for all entities e in State(T), e.available_at <= T.
Prevents data leakage across historical matches, team Elo ratings, EWMA form,
confirmed lineups, betting odds, and in-play match events.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

from python.models.elo import EloSystem
from python.models.form import FormCalculator, MultiDimensionalForm
from python.data_contracts import CanonicalMatch, CanonicalOddsMarket, CanonicalEvent

logger = logging.getLogger(__name__)


def _to_datetime_utc(val: Any) -> Optional[datetime]:
    """Parse string or datetime object into timezone-aware UTC datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    if isinstance(val, str):
        val_clean = val.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(val_clean)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
                try:
                    dt = datetime.strptime(val_clean, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
    return None


class PointInTimeReplayer:
    """
    Point-in-time state reconstructor as of any historical timestamp T.
    Enforces the No-Lookahead Invariant: for all entities e in State(T), e.available_at <= T.
    """

    def __init__(self, default_elo_k: float = 32.0, default_form_half_life: float = 5.0):
        self.default_elo_k = default_elo_k
        self.default_form_half_life = default_form_half_life

    def filter_matches_strictly_before(
        self,
        matches: List[Union[CanonicalMatch, Dict[str, Any]]],
        as_of_time: datetime,
    ) -> List[Union[CanonicalMatch, Dict[str, Any]]]:
        """
        Reconstruct historical matches available strictly before or at T.
        Excludes any match kicking off at or after T, or whose result was published after T.
        """
        target_t = _to_datetime_utc(as_of_time)
        if target_t is None:
            raise ValueError("as_of_time must be a valid datetime")

        valid_matches = []
        for m in matches:
            # Check availability timestamp
            avail_dt = None
            kickoff_dt = None

            if isinstance(m, CanonicalMatch):
                avail_dt = _to_datetime_utc(m.available_at)
                kickoff_dt = _to_datetime_utc(m.kickoff_utc)
            elif isinstance(m, dict):
                avail_dt = _to_datetime_utc(m.get("available_at") or m.get("source_timestamp"))
                kickoff_dt = _to_datetime_utc(
                    m.get("kickoff_utc") or m.get("date") or m.get("match_date")
                )

            # Fallback if available_at is absent: finished match results are available ~2h after kickoff
            if avail_dt is None and kickoff_dt is not None:
                avail_dt = kickoff_dt + timedelta(minutes=115)

            # Invariant: match and its outcome must have occurred and been recorded strictly <= T
            if avail_dt is not None:
                if avail_dt <= target_t:
                    valid_matches.append(m)
            elif kickoff_dt is not None:
                if kickoff_dt < target_t:
                    valid_matches.append(m)

        return valid_matches

    def compute_elo_at(
        self,
        historical_matches: List[Union[CanonicalMatch, Dict[str, Any]]],
        as_of_time: datetime,
    ) -> EloSystem:
        """
        Reconstruct dynamic team Elo ratings strictly before T.
        """
        prior_matches = self.filter_matches_strictly_before(historical_matches, as_of_time)
        elo = EloSystem()
        elo.K_FACTOR = self.default_elo_k

        # Normalize matches to list of dicts sorted chronologically
        normalized_history = []
        for m in prior_matches:
            if isinstance(m, CanonicalMatch):
                home_id = m.home_team_id
                away_id = m.away_team_id
                # CanonicalMatch does not store goals directly; retrieve from metadata if dict
                match_dt = m.kickoff_utc
                h_goals = getattr(m, "home_goals", 0)
                a_goals = getattr(m, "away_goals", 0)
            else:
                home_id = m.get("home_team_id") or m.get("home_id") or m.get("home_team")
                away_id = m.get("away_team_id") or m.get("away_id") or m.get("away_team")
                h_goals = m.get("home_goals") if m.get("home_goals") is not None else m.get("fthg", 0)
                a_goals = m.get("away_goals") if m.get("away_goals") is not None else m.get("ftag", 0)
                match_dt = _to_datetime_utc(m.get("kickoff_utc") or m.get("date") or m.get("match_date"))

            normalized_history.append({
                "home_id": home_id,
                "away_id": away_id,
                "home_goals": int(h_goals or 0),
                "away_goals": int(a_goals or 0),
                "date": match_dt or datetime.min.replace(tzinfo=timezone.utc),
            })

        normalized_history.sort(key=lambda x: x["date"])
        for m in normalized_history:
            elo.update(m["home_id"], m["away_id"], m["home_goals"], m["away_goals"])

        return elo

    def compute_form_at(
        self,
        historical_matches: List[Union[CanonicalMatch, Dict[str, Any]]],
        as_of_time: datetime,
        team_id: Any,
        half_life_matches: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Reconstruct dynamic EWMA form strictly before T for a specific team.
        """
        hl = half_life_matches or self.default_form_half_life
        calc = FormCalculator(half_life_matches=hl)
        prior_matches = self.filter_matches_strictly_before(historical_matches, as_of_time)

        team_results = []
        for m in prior_matches:
            if isinstance(m, dict):
                h_id = m.get("home_team_id") or m.get("home_id") or m.get("home_team")
                a_id = m.get("away_team_id") or m.get("away_id") or m.get("away_team")
                h_goals = m.get("home_goals") if m.get("home_goals") is not None else m.get("fthg", 0)
                a_goals = m.get("away_goals") if m.get("away_goals") is not None else m.get("ftag", 0)
                m_dt = _to_datetime_utc(m.get("kickoff_utc") or m.get("date") or m.get("match_date"))

                if h_id == team_id:
                    team_results.append({
                        "date": m_dt,
                        "goals_scored": float(h_goals or 0),
                        "goals_conceded": float(a_goals or 0),
                        "points": 3.0 if (h_goals or 0) > (a_goals or 0) else (1.0 if h_goals == a_goals else 0.0),
                    })
                elif a_id == team_id:
                    team_results.append({
                        "date": m_dt,
                        "goals_scored": float(a_goals or 0),
                        "goals_conceded": float(h_goals or 0),
                        "points": 3.0 if (a_goals or 0) > (h_goals or 0) else (1.0 if a_goals == h_goals else 0.0),
                    })

        team_results.sort(key=lambda x: x["date"] or datetime.min.replace(tzinfo=timezone.utc))

        if not team_results:
            return {"form_points": 0.0, "form_goals_scored": 0.0, "form_goals_conceded": 0.0, "matches_counted": 0}

        form_pts = calc.calculate_ewma_form(team_results, "points")
        form_gs = calc.calculate_ewma_form(team_results, "goals_scored")
        form_gc = calc.calculate_ewma_form(team_results, "goals_conceded")

        return {
            "form_points": form_pts,
            "form_goals_scored": form_gs,
            "form_goals_conceded": form_gc,
            "matches_counted": len(team_results),
        }

    def reconstruct_lineup_at(
        self,
        lineup_data: Optional[Dict[str, Any]],
        kickoff_time: datetime,
        as_of_time: datetime,
    ) -> Dict[str, Any]:
        """
        Reconstruct confirmed lineup state as of timestamp T.
        Enforces:
        - If publication timestamp > T, lineup is hidden (None).
        - If publication timestamp is unverified, tag lineup_availability_timestamp_quality = "UNKNOWN".
        - If verified <= T, lineup is visible and tagged "VERIFIED".
        """
        t = _to_datetime_utc(as_of_time)
        ko = _to_datetime_utc(kickoff_time)

        if lineup_data is None:
            return {
                "lineup": None,
                "lineup_confirmed": False,
                "lineup_availability_timestamp_quality": "UNKNOWN",
                "reason": "NO_LINEUP_DATA",
            }

        # Check for verified announcement timestamp
        pub_time_raw = (
            lineup_data.get("published_at")
            or lineup_data.get("available_at")
            or lineup_data.get("verified_at")
            or lineup_data.get("timestamp")
        )
        pub_dt = _to_datetime_utc(pub_time_raw)

        if pub_dt is not None:
            # Exact verified timestamp exists
            quality = "VERIFIED"
            if pub_dt > t:
                # Lineup not yet published as of T
                return {
                    "lineup": None,
                    "lineup_confirmed": False,
                    "lineup_availability_timestamp_quality": quality,
                    "reason": "FUTURE_PUBLICATION",
                    "published_at": pub_dt.isoformat(),
                }
            else:
                return {
                    "lineup": lineup_data,
                    "lineup_confirmed": True,
                    "lineup_availability_timestamp_quality": quality,
                    "published_at": pub_dt.isoformat(),
                }
        else:
            # Exact publication timestamp is unverified!
            quality = "UNKNOWN"
            # Fallback: Official lineups are strictly published ~60 minutes before kickoff (T-60m window).
            # If as_of_time is prior to T-60m, lineup is strictly hidden to prevent lookahead leak.
            t_minus_60 = ko - timedelta(minutes=60)
            if t < t_minus_60:
                return {
                    "lineup": None,
                    "lineup_confirmed": False,
                    "lineup_availability_timestamp_quality": quality,
                    "reason": "PRE_ANNOUNCEMENT_WINDOW",
                }
            else:
                return {
                    "lineup": lineup_data,
                    "lineup_confirmed": True,
                    "lineup_availability_timestamp_quality": quality,
                    "reason": "ESTIMATED_WINDOW",
                }

    def reconstruct_odds_at(
        self,
        odds_snapshots: List[Dict[str, Any]],
        kickoff_time: datetime,
        as_of_time: datetime,
    ) -> Optional[Dict[str, Any]]:
        """
        Reconstruct 1xBet odds available at or before T.
        Enforces:
        - Kickoff or closing odds are strictly invisible prior to kickoff (T < kickoff).
        - Any snapshot taken after T is invisible.
        """
        t = _to_datetime_utc(as_of_time)
        ko = _to_datetime_utc(kickoff_time)

        valid_snapshots = []
        for snap in odds_snapshots:
            snap_time = _to_datetime_utc(
                snap.get("available_at") or snap.get("timestamp") or snap.get("source_timestamp")
            )
            is_closing = snap.get("is_closing", False) or snap.get("stage") == "CLOSING"

            # If snapshot is marked as closing odds or at kickoff, it is strictly invisible prior to kickoff
            if is_closing and t < ko:
                continue

            if snap_time is not None:
                if snap_time <= t:
                    # Also guard against closing snapshot dated after kickoff being read before kickoff
                    if snap_time >= ko and t < ko:
                        continue
                    valid_snapshots.append((snap_time, snap))
            else:
                # If no timestamp, can only be used if not marked as closing and T is within safe pre-match
                if not is_closing and t <= ko:
                    valid_snapshots.append((datetime.min.replace(tzinfo=timezone.utc), snap))

        if not valid_snapshots:
            return None

        # Return latest snapshot available as of T
        valid_snapshots.sort(key=lambda x: x[0])
        return valid_snapshots[-1][1]

    def filter_inplay_events(
        self,
        events: List[Dict[str, Any]],
        current_minute: int,
        as_of_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter in-play events occurring strictly <= current_minute and <= as_of_time.
        Prevents future events (e.g. 80' red card) from leaking into earlier minute state (e.g. 20').
        """
        t = _to_datetime_utc(as_of_time) if as_of_time is not None else None
        valid_events = []

        for e in events:
            # Check minute boundary
            ev_min = e.get("minute", 0)
            if ev_min > current_minute:
                continue

            # Check timestamp boundary if present
            if t is not None:
                ev_time = _to_datetime_utc(
                    e.get("available_at") or e.get("timestamp") or e.get("source_timestamp")
                )
                if ev_time is not None and ev_time > t:
                    continue

            valid_events.append(e)

        return valid_events

    def validate_no_lookahead(
        self,
        features: Dict[str, Any],
        as_of_time: datetime,
        future_events: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Validate No-Lookahead Invariant:
        For all entities e in features, e.available_at <= as_of_time.
        Also asserts that no event in future_events was used or included in features.
        """
        t = _to_datetime_utc(as_of_time)
        if t is None:
            raise ValueError("as_of_time must be a valid datetime")

        # 1. Check future events leakage
        if future_events:
            for ev in future_events:
                # If event is explicitly marked 'used' or present in features
                if ev.get("used", False):
                    ev_time = _to_datetime_utc(ev.get("timestamp") or ev.get("available_at"))
                    ev_min = ev.get("minute", None)
                    current_min = features.get("minute", None)
                    if ev_time and ev_time > t:
                        return False
                    if current_min is not None and ev_min is not None and ev_min > current_min:
                        return False

        # 2. Check all feature values recursively
        def _check_val(v: Any) -> bool:
            if isinstance(v, datetime):
                v_dt = _to_datetime_utc(v)
                if v_dt and v_dt > t:
                    return False
            elif isinstance(v, dict):
                for time_key in ("available_at", "timestamp", "source_timestamp", "published_at", "match_date"):
                    if time_key in v:
                        dt_val = _to_datetime_utc(v[time_key])
                        if dt_val and dt_val > t:
                            return False
                for sub_v in v.values():
                    if not _check_val(sub_v):
                        return False
            elif isinstance(v, list):
                for item in v:
                    if not _check_val(item):
                        return False
            return True

        return _check_val(features)

    def reconstruct_state(
        self,
        as_of_time: datetime,
        match: Dict[str, Any],
        historical_matches: List[Dict[str, Any]],
        lineup_data: Optional[Dict[str, Any]] = None,
        odds_snapshots: Optional[List[Dict[str, Any]]] = None,
        inplay_events: Optional[List[Dict[str, Any]]] = None,
        current_minute: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Construct a complete, point-in-time verified State(T).
        """
        t = _to_datetime_utc(as_of_time)
        ko = _to_datetime_utc(match.get("kickoff_utc") or match.get("date"))

        # 1. Elo and Form ratings as of T
        elo = self.compute_elo_at(historical_matches, t)
        home_id = match.get("home_team_id") or match.get("home_id") or match.get("home_team")
        away_id = match.get("away_team_id") or match.get("away_id") or match.get("away_team")

        home_form = self.compute_form_at(historical_matches, t, home_id)
        away_form = self.compute_form_at(historical_matches, t, away_id)

        # 2. Lineup as of T
        lineup_state = self.reconstruct_lineup_at(lineup_data, ko or t, t)

        # 3. Odds as of T
        odds_state = self.reconstruct_odds_at(odds_snapshots or [], ko or t, t)

        # 4. In-play events if live
        events_state = []
        if inplay_events is not None and current_minute is not None:
            events_state = self.filter_inplay_events(inplay_events, current_minute, t)

        state = {
            "as_of_time": t,
            "match": match,
            "home_elo": elo.get_rating(home_id),
            "away_elo": elo.get_rating(away_id),
            "home_form": home_form,
            "away_form": away_form,
            "lineup_state": lineup_state,
            "odds_state": odds_state,
            "inplay_events": events_state,
            "current_minute": current_minute,
        }

        # Verify invariant
        if not self.validate_no_lookahead(state, t):
            raise ValueError(f"No-Lookahead Invariant violated in reconstructed state as of {t}")

        return state
