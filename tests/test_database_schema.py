"""
Database Schema & RLS Hardening Test Suite — Phase 1
Verifies Supabase connectivity, anonymous read permissions on public tables,
and RLS negative authorization blocking unauthenticated writes on sensitive tables.
"""
import os
import glob
import json
import urllib.request
import urllib.error
import pytest

SUPABASE_URL = os.environ.get(
    "NEXT_PUBLIC_SUPABASE_URL",
    "https://qqcxjjkgvqknesrtnwal.supabase.co"
)
ANON_KEY = os.environ.get(
    "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
    "sb_publishable_MWK1XOnTtdc4MsagVnYHHw_qJUNnqsh"
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MIGRATIONS_DIR = os.path.join(REPO_ROOT, "supabase", "migrations")


def _supabase_request(endpoint: str, method: str = "GET", data: dict | None = None) -> tuple[int, dict | list]:
    """Execute an HTTP request to Supabase REST API using the public/anon key."""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as err:
        err_content = err.read().decode("utf-8")
        try:
            err_json = json.loads(err_content)
        except Exception:
            err_json = {"error": err_content}
        return err.code, err_json


class TestMigrationIntegrity:
    """Verify local SQL migration files integrity and sequence."""

    def test_migration_files_exist_in_order(self):
        """Ensure migrations 000 through 005 exist and are non-empty."""
        expected_migrations = [
            "000_baseline_reconciliation.sql",
            "001_initial_schema.sql",
            "002_seed_competitions.sql",
            "003_seed_market_definitions.sql",
            "004_historical_matches.sql",
            "005_rls_and_indexing_hardening.sql"
        ]

        for fname in expected_migrations:
            path = os.path.join(MIGRATIONS_DIR, fname)
            assert os.path.exists(path), f"Migration file missing: {fname}"
            assert os.path.getsize(path) > 50, f"Migration file empty or truncated: {fname}"

    def test_migrations_contain_idempotent_syntax(self):
        """Verify migrations use IF NOT EXISTS / DROP POLICY IF EXISTS for safety."""
        files = glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql"))
        assert len(files) >= 6

        # Check 000 has IF NOT EXISTS
        with open(os.path.join(MIGRATIONS_DIR, "000_baseline_reconciliation.sql"), "r", encoding="utf-8") as f:
            content_000 = f.read()
            assert "CREATE TABLE IF NOT EXISTS public.schema_migrations" in content_000

        # Check 005 has DROP POLICY IF EXISTS
        with open(os.path.join(MIGRATIONS_DIR, "005_rls_and_indexing_hardening.sql"), "r", encoding="utf-8") as f:
            content_005 = f.read()
            assert "DROP POLICY IF EXISTS" in content_005
            assert "idx_matches_competition_id" in content_005


class TestDatabaseSchemaAndAccess:
    """Live Supabase API access and Row Level Security validation."""

    def test_anon_can_read_historical_matches(self):
        """Verify anonymous clients can read historical training matches."""
        status, data = _supabase_request(
            "historical_matches?select=id,league_code,match_date,home_team,away_team,fthg,ftag&limit=5"
        )
        assert status == 200
        assert isinstance(data, list)
        assert len(data) == 5, f"Expected 5 historical matches, got {len(data)}"
        assert "home_team" in data[0]

    def test_anon_can_read_competitions(self):
        """Verify anonymous clients can read registered competitions."""
        status, data = _supabase_request("competitions?select=id,name,league_id&limit=5")
        assert status == 200
        assert isinstance(data, list)

    def test_anon_cannot_insert_model_predictions(self):
        """Negative test: Anonymous client write to model_predictions must fail."""
        status, data = _supabase_request(
            "model_predictions",
            method="POST",
            data={
                "match_id": 999999,
                "market": "1X2",
                "predicted_prob": 0.99,
                "is_candidate": False
            }
        )
        # Must be rejected by RLS or lack of permissions (401, 403, 404, or 400 with RLS message)
        assert status in [400, 401, 403, 404], (
            f"SECURITY FAILURE: Anon was unexpectedly allowed to write to model_predictions! "
            f"Status: {status}, Response: {data}"
        )

    def test_anon_cannot_insert_paper_bets(self):
        """Negative test: Anonymous client write to paper_bets must fail."""
        status, data = _supabase_request(
            "paper_bets",
            method="POST",
            data={
                "match_id": 999999,
                "prediction_id": 1,
                "market": "1X2",
                "stake": 1000.0,
                "status": "PLACED"
            }
        )
        assert status in [400, 401, 403, 404], (
            f"SECURITY FAILURE: Anon was unexpectedly allowed to write to paper_bets! "
            f"Status: {status}, Response: {data}"
        )

    def test_anon_cannot_insert_learning_runs(self):
        """Negative test: Anonymous client write to learning_runs must fail."""
        status, data = _supabase_request(
            "learning_runs",
            method="POST",
            data={
                "model_name": "malicious_injection",
                "status": "COMPLETED"
            }
        )
        assert status in [400, 401, 403, 404], (
            f"SECURITY FAILURE: Anon was unexpectedly allowed to write to learning_runs! "
            f"Status: {status}, Response: {data}"
        )
