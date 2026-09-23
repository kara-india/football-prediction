"""
Automated Test Suite for Point-in-Time State Reconstruction & No-Lookahead Invariant
Validates mathematical and temporal integrity: for all entities e in State(T), e.available_at <= T.
Zero empty try/except blocks permitted.
"""
from datetime import datetime, timezone, timedelta
import pytest

from python.backtesting.point_in_time_replayer import PointInTimeReplayer
from python.backtesting.historical_replayer import HistoricalReplayer
from python.models.elo import EloSystem
from python.data_contracts import CanonicalMatch


def test_historical_replayer_filtering():
    """Verify legacy HistoricalReplayer filtering retains events <= snapshot minute."""
    hr = HistoricalReplayer()
    events = [{"minute": 60, "type": "sub"}, {"minute": 61, "type": "goal"}]
    state = hr._reconstruct_state_at({}, events, 60)
    assert len(state["events"]) == 1
    assert state["events"][0]["minute"] == 60


def test_validate_no_lookahead_fails_on_future():
    """Verify legacy validate_no_lookahead flags future events."""
    hr = HistoricalReplayer()
    events = [{"minute": 30, "type": "goal", "used": True}]
    assert not hr.validate_no_lookahead({}, 25, events)


def test_matches_after_T_are_strictly_invisible():
    """Matches kicking off or finishing after timestamp T must be strictly invisible."""
    replayer = PointInTimeReplayer()
    t_checkpoint = datetime(2023, 10, 15, 14, 0, tzinfo=timezone.utc)

    matches = [
        {
            "match_id": "match_past",
            "home_id": 1,
            "away_id": 2,
            "home_goals": 2,
            "away_goals": 1,
            "kickoff_utc": datetime(2023, 10, 10, 15, 0, tzinfo=timezone.utc),
            "available_at": datetime(2023, 10, 10, 17, 0, tzinfo=timezone.utc),
        },
        {
            "match_id": "match_future",
            "home_id": 1,
            "away_id": 3,
            "home_goals": 3,
            "away_goals": 0,
            "kickoff_utc": datetime(2023, 10, 15, 16, 0, tzinfo=timezone.utc),
            "available_at": datetime(2023, 10, 15, 18, 0, tzinfo=timezone.utc),
        },
        {
            "match_id": "match_tomorrow",
            "home_id": 2,
            "away_id": 3,
            "home_goals": 1,
            "away_goals": 1,
            "kickoff_utc": datetime(2023, 10, 16, 12, 0, tzinfo=timezone.utc),
            "available_at": datetime(2023, 10, 16, 14, 0, tzinfo=timezone.utc),
        },
    ]

    visible = replayer.filter_matches_strictly_before(matches, as_of_time=t_checkpoint)
    visible_ids = [m["match_id"] for m in visible]

    assert "match_past" in visible_ids
    assert "match_future" not in visible_ids
    assert "match_tomorrow" not in visible_ids
    assert len(visible) == 1


def test_lineups_after_T_are_strictly_invisible():
    """Lineups published after T must remain hidden."""
    replayer = PointInTimeReplayer()
    kickoff = datetime(2023, 11, 1, 15, 0, tzinfo=timezone.utc)
    pub_time = datetime(2023, 11, 1, 14, 0, tzinfo=timezone.utc)  # T-60m

    raw_lineup = {
        "published_at": pub_time.isoformat(),
        "home_xi": ["Player A", "Player B"],
        "away_xi": ["Player X", "Player Y"],
    }

    # As of T-75m (13:45 UTC), lineup was not yet published
    t_early = datetime(2023, 11, 1, 13, 45, tzinfo=timezone.utc)
    state_early = replayer.reconstruct_lineup_at(raw_lineup, kickoff, t_early)
    assert state_early["lineup"] is None
    assert state_early["lineup_confirmed"] is False
    assert state_early["lineup_availability_timestamp_quality"] == "VERIFIED"
    assert state_early["reason"] == "FUTURE_PUBLICATION"

    # As of T-55m (14:05 UTC), lineup was published
    t_after_pub = datetime(2023, 11, 1, 14, 5, tzinfo=timezone.utc)
    state_visible = replayer.reconstruct_lineup_at(raw_lineup, kickoff, t_after_pub)
    assert state_visible["lineup"] is not None
    assert state_visible["lineup_confirmed"] is True
    assert state_visible["lineup_availability_timestamp_quality"] == "VERIFIED"


def test_unverified_lineup_tagged_unknown():
    """If exact publication timestamp is unverified, tag quality as 'UNKNOWN'."""
    replayer = PointInTimeReplayer()
    kickoff = datetime(2023, 11, 1, 15, 0, tzinfo=timezone.utc)

    # Lineup data missing published_at / available_at
    unverified_lineup = {
        "home_xi": ["Player A", "Player B"],
        "away_xi": ["Player X", "Player Y"],
    }

    # At T-90m: before standard window, must be hidden to prevent leak
    t_early = datetime(2023, 11, 1, 13, 30, tzinfo=timezone.utc)
    state_early = replayer.reconstruct_lineup_at(unverified_lineup, kickoff, t_early)
    assert state_early["lineup"] is None
    assert state_early["lineup_availability_timestamp_quality"] == "UNKNOWN"

    # At T-45m: within window, may be present but tagged UNKNOWN
    t_window = datetime(2023, 11, 1, 14, 15, tzinfo=timezone.utc)
    state_window = replayer.reconstruct_lineup_at(unverified_lineup, kickoff, t_window)
    assert state_window["lineup"] is not None
    assert state_window["lineup_availability_timestamp_quality"] == "UNKNOWN"


def test_inplay_future_events_cannot_affect_earlier_state():
    """An 80' red card or 90' goal cannot affect minute 20 state."""
    replayer = PointInTimeReplayer()
    events = [
        {"minute": 10, "type": "YELLOW_CARD", "team": "Home"},
        {"minute": 18, "type": "CORNER", "team": "Away"},
        {"minute": 25, "type": "GOAL", "team": "Home"},
        {"minute": 80, "type": "RED_CARD", "team": "Away"},
        {"minute": 90, "type": "GOAL", "team": "Away"},
    ]

    filtered_at_20 = replayer.filter_inplay_events(events, current_minute=20)
    assert len(filtered_at_20) == 2
    assert [e["minute"] for e in filtered_at_20] == [10, 18]
    assert all(e["minute"] <= 20 for e in filtered_at_20)

    # Verify 80' red card is completely absent
    assert not any(e["type"] == "RED_CARD" for e in filtered_at_20)


def test_future_odds_cannot_leak_into_prematch_predictions():
    """Closing / kickoff odds snapshots are strictly invisible prior to kickoff."""
    replayer = PointInTimeReplayer()
    kickoff = datetime(2023, 12, 1, 15, 0, tzinfo=timezone.utc)

    snapshots = [
        {
            "snapshot_id": "snap_early",
            "available_at": datetime(2023, 11, 30, 10, 0, tzinfo=timezone.utc),
            "odds_home": 2.20,
            "is_closing": False,
        },
        {
            "snapshot_id": "snap_t_minus_1h",
            "available_at": datetime(2023, 12, 1, 14, 0, tzinfo=timezone.utc),
            "odds_home": 2.10,
            "is_closing": False,
        },
        {
            "snapshot_id": "snap_closing",
            "available_at": datetime(2023, 12, 1, 15, 0, tzinfo=timezone.utc),
            "odds_home": 1.95,
            "is_closing": True,
        },
    ]

    # At T-2h (13:00 UTC), only early snapshot is visible
    odds_at_13h = replayer.reconstruct_odds_at(
        snapshots, kickoff, as_of_time=datetime(2023, 12, 1, 13, 0, tzinfo=timezone.utc)
    )
    assert odds_at_13h["snapshot_id"] == "snap_early"

    # At T-30m (14:30 UTC), T-1h snapshot is visible, but closing odds are invisible
    odds_at_1430 = replayer.reconstruct_odds_at(
        snapshots, kickoff, as_of_time=datetime(2023, 12, 1, 14, 30, tzinfo=timezone.utc)
    )
    assert odds_at_1430["snapshot_id"] == "snap_t_minus_1h"

    # At Kickoff (15:00 UTC), closing odds are visible
    odds_at_ko = replayer.reconstruct_odds_at(
        snapshots, kickoff, as_of_time=datetime(2023, 12, 1, 15, 0, tzinfo=timezone.utc)
    )
    assert odds_at_ko["snapshot_id"] == "snap_closing"


def test_validate_no_lookahead_invariant():
    """Assert validate_no_lookahead returns False on any injected future timestamp."""
    replayer = PointInTimeReplayer()
    t_target = datetime(2023, 5, 1, 12, 0, tzinfo=timezone.utc)

    valid_features = {
        "home_elo": 1550.0,
        "away_elo": 1480.0,
        "timestamp": datetime(2023, 5, 1, 11, 0, tzinfo=timezone.utc),
        "nested": {"available_at": datetime(2023, 5, 1, 11, 30, tzinfo=timezone.utc)},
    }
    assert replayer.validate_no_lookahead(valid_features, as_of_time=t_target) is True

    # Inject future timestamp
    leaked_features = {
        "home_elo": 1550.0,
        "away_elo": 1480.0,
        "timestamp": datetime(2023, 5, 1, 13, 0, tzinfo=timezone.utc),  # > t_target!
    }
    assert replayer.validate_no_lookahead(leaked_features, as_of_time=t_target) is False


def test_elo_reconstruction_strictly_uses_prior_matches():
    """Team Elo at T must reflect only matches completed before T."""
    replayer = PointInTimeReplayer()

    matches = [
        {
            "home_id": 1,
            "away_id": 2,
            "home_goals": 3,
            "away_goals": 0,
            "kickoff_utc": datetime(2023, 1, 1, 15, 0, tzinfo=timezone.utc),
            "available_at": datetime(2023, 1, 1, 17, 0, tzinfo=timezone.utc),
        },
        {
            "home_id": 1,
            "away_id": 2,
            "home_goals": 0,
            "away_goals": 5,
            "kickoff_utc": datetime(2023, 6, 1, 15, 0, tzinfo=timezone.utc),
            "available_at": datetime(2023, 6, 1, 17, 0, tzinfo=timezone.utc),
        },
    ]

    # Reconstruct at Feb 1, 2023 (after match 1, before match 2)
    t_feb = datetime(2023, 2, 1, 0, 0, tzinfo=timezone.utc)
    elo_feb = replayer.compute_elo_at(matches, t_feb)

    # After winning match 1, team 1 rating should be higher than default 1500
    assert elo_feb.get_rating(1) > 1500.0
    assert elo_feb.get_rating(2) < 1500.0
    rating_after_match_1 = elo_feb.get_rating(1)

    # Reconstruct at July 1, 2023 (after match 2)
    t_july = datetime(2023, 7, 1, 0, 0, tzinfo=timezone.utc)
    elo_july = replayer.compute_elo_at(matches, t_july)

    # After losing match 2 0-5, team 1 rating must be lower than after match 1
    assert elo_july.get_rating(1) < rating_after_match_1
