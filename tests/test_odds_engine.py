"""
Target Odds Engine & Anti-Fabrication Test Suite — Phase 4
Verifies exact margin calculation, proportional & Shin devigging,
anti-fabrication failure modes, and CanonicalOddsMarket persistence serialization.
"""
import math
from datetime import datetime, timezone
import pytest

from python.odds.devig import DeVIgEngine
from python.odds.snapshot_writer import OddsSnapshotWriter
from python.adapters.one_xbet_adapter import OneXBetAdapter, OddsUnavailableException
from python.data_contracts import CanonicalOddsMarket, CanonicalOddsSelection


class TestDevigEngine:
    """Mathematical verification of margin calculations and probability normalization."""

    def test_margin_calculation_1x2(self):
        """Standard 1X2 prices [1.95, 3.40, 4.20] should produce ~4.5% margin."""
        odds = [1.95, 3.40, 4.20]
        margin = DeVIgEngine.calculate_margin(odds)
        # 1/1.95 + 1/3.40 + 1/4.20 = 0.5128 + 0.2941 + 0.2381 = 1.0450 -> 4.5%
        assert round(margin, 3) == 0.045

    def test_multiplicative_devig_sum_to_one(self):
        """Proportional devigging must sum to 1.0 within float precision."""
        odds = [1.50, 4.80, 6.50]
        fair_probs = DeVIgEngine.multiplicative_devig(odds)
        assert len(fair_probs) == 3
        assert math.isclose(sum(fair_probs), 1.0, abs_tol=1e-6)
        # Strong favorite must have highest probability
        assert fair_probs[0] > fair_probs[1] > fair_probs[2]

    def test_shin_devig_sum_to_one(self):
        """Shin devigging must sum to 1.0 and estimate non-negative insider parameter z."""
        odds = [1.95, 3.40, 4.20]
        fair_probs, z = DeVIgEngine.shin_devig(odds)
        assert len(fair_probs) == 3
        assert math.isclose(sum(fair_probs), 1.0, abs_tol=1e-6)
        assert z >= 0.0

    def test_invalid_odds_raise_value_error(self):
        """Prices <= 1.0 are invalid and must raise ValueError."""
        with pytest.raises(ValueError):
            DeVIgEngine.calculate_margin([0.95, 3.40, 4.20])
        with pytest.raises(ValueError):
            DeVIgEngine.multiplicative_devig([1.0, 2.0])


class TestOneXBetAntiFabrication:
    """Enforce strict refusal to invent synthetic odds when target bookmaker is unreachable."""

    def test_empty_prices_raise_odds_unavailable(self):
        """Empty 1xBet line must raise OddsUnavailableException."""
        adapter = OneXBetAdapter()
        with pytest.raises(OddsUnavailableException):
            adapter.parse_market("match_123", "MATCH_1X2", {})

    def test_parse_market_creates_canonical_odds(self):
        """Valid 1xBet prices must be parsed into frozen CanonicalOddsMarket with devigged prices."""
        adapter = OneXBetAdapter()
        raw_prices = {"Home": 2.10, "Draw": 3.30, "Away": 3.60}
        market = adapter.parse_market("api_football_9999", "MATCH_1X2", raw_prices)

        assert isinstance(market, CanonicalOddsMarket)
        assert market.bookmaker == "1xbet"
        assert market.canonical_market == "MATCH_1X2"
        assert len(market.selections) == 3
        assert math.isclose(sum(s.devigged_prob for s in market.selections), 1.0, abs_tol=1e-4)

    def test_offline_reachability_raises_odds_unavailable(self, monkeypatch):
        """If 1xBet endpoint is unreachable, get_match_odds must raise OddsUnavailableException."""
        adapter = OneXBetAdapter()
        # Mock reachability to simulate offline or geo-blocked environment
        monkeypatch.setattr(
            adapter,
            "check_network_reachability",
            lambda: {"reachable": False, "status_code": None, "detail": "Simulated offline"}
        )

        with pytest.raises(OddsUnavailableException) as exc:
            adapter.get_match_odds("m1", "Arsenal", "Chelsea", datetime.now(timezone.utc))
        assert "ODDS_UNAVAILABLE" in str(exc.value) or "unavailable" in str(exc.value).lower()


class TestOddsSnapshotWriter:
    """Verify serialization and 60-second deduplication in snapshot logging."""

    def test_snapshot_serialization_and_deduplication(self):
        writer = OddsSnapshotWriter(supabase_url="", supabase_key="")
        now = datetime.now(timezone.utc)

        selections = [
            CanonicalOddsSelection(selection="Home", line=None, decimal_odds=2.00, implied_prob=0.50, devigged_prob=0.48),
            CanonicalOddsSelection(selection="Draw", line=None, decimal_odds=3.20, implied_prob=0.3125, devigged_prob=0.30),
            CanonicalOddsSelection(selection="Away", line=None, decimal_odds=4.00, implied_prob=0.25, devigged_prob=0.22),
        ]
        market = CanonicalOddsMarket(
            match_id="api_football_12345",
            bookmaker="1xbet",
            canonical_market="MATCH_1X2",
            period="FULL_TIME",
            is_live=False,
            selections=selections,
            market_margin=0.0625,
            source_timestamp=now,
            available_at=now,
        )

        # First serialization: 3 rows generated
        rows1 = writer.serialize_market(market)
        assert len(rows1) == 3
        assert rows1[0]["provider"] == "1xbet"
        assert rows1[0]["match_id"] == 12345
        assert rows1[0]["decimal_odds"] == 2.00

        # Second serialization with identical prices within 60s: deduplicated to 0 rows
        rows2 = writer.serialize_market(market)
        assert len(rows2) == 0
