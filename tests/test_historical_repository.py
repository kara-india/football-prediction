import pandas as pd

from python.data.historical_repository import HistoricalMatchRepository


def test_historical_repository_maps_database_schema_to_model_schema():
    source = pd.DataFrame([
        {
            "id": 1,
            "league_code": "E0",
            "league_name": "Premier League (England)",
            "match_date": "2024-05-19",
            "home_team": "Arsenal",
            "away_team": "Everton",
            "fthg": 2,
            "ftag": 1,
        }
    ])

    out = HistoricalMatchRepository.to_model_frame(source)

    assert out.loc[0, "home_id"] == "Arsenal"
    assert out.loc[0, "away_id"] == "Everton"
    assert out.loc[0, "home_goals"] == 2
    assert out.loc[0, "away_goals"] == 1
    assert pd.Timestamp(out.loc[0, "date"]).tz is not None


def test_historical_repository_rejects_missing_goal_fields():
    source = pd.DataFrame([
        {
            "id": 1,
            "home_team": "A",
            "away_team": "B",
            "match_date": "2024-01-01",
        }
    ])

    try:
        HistoricalMatchRepository.to_model_frame(source)
    except ValueError as exc:
        assert "required fields" in str(exc)
    else:
        raise AssertionError("Repository accepted incomplete historical data.")
