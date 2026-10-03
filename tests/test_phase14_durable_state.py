"""
Automated Test Suite for Phase 14: Durable State Foundation
Validates lineup fingerprinting, deterministic hash invariance,
version increment on roster changes, and restart idempotency.
"""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import List
import pytest

from python.workers.lineup_watcher import LineupWatcherWorker
from python.workers.analysis_worker import AnalysisWorker


def test_lineup_fingerprint_deterministic():
    """Verify that order of player IDs does not change the SHA-256 fingerprint."""
    watcher = LineupWatcherWorker()
    starters_a = [10, 25, 3, 7, 99, 14, 5, 8, 1, 22, 17]
    starters_b = [17, 22, 1, 8, 5, 14, 99, 7, 3, 25, 10]  # Reversed order

    fp_a = watcher._compute_lineup_fingerprint(starters_a)
    fp_b = watcher._compute_lineup_fingerprint(starters_b)

    assert fp_a == fp_b
    assert len(fp_a) == 64  # Valid SHA-256 hex string


def test_lineup_fingerprint_change_detected():
    """Verify that substituting even one player changes the fingerprint."""
    watcher = LineupWatcherWorker()
    starters_original = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    starters_subbed = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12]  # Player 11 replaced by 12

    fp_orig = watcher._compute_lineup_fingerprint(starters_original)
    fp_sub = watcher._compute_lineup_fingerprint(starters_subbed)

    assert fp_orig != fp_sub


def test_lineup_resolve_new_vs_unchanged_vs_revision():
    """Verify stage and version resolution based on database snapshot record."""
    watcher = LineupWatcherWorker()
    fixture_id = 99999
    fp1 = "aaaa" * 16
    fp2 = "bbbb" * 16

    # 1. No existing snapshot in DB -> LINEUP_CONFIRMED, version 1
    watcher._get_latest_lineup_snapshot = lambda f_id: None  # type: ignore[assignment]
    stage1, ver1 = watcher._resolve_lineup_stage_and_version(fixture_id, fp1)
    assert stage1 == "LINEUP_CONFIRMED"
    assert ver1 == 1

    # 2. Existing snapshot in DB with identical fingerprint -> ALREADY_PERSISTED
    existing_snap = {
        "fixture_id": fixture_id,
        "snapshot_version": 1,
        "lineup_fingerprint": fp1,
        "stage": "LINEUP_CONFIRMED",
    }
    watcher._get_latest_lineup_snapshot = lambda f_id: existing_snap  # type: ignore[assignment]
    stage2, ver2 = watcher._resolve_lineup_stage_and_version(fixture_id, fp1)
    assert stage2 == "ALREADY_PERSISTED"
    assert ver2 == -1

    # 3. Existing snapshot with DIFFERENT fingerprint -> LINEUP_V2, version 2
    stage3, ver3 = watcher._resolve_lineup_stage_and_version(fixture_id, fp2)
    assert stage3 == "LINEUP_V2"
    assert ver3 == 2


def test_worker_restart_idempotency_from_db():
    """Simulate a worker restart where in-memory state is empty but DB has the snapshot."""
    # Worker 1 runs and finishes
    watcher1 = LineupWatcherWorker()
    fp = watcher1._compute_lineup_fingerprint([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])

    # Worker 2 starts fresh (clean memory)
    watcher2 = LineupWatcherWorker()
    assert len(watcher2._session_fingerprints) == 0

    # Mock DB returns the previously stored snapshot
    watcher2._get_latest_lineup_snapshot = lambda f_id: {  # type: ignore[assignment]
        "fixture_id": f_id,
        "snapshot_version": 1,
        "lineup_fingerprint": fp,
        "stage": "LINEUP_CONFIRMED",
    }

    # Should detect as ALREADY_PERSISTED without re-inserting or re-predicting
    stage, ver = watcher2._resolve_lineup_stage_and_version(777, fp)
    assert stage == "ALREADY_PERSISTED"
    assert ver == -1


def test_phase14_migration_files_exist_and_valid():
    """Verify that migrations 011, 012, 013 exist and have required table definitions."""
    from pathlib import Path
    migrations_dir = Path(__file__).parent.parent / "supabase" / "migrations"

    m11 = migrations_dir / "011_lineup_snapshots.sql"
    m12 = migrations_dir / "012_decision_opportunities.sql"
    m13 = migrations_dir / "013_learning_state.sql"

    assert m11.exists(), "011_lineup_snapshots.sql must exist"
    assert m12.exists(), "012_decision_opportunities.sql must exist"
    assert m13.exists(), "013_learning_state.sql must exist"

    text11 = m11.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS lineup_snapshots" in text11
    assert "lineup_fingerprint" in text11
    assert "snapshot_version" in text11
    assert "is_immutable" in text11

    text12 = m12.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS decision_opportunities" in text12
    assert "raw_probability" in text12
    assert "calibrated_probability" in text12
    assert "gate_decision" in text12

    text13 = m13.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS learning_state" in text13
    assert "state_json" in text13
    assert "learner_name" in text13
