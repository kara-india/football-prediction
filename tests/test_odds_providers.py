import pytest
import datetime
from python.providers.market_normalizer import (
    normalize_market_name, de_vig, implied_probability, 
    calculate_margin, validate_market
)
from python.providers.stale_odds_detector import StaleOddsDetector
from python.providers.provider_registry import ProviderRegistry
from python.providers.base import OddsProvider, ProviderHealth, OddsEvent, OddsMarket

@pytest.mark.asyncio
async def test_market_normalization():
    assert normalize_market_name('Match Winner') == '1x2'
    assert normalize_market_name('Unknown') is None

def test_de_vigging_calculation():
    odds = [2.0, 3.0, 4.0]  # 50%, 33.3%, 25% -> sum = 1.0833
    de_vigged = de_vig(odds)
    assert abs(sum(de_vigged) - 1.0) < 1e-6
    assert abs(de_vigged[0] - (0.5 / 1.083333333)) < 1e-5

def test_implied_probability():
    assert implied_probability(2.0) == 0.5
    assert implied_probability(4.0) == 0.25

def test_stale_odds_detection():
    detector = StaleOddsDetector()
    now = datetime.datetime.now(datetime.timezone.utc)
    
    assert not detector.is_stale(now - datetime.timedelta(seconds=100), True)
    assert detector.is_stale(now - datetime.timedelta(seconds=150), True)
    
    assert not detector.is_stale(now - datetime.timedelta(seconds=1500), False)
    assert detector.is_stale(now - datetime.timedelta(seconds=2000), False)

def test_market_validation():
    assert validate_market('1x2', '1') is True
    assert validate_market('1x2', 'X') is True
    assert validate_market('1x2', 'Invalid') is False
    assert validate_market('invalid_market', '1') is False

@pytest.mark.asyncio
async def test_provider_registry_returns_none_when_no_1xbet_provider():
    class MockProvider(OddsProvider):
        async def health_check(self):
            return ProviderHealth(
                provider="mock", authenticated=True, reachable=True,
                live_odds_supported=False, prematch_supported=False,
                request_limit=None, requests_remaining=None,
                last_success=None, last_error=None, supported_markets=[],
                is_1xbet_confirmed=False
            )
        async def discover_events(self, league_ids): return []
        async def get_live_events(self): return []
        async def get_prematch_events(self, league_id): return []
        async def get_markets(self, event_id): return []
        async def get_event_markets(self, event_id, market_types): return []

    registry = ProviderRegistry()
    registry.register(MockProvider(), 1)
    
    provider = await registry.get_1xbet_provider()
    assert provider is None

@pytest.mark.asyncio
async def test_provider_registry_returns_1xbet_provider():
    class MockProvider(OddsProvider):
        async def health_check(self):
            return ProviderHealth(
                provider="mock", authenticated=True, reachable=True,
                live_odds_supported=False, prematch_supported=False,
                request_limit=None, requests_remaining=None,
                last_success=None, last_error=None, supported_markets=[],
                is_1xbet_confirmed=True
            )
        async def discover_events(self, league_ids): return []
        async def get_live_events(self): return []
        async def get_prematch_events(self, league_id): return []
        async def get_markets(self, event_id): return []
        async def get_event_markets(self, event_id, market_types): return []

    registry = ProviderRegistry()
    registry.register(MockProvider(), 1)
    
    provider = await registry.get_1xbet_provider()
    assert provider is not None
