"""Recovery A0: API-Football must not be reachable from runtime code."""

from pathlib import Path

from python.adapters.api_football import APIFootballAdapter, APIFootballDisabled
from python.providers.runtime_registry import (
    RETIRED_PROVIDERS,
    ProviderNotAllowed,
    assert_provider_allowed,
    runtime_provider_names,
)

ROOT = Path(__file__).resolve().parents[1]
NEEDLE = "api-sports" + ".io"
SKIP_DIRS = {".git", "node_modules", ".next", "__pycache__"}


def test_host_string_absent_outside_this_file():
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.suffix not in {".py", ".ts", ".tsx", ".js", ".yml", ".yaml", ".md", ".env"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if NEEDLE in text:
            hits.append(str(path.relative_to(ROOT)))
    assert hits == []


def test_keyed_adapter_does_not_call_network(monkeypatch):
    adapter = APIFootballAdapter(api_key="present-but-unused")
    adapter.quota_remaining = 50

    def explode(*_args, **_kwargs):
        raise AssertionError("session.get must not be called")

    monkeypatch.setattr(adapter.session, "get", explode)
    try:
        adapter._make_request("fixtures")
    except APIFootballDisabled:
        return
    raise AssertionError("expected APIFootballDisabled")


def test_runtime_registry_rejects_api_football():
    assert "api_football" not in runtime_provider_names()
    assert "api-football" in RETIRED_PROVIDERS
    try:
        assert_provider_allowed("api-football")
    except ProviderNotAllowed:
        return
    raise AssertionError("api-football must be rejected")
