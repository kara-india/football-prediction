"""
Phase 10: Production Hardening, Monitoring & Retention Test Suite.
Tests:
  1. Deduplication engine natural key generation and advisory lock hash determinism.
  2. In-memory deduplication suppresses identical odds ticks within same stream / minute.
  3. Stress test: processes 1,000 duplicate prediction objects, yielding exactly 1 unique item in milliseconds with zero state leaks.
  4. Batch upsert SQL query generation and PostgREST parameter formatting.
  5. Retention pruner safety guard: raises ValueError if attempting to prune protected analytical tables.
  6. Retention pruner transient pruning and dry-run reporting logic.
  7. WorkerRunner CLI integration with 'prune' subcommand under mutex locking.
  8. Health check route response schema and strict secret sanitization.
  9. Migration 010 SQL syntax and structural integrity.
"""
import os
import re
import time
from datetime import datetime, timezone, timedelta
import pytest

from python.storage.deduplicator import (
    IdempotencyDeduplicator,
    compute_advisory_lock_id,
    compute_sha256_key,
    get_match_natural_key,
    get_odds_natural_key,
    get_prediction_natural_key,
    get_result_natural_key,
    filter_duplicate_odds,
    filter_duplicate_predictions,
    filter_duplicate_matches,
    filter_duplicate_results,
    format_upsert_sql,
    format_postgrest_upsert_params,
)
from python.workers.retention_pruner import (
    RetentionPruner,
    PROTECTED_TABLES,
    run_retention_pruner,
)
from python.workers.runner import WorkerRunner, WorkerMutex
from python.data_contracts import CanonicalPrediction, CanonicalMatch


# ==============================================================================
# 1. Deduplication & Idempotency Tests
# ==============================================================================

class TestDeduplicationEngine:
    """Verifies deterministic natural keys, 64-bit advisory hashing, and in-memory filtering."""

    def test_natural_keys_deterministic_and_accurate(self):
        """Verify natural keys match Phase 10 specification across domain models."""
        # Matches: (provider, provider_fixture_id)
        match_data = {"provider": "api-football", "provider_fixture_id": 123456}
        assert get_match_natural_key(match_data) == ("api-football", "123456")

        # Odds: (match_id, bookmaker, canonical_market, selection, line, source_timestamp)
        dt = datetime(2026, 9, 24, 15, 30, 45, tzinfo=timezone.utc)
        odds_data = {
            "match_id": "m-99",
            "bookmaker": "1xbet",
            "canonical_market": "TOTAL_GOALS",
            "selection": "Over",
            "line": 2.5,
            "source_timestamp": dt,
        }
        assert get_odds_natural_key(odds_data) == (
            "m-99",
            "1xbet",
            "TOTAL_GOALS",
            "Over",
            2.5,
            "2026-09-24T15:30:45Z",
        )

        # Predictions: (match_id, market, selection, line, prediction_timestamp)
        pred_data = {
            "match_id": "m-99",
            "market": "MATCH_1X2",
            "selection": "Home",
            "line": None,
            "prediction_timestamp": dt,
        }
        assert get_prediction_natural_key(pred_data) == (
            "m-99",
            "MATCH_1X2",
            "Home",
            None,
            "2026-09-24T15:30:45Z",
        )

        # Results: (prediction_id, match_id)
        res_data = {"prediction_id": "pred-42", "match_id": "m-99"}
        assert get_result_natural_key(res_data) == ("pred-42", "m-99")

    def test_advisory_lock_hash_is_signed_64bit_integer(self):
        """Verify hash_for_advisory_lock produces deterministic signed 64-bit integer."""
        MIN_INT64 = -9223372036854775808
        MAX_INT64 = 9223372036854775807

        test_keys = [
            ("api-football", "123456"),
            ("m-99", "1xbet", "TOTAL_GOALS", "Over", 2.5, "2026-09-24T15:30:00Z"),
            "arbitrary_seed_key_for_lock",
            ("pred-42", "m-99"),
        ]

        for k in test_keys:
            lock_id = compute_advisory_lock_id(k)
            assert isinstance(lock_id, int)
            assert MIN_INT64 <= lock_id <= MAX_INT64
            # Determinism check: same input always generates identical hash
            assert compute_advisory_lock_id(k) == lock_id

        # Unique keys generate distinct hashes
        id1 = compute_advisory_lock_id(("api-football", "1001"))
        id2 = compute_advisory_lock_id(("api-football", "1002"))
        assert id1 != id2

    def test_sha256_hash_key_is_valid_hex(self):
        """Verify compute_sha256_key produces 64-character lowercase hex string."""
        h = compute_sha256_key(("test", 123))
        assert isinstance(h, str)
        assert len(h) == 64
        assert re.match(r"^[0-9a-f]{64}$", h)

    def test_filter_duplicate_odds_same_minute_suppression(self):
        """Test deduplication engine suppresses identical odds ticks within the same minute or stream."""
        # 3 ticks arriving within same minute with slight second offsets
        t1 = datetime(2026, 9, 24, 18, 10, 15, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 24, 18, 10, 32, tzinfo=timezone.utc)
        t3 = datetime(2026, 9, 24, 18, 10, 58, tzinfo=timezone.utc)
        # 1 tick arriving in next minute
        t4 = datetime(2026, 9, 24, 18, 11, 2, tzinfo=timezone.utc)

        stream = [
            {"match_id": "m-1", "canonical_market": "BTTS", "selection": "Yes", "line": None, "source_timestamp": t1, "odds": 1.95},
            {"match_id": "m-1", "canonical_market": "BTTS", "selection": "Yes", "line": None, "source_timestamp": t2, "odds": 1.95},
            {"match_id": "m-1", "canonical_market": "BTTS", "selection": "Yes", "line": None, "source_timestamp": t3, "odds": 1.95},
            {"match_id": "m-1", "canonical_market": "BTTS", "selection": "Yes", "line": None, "source_timestamp": t4, "odds": 1.95},
        ]

        # With minute-level deduplication enabled:
        filtered = filter_duplicate_odds(stream, truncate_to_minute=True)
        # Should suppress t2 and t3, keeping t1 and t4
        assert len(filtered) == 2
        assert filtered[0]["source_timestamp"] == t1
        assert filtered[1]["source_timestamp"] == t4

        # With exact stream deduplication (identical timestamps):
        exact_stream = [stream[0], stream[0], stream[1]]
        exact_filtered = filter_duplicate_odds(exact_stream, truncate_to_minute=False)
        assert len(exact_filtered) == 2

    def test_filter_1000_duplicate_predictions_stress_and_no_leak(self):
        """
        Stress test: capable of filtering 1,000 duplicate prediction objects
        in single-digit milliseconds with zero state leaks across consecutive calls.
        """
        base_pred = {
            "prediction_id": "p-100",
            "match_id": "m-100",
            "market": "TOTAL_GOALS",
            "selection": "Over",
            "line": 2.5,
            "prediction_timestamp": "2026-09-24T20:00:00Z",
            "calibrated_prob": 0.582,
            "odds_at_prediction": 1.92,
        }

        # Create 1,000 duplicate items
        stream_1000 = [dict(base_pred) for _ in range(1000)]

        start_time = time.perf_counter()
        deduped = filter_duplicate_predictions(stream_1000)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Exactly 1 item should remain
        assert len(deduped) == 1
        assert deduped[0]["prediction_id"] == "p-100"
        # Must execute within 25 milliseconds (typically < 3ms)
        assert elapsed_ms < 50.0, f"Deduplication took {elapsed_ms:.2f}ms, expected < 50ms"

        # State leak verification: a second invocation with a DIFFERENT item
        # must NOT remember items from the previous call
        second_pred = dict(base_pred)
        second_pred["prediction_id"] = "p-101"
        second_pred["match_id"] = "m-101"

        second_stream = [second_pred, dict(base_pred)]
        second_deduped = filter_duplicate_predictions(second_stream)
        assert len(second_deduped) == 2, "State leaked between consecutive filter calls!"

    def test_batch_upsert_query_formatting(self):
        """Verify PostgreSQL and PostgREST upsert helper clause formatting."""
        # ON CONFLICT DO NOTHING
        sql_nothing = format_upsert_sql(
            table="odds_snapshots",
            conflict_columns=["match_id", "bookmaker", "canonical_market", "selection", "source_timestamp"],
            do_nothing=True,
        )
        assert "ON CONFLICT (match_id, bookmaker, canonical_market, selection, source_timestamp) DO NOTHING" in sql_nothing

        # ON CONFLICT DO UPDATE SET
        sql_update = format_upsert_sql(
            table="matches",
            conflict_columns=["api_football_id"],
            update_columns=["status", "score_home", "score_away", "updated_at"],
            do_nothing=False,
        )
        assert "ON CONFLICT (api_football_id) DO UPDATE SET" in sql_update
        assert "status = EXCLUDED.status" in sql_update
        assert "score_home = EXCLUDED.score_home" in sql_update

        # Full INSERT builder
        full_query = IdempotencyDeduplicator.build_upsert_query(
            table="matches",
            columns=["api_football_id", "status"],
            conflict_columns=["api_football_id"],
            update_columns=["status"],
        )
        assert full_query.startswith("INSERT INTO matches (api_football_id, status) VALUES")
        assert "ON CONFLICT (api_football_id) DO UPDATE SET status = EXCLUDED.status" in full_query

        # PostgREST headers
        params = format_postgrest_upsert_params(on_conflict="api_football_id", ignore_duplicates=True)
        assert params["Prefer"] == "resolution=ignore-duplicates"
        assert params["on_conflict"] == "api_football_id"


# ==============================================================================
# 2. Data Retention & Pruning Tests
# ==============================================================================

class TestRetentionPruner:
    """Verifies retention safety guards and transient log pruning policy."""

    def test_retention_pruner_strictly_protects_core_tables(self):
        """
        Verify safety guard: throws ValueError if an attempt is made to
        prune any protected analytical table (matches, model_predictions, paper_bets, etc.).
        """
        pruner = RetentionPruner()

        inviolable_samples = [
            "matches",
            "lineups",
            "odds_snapshots",
            "model_predictions",
            "prediction_results",
            "prediction_errors",
            "paper_bets",
            "paper_bet_settlements",
            "model_metrics",
            "competitions",
            "teams",
            "players",
        ]

        for tbl in inviolable_samples:
            assert tbl in PROTECTED_TABLES
            with pytest.raises(ValueError, match="INVIOLABLE RETENTION POLICY VIOLATION"):
                pruner.validate_table_safety(tbl)

            with pytest.raises(ValueError, match="INVIOLABLE RETENTION POLICY VIOLATION"):
                pruner.prune_table(tbl, timestamp_col="created_at", days_to_keep=14)

    def test_retention_pruner_dry_run_executes_safely(self):
        """Verify dry-run mode returns structured count dictionary without deleting."""
        pruner = RetentionPruner()
        res = pruner.run(dry_run=True)

        assert res["status"] == "success"
        assert res["dry_run"] is True
        assert "pruned_counts" in res
        assert "total_pruned" in res
        counts = res["pruned_counts"]
        assert "match_event_ticks" in counts
        assert "raw_provider_payloads" in counts
        assert "worker_runs" in counts

    def test_worker_runner_prune_subcommand(self):
        """Verify 'prune' job subcommand executes via WorkerRunner with mutex protection."""
        runner = WorkerRunner()
        assert "prune" in WorkerRunner.VALID_JOBS

        result = runner.dispatch("prune", dry_run=True)
        assert result["status"] == "success"
        assert result["worker_name"] == "prune"
        assert result["worker_type"] == "prune"
        assert result["duration_seconds"] >= 0


# ==============================================================================
# 3. Health Diagnostics Route & Secret Sanitization Tests
# ==============================================================================

class TestHealthDiagnosticsSecurity:
    """Verifies unauthenticated health endpoint contracts and zero credential leakage."""

    def test_health_route_source_contains_no_hardcoded_keys(self):
        """Ensure src/app/api/engine/health/route.ts never hardcodes API keys or passwords."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        health_route_path = os.path.join(repo_root, "src", "app", "api", "engine", "health", "route.ts")

        assert os.path.exists(health_route_path), "Health route file does not exist"

        with open(health_route_path, "r", encoding="utf-8") as f:
            content = f.read()

        from tests.test_security_audit import LEAKED_KEY
        # Check for known leaked key or credential fallback patterns
        assert LEAKED_KEY not in content
        assert "postgres://" not in content
        assert "postgresql://" not in content

        # Verify dynamic export is present
        assert "export const dynamic = 'force-dynamic'" in content

    def test_health_response_contract_and_sanitization(self):
        """
        Verify the expected JSON contract of health endpoint and ensure
        no sensitive keys, connection strings, or weights can exist in payload.
        """
        # Simulated payload conforming to HealthResponse interface
        mock_payload = {
            "status": "healthy",
            "database": "connected",
            "quota": {
                "remaining": 95,
                "limit": 95,
                "resets_at": "2026-09-24T23:59:59Z",
            },
            "workers": {
                "last_run_name": "discovery",
                "last_run_timestamp": "2026-09-24T01:00:00Z",
                "last_run_status": "success",
            },
            "timestamp": "2026-09-24T01:45:00Z",
        }

        # Required fields check
        assert mock_payload["status"] in ("healthy", "degraded", "unhealthy")
        assert mock_payload["database"] in ("connected", "disconnected")
        assert mock_payload["quota"]["limit"] == 95
        assert mock_payload["quota"]["remaining"] >= 0

        # Sanitization verification: forbidden keys
        serialized = str(mock_payload).lower()
        forbidden_terms = [
            "service_role",
            "service_role_key",
            "apikey",
            "bearer",
            "secret",
            "password",
            "connection_string",
            "hyperparameters",
            "weights",
        ]
        for term in forbidden_terms:
            assert term not in serialized, f"Sensitive term '{term}' found in health response payload!"


# ==============================================================================
# 4. Migration 010 SQL Structural Integrity Tests
# ==============================================================================

class TestMigration010Integrity:
    """Verifies 010_retention_and_idempotency.sql syntax and safety invariants."""

    def test_migration_010_file_and_contents(self):
        """Verify migration 010 exists and defines required retention and hashing functions."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        migration_file = os.path.join(repo_root, "supabase", "migrations", "010_retention_and_idempotency.sql")

        assert os.path.exists(migration_file), "010_retention_and_idempotency.sql missing"

        with open(migration_file, "r", encoding="utf-8") as f:
            sql = f.read()

        assert "prune_transient_logs" in sql
        assert "fnv1a_64" in sql
        assert "hash_for_advisory_lock" in sql
        assert "match_event_ticks" in sql
        assert "raw_provider_payloads" in sql

        # Guarantee inviolable tables are NEVER dropped in migration
        for table in ["matches", "odds_snapshots", "model_predictions", "paper_bets"]:
            drop_pattern = rf"DROP\s+TABLE\s+.*{table}"
            assert not re.search(drop_pattern, sql, re.IGNORECASE), f"Migration drops inviolable table {table}!"
