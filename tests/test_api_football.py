import pytest
from python.adapters.api_football import APIFootballAdapter, QuotaExceededError, DataNotAvailableError
from python.data_pipeline.cache import DataCache
from python.data_pipeline.ingestion import DataIngestionPipeline

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = "Mocked Response"

    def json(self):
        return self.json_data

class MockSession:
    def __init__(self):
        self.responses = {}

    def get(self, url, headers=None, params=None):
        return MockResponse({"response": [{"id": 1}]}, 200)

def test_adapter_initialization():
    adapter = APIFootballAdapter(api_key="test")
    assert adapter.api_key == "test"

def test_cache_ttl_behavior():
    cache = DataCache()
    cache.set("key1", "val1", 300)
    assert cache.get("key1") == "val1"
    
def test_quota_exceeded_handling(monkeypatch):
    adapter = APIFootballAdapter(api_key="test")
    adapter.quota_remaining = 5
    with pytest.raises(QuotaExceededError):
        adapter.get_fixtures(39, 2023)

def test_lineup_confirmation():
    pipeline = DataIngestionPipeline()
    # Mocking
    pipeline.api.get_fixture_lineups = lambda x: [{"startXI": [{"player": {"id": 1, "name": "Player 1"}}]}]
    assert pipeline.check_lineup_confirmation(1) == True
    
    pipeline.api.get_fixture_lineups = lambda x: [{"startXI": []}]
    assert pipeline.check_lineup_confirmation(1) == False
    
    pipeline.api.get_fixture_lineups = lambda x: []
    assert pipeline.check_lineup_confirmation(1) == False
