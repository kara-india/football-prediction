from python.simulation.match_state import MatchState


def test_first_half_live_state_includes_second_half():
    state = MatchState(
        minute=28,
        added_time=0,
        score_home=0,
        score_away=1,
        period="first_half",
        possession_home=50.0,
        shots_home=0,
        shots_away=0,
        shots_on_target_home=0,
        shots_on_target_away=0,
        xg_home=0.0,
        xg_away=0.0,
        corners_home=0,
        corners_away=0,
        fouls_home=0,
        fouls_away=0,
        yellow_cards_home=0,
        yellow_cards_away=0,
        red_cards_home=0,
        red_cards_away=0,
        offsides_home=0,
        offsides_away=0,
        substitutions_home=0,
        substitutions_away=0,
        is_live=True,
        lineup_confirmed=True,
    )
    assert state.remaining_minutes == 62


def test_second_half_live_state_uses_time_to_full_time():
    state = MatchState(
        minute=54,
        added_time=0,
        score_home=3,
        score_away=1,
        period="second_half",
        possession_home=50.0,
        shots_home=0,
        shots_away=0,
        shots_on_target_home=0,
        shots_on_target_away=0,
        xg_home=0.0,
        xg_away=0.0,
        corners_home=0,
        corners_away=0,
        fouls_home=0,
        fouls_away=0,
        yellow_cards_home=0,
        yellow_cards_away=0,
        red_cards_home=0,
        red_cards_away=0,
        offsides_home=0,
        offsides_away=0,
        substitutions_home=0,
        substitutions_away=0,
        is_live=True,
        lineup_confirmed=True,
    )
    assert state.remaining_minutes == 36
