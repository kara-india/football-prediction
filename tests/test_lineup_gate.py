"""
Lineup Gatekeeper & Runtime Eligibility Test Suite — Phase 5
Verifies official starting XI validation (11 vs 11), competition allowlisting,
T-60m window gating, and refusal to generate predictions when lineups are unconfirmed.
"""
from datetime import datetime, timezone, timedelta
import pytest

from python.engine.competition_gate import CompetitionGatekeeper, ALLOWED_COMPETITIONS
from python.workers.lineup_gatekeeper import LineupGatekeeperWorker, LineupValidationError


class TestCompetitionGatekeeper:
    """Validate approved competition universe and category exclusions."""

    def test_tier1_competitions_approved(self):
        """Top 10 domestic leagues and major tournaments must be approved."""
        approved_ids = [39, 140, 78, 135, 61, 88, 94, 144, 128, 71, 2, 3, 1, 4]
        for cid in approved_ids:
            is_ok, reason = CompetitionGatekeeper.evaluate_eligibility(
                league_id=cid,
                home_team="Team A",
                away_team="Team B"
            )
            assert is_ok is True
            assert reason is None

    def test_unapproved_league_rejected(self):
        """Non-tier-1 leagues must be rejected."""
        is_ok, reason = CompetitionGatekeeper.evaluate_eligibility(
            league_id=9999,
            home_team="Team A",
            away_team="Team B"
        )
        assert is_ok is False
        assert "UNAPPROVED_COMPETITION" in reason

    def test_youth_and_women_teams_rejected(self):
        """Teams matching youth, women, or reserve patterns must be rejected."""
        test_cases = [
            (39, "Arsenal U21", "Chelsea U21"),
            (140, "Barcelona Femeni", "Real Madrid Femenino"),
            (78, "Bayern Munich II", "Dortmund II"),
            (61, "PSG Youth", "Lyon Youth"),
        ]
        for lid, h, a in test_cases:
            is_ok, reason = CompetitionGatekeeper.evaluate_eligibility(
                league_id=lid,
                home_team=h,
                away_team=a
            )
            assert is_ok is False
            assert "EXCLUDED_CATEGORY" in reason


class TestLineupPayloadValidation:
    """Validate 11 vs 11 team sheet verification and formation checks."""

    def test_valid_11_starters_accepted(self):
        """Lineups with exactly 11 starters per team must be confirmed."""
        mock_payload = [
            {
                "team": {"id": 1, "name": "Arsenal"},
                "formation": "4-3-3",
                "startXI": [{"player": {"id": i, "name": f"Home {i}"}} for i in range(11)],
                "substitutes": [{"player": {"id": 100, "name": "Sub 1"}}]
            },
            {
                "team": {"id": 2, "name": "Chelsea"},
                "formation": "4-2-3-1",
                "startXI": [{"player": {"id": i, "name": f"Away {i}"}} for i in range(11)],
                "substitutes": [{"player": {"id": 200, "name": "Sub 2"}}]
            }
        ]
        is_valid, reason, parsed = LineupGatekeeperWorker.validate_lineup_payload(mock_payload)
        assert is_valid is True
        assert reason == "LINEUPS_CONFIRMED"
        assert parsed["home"]["formation"] == "4-3-3"
        assert len(parsed["home"]["starters"]) == 11
        assert len(parsed["away"]["starters"]) == 11

    def test_incomplete_starters_rejected(self):
        """Team sheet with fewer than 11 starters must be rejected as incomplete."""
        mock_partial = [
            {
                "team": {"id": 1, "name": "Arsenal"},
                "formation": "4-3-3",
                "startXI": [{"player": {"id": i, "name": f"Home {i}"}} for i in range(9)],  # Only 9 starters
            },
            {
                "team": {"id": 2, "name": "Chelsea"},
                "formation": "4-2-3-1",
                "startXI": [{"player": {"id": i, "name": f"Away {i}"}} for i in range(11)],
            }
        ]
        is_valid, reason, _ = LineupGatekeeperWorker.validate_lineup_payload(mock_partial)
        assert is_valid is False
        assert "HOME_XI_INVALID" in reason

    def test_empty_lineup_rejected(self):
        """Empty list must be rejected."""
        is_valid, reason, _ = LineupGatekeeperWorker.validate_lineup_payload([])
        assert is_valid is False
        assert "LINEUPS_INCOMPLETE" in reason


class TestLineupWindowAndEconomy:
    """Validate that polling is strictly confined to T-60m and skips confirmed fixtures."""

    def test_window_filter_confines_to_60m(self):
        now = datetime.now(timezone.utc)
        worker = LineupGatekeeperWorker()

        fixtures = [
            # 1. Kickoff in 2 hours (T-120m): Too far, must be skipped
            {"id": 1, "kickoff_utc": now + timedelta(minutes=120), "lineup_confirmed": False},
            # 2. Kickoff in 45 minutes (T-45m): Inside window, must be polled
            {"id": 2, "kickoff_utc": now + timedelta(minutes=45), "lineup_confirmed": False},
            # 3. Kickoff in 10 minutes (T-10m): Inside window, must be polled
            {"id": 3, "kickoff_utc": now + timedelta(minutes=10), "lineup_confirmed": False},
            # 4. Kickoff in 30 minutes but ALREADY confirmed: Must be skipped
            {"id": 4, "kickoff_utc": now + timedelta(minutes=30), "lineup_confirmed": True},
            # 5. Kickoff already passed: Must be skipped
            {"id": 5, "kickoff_utc": now - timedelta(minutes=10), "lineup_confirmed": False},
        ]

        candidates = worker.check_eligible_matches_within_window(fixtures, max_minutes_ahead=60)
        candidate_ids = [c["id"] for c in candidates]

        # Only fixture 2 and 3 should be selected
        assert candidate_ids == [2, 3]
