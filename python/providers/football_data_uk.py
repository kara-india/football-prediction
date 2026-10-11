"""Local historical Premier League corpus from football-data.co.uk.

This adapter intentionally has no network code. Vendor the E0 season CSVs under
``data/football_data_uk``; training and tests read only those committed files.
Closing prices are historical labels and must not be used as executable live odds.
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "football_data_uk"
ALIASES_PATH = Path(__file__).resolve().parents[2] / "data" / "team_aliases.csv"
LONDON = ZoneInfo("Europe/London")

REQUIRED_COLUMNS = ("Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG")
def _parse_date(raw: str, raw_time: str) -> datetime:
    """Parse source-local kickoff date/time and return timezone-aware UTC."""
    match_date = datetime.strptime(raw.strip(), "%d/%m/%Y").date()
    kickoff = datetime.strptime(raw_time.strip(), "%H:%M").time()
    return datetime.combine(match_date, kickoff, tzinfo=LONDON).astimezone(timezone.utc)


def _read_csv(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    raise ValueError(f"CSV has no header: {path}")
                reader.fieldnames = [name.strip().lstrip("\ufeff") for name in reader.fieldnames]
                missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
                if missing:
                    raise ValueError(f"{path.name} missing required columns: {sorted(missing)}")
                return list(reader)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path}")


def _number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def load_team_aliases(path: Path | str = ALIASES_PATH) -> dict[tuple[str, str], str]:
    """Return exact (source, provider_name) aliases; no fuzzy matching."""
    aliases: dict[tuple[str, str], str] = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["source"].strip(), row["provider_name"].strip())
            canonical = row["canonical_team_id"].strip()
            if not all(key) or not canonical or key in aliases:
                raise ValueError(f"Invalid or duplicate team alias row: {row}")
            aliases[key] = canonical
    return aliases


def canonical_team(source: str, provider_name: str, aliases: dict[tuple[str, str], str]) -> str | None:
    """Resolve an exact provider name; callers must abstain on ``None``."""
    return aliases.get((source, provider_name))


def load_matches(
    data_dir: Path | str = DATA_DIR,
    *,
    as_of: datetime | None = None,
    seasons: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Load committed E0 CSVs into a point-in-time-safe historical frame.

    Results and post-match statistics become available at kickoff + 3 hours.
    Closing odds are retained in explicitly named ``closing_*`` columns for
    training labels only. ``as_of`` filters out rows whose results were not
    yet available at that point in time.
    """
    root = Path(data_dir)
    requested = set(seasons) if seasons is not None else None
    paths = sorted(root.glob("*-E0.csv"))
    if requested is not None:
        paths = [path for path in paths if path.name.split("-", 1)[0] in requested]
    if not paths:
        raise FileNotFoundError(f"No committed E0 season CSVs found in {root}")

    if as_of is not None and as_of.utcoffset() is None:
        raise ValueError("as_of must include a timezone")
    cutoff = as_of.astimezone(timezone.utc) if as_of else None
    aliases = load_team_aliases()
    records: list[dict[str, object]] = []
    for path in paths:
        season_code = path.name.split("-", 1)[0]
        for row in _read_csv(path):
            home = (row.get("HomeTeam") or "").strip()
            away = (row.get("AwayTeam") or "").strip()
            if not home or not away:
                continue
            kickoff = _parse_date(row["Date"], row.get("Time") or "")
            available_at = kickoff + timedelta(hours=3)
            if cutoff and available_at > cutoff:
                continue
            home_goals = _number(row.get("FTHG"))
            away_goals = _number(row.get("FTAG"))
            if home_goals is None or away_goals is None:
                continue
            record: dict[str, object] = {
                "season": season_code,
                "date": pd.Timestamp(kickoff.replace(tzinfo=None)),
                "kickoff_utc": kickoff,
                "available_at": available_at,
                "home_team": home,
                "away_team": away,
                "home_id": canonical_team("football_data_uk", home, aliases),
                "away_id": canonical_team("football_data_uk", away, aliases),
                "home_goals": int(home_goals),
                "away_goals": int(away_goals),
                "home_shots": _number(row.get("HS")),
                "away_shots": _number(row.get("AS")),
                "home_shots_on_target": _number(row.get("HST")),
                "away_shots_on_target": _number(row.get("AST")),
                "opening_b365_home": _number(row.get("B365H")),
                "opening_b365_draw": _number(row.get("B365D")),
                "opening_b365_away": _number(row.get("B365A")),
                "opening_b365_over_2_5": _number(row.get("B365>2.5")),
                "opening_b365_under_2_5": _number(row.get("B365<2.5")),
                "closing_b365_home": _number(row.get("B365CH")),
                "closing_b365_draw": _number(row.get("B365CD")),
                "closing_b365_away": _number(row.get("B365CA")),
                "closing_b365_over_2_5": _number(row.get("B365C>2.5")),
                "closing_b365_under_2_5": _number(row.get("B365C<2.5")),
                "source_file": path.name,
            }
            records.append(record)

    result = pd.DataFrame.from_records(records)
    if result.empty:
        return pd.DataFrame(columns=[
            "season", "date", "kickoff_utc", "available_at", "home_team", "away_team",
            "home_id", "away_id", "home_goals", "away_goals", "home_shots", "away_shots",
            "home_shots_on_target", "away_shots_on_target", "opening_b365_home",
            "opening_b365_draw", "opening_b365_away", "opening_b365_over_2_5",
            "opening_b365_under_2_5", "closing_b365_home", "closing_b365_draw",
            "closing_b365_away", "closing_b365_over_2_5", "closing_b365_under_2_5",
            "source_file",
        ])
    return result.sort_values(["kickoff_utc", "home_id", "away_id"]).reset_index(drop=True)
