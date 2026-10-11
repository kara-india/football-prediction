from datetime import timedelta

from python.providers.football_data_uk import (
    canonical_team,
    load_matches,
    load_team_aliases,
)


def test_vendored_completed_epl_seasons_and_point_in_time_cutoff():
    matches = load_matches()

    assert len(matches) == 7 * 380
    assert set(matches["season"]) == {"1920", "2021", "2122", "2223", "2324", "2425", "2526"}
    first = matches.iloc[0]
    assert first["kickoff_utc"].utcoffset().total_seconds() == 0
    assert first["available_at"] - first["kickoff_utc"] == timedelta(hours=3)
    assert matches["opening_b365_home"].notna().any()
    assert matches["closing_b365_home"].notna().any()
    assert matches["closing_b365_over_2_5"].notna().any()

    before_result = load_matches(as_of=first["kickoff_utc"] + timedelta(hours=2))
    after_result = load_matches(as_of=first["available_at"])
    assert len(before_result) == 0
    assert len(after_result) == 1


def test_team_aliases_are_exact_and_cover_vendored_names():
    aliases = load_team_aliases()
    matches = load_matches()
    source_names = set(matches["home_team"]) | set(matches["away_team"])

    assert all(("football_data_uk", name) in aliases for name in source_names)
    assert canonical_team("football_data_uk", "Man City", aliases) == "manchester_city"
    assert canonical_team("football_data_org", "Manchester City FC", aliases) == "manchester_city"
    assert canonical_team("fpl", "MCI", aliases) == "manchester_city"
    assert canonical_team("football_data_uk", "Manchester City", aliases) is None
