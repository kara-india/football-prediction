"""
Quota Governance & Cost Safety Test Suite — Phase 2
Verifies atomic quota reservation, strict enforcement of the ₹0.00 cost mandate,
50 user reserve, 45 worker budget, 5 safety buffer, and zero filesystem leaks.
"""
import os
import concurrent.futures
from datetime import datetime, timezone
import pytest

from python.adapters.quota_manager import CentralQuotaManager, QuotaExceededError

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestQuotaGovernor:
    """Validate strict daily limits and cost containment."""

    def test_worker_budget_cap_at_45(self):
        """Sequential worker requests must strictly stop at 45. 46th must raise QuotaExceededError."""
        # Use an isolated in-memory manager instance without remote DB to test boundary logic
        manager = CentralQuotaManager(supabase_url="", supabase_key="")

        # Successfully reserve 45 worker credits
        for i in range(45):
            res = manager.reserve(is_user=False, cost=1)
            assert res["allowed"] is True

        status = manager.get_status()
        assert status["worker_used"] == 45
        assert status["remaining_worker"] == 0
        assert status["remaining_user"] == 50

        # 46th automated worker request must fail
        with pytest.raises(QuotaExceededError) as exc_info:
            manager.reserve(is_user=False, cost=1)
        assert "worker budget exhausted" in str(exc_info.value).lower()

    def test_user_reserve_cap_at_50(self):
        """Sequential user requests must strictly stop at 50. 51st must raise QuotaExceededError."""
        manager = CentralQuotaManager(supabase_url="", supabase_key="")

        # Successfully reserve 50 user credits
        for i in range(50):
            res = manager.reserve(is_user=True, cost=1)
            assert res["allowed"] is True

        status = manager.get_status()
        assert status["user_used"] == 50
        assert status["remaining_user"] == 0

        # 51st user request must fail
        with pytest.raises(QuotaExceededError) as exc_info:
            manager.reserve(is_user=True, cost=1)
        assert "user analysis quota reached" in str(exc_info.value).lower()

    def test_hard_stop_total_at_95(self):
        """Combined usage must never exceed 95 (preserving 5 requests emergency buffer)."""
        manager = CentralQuotaManager(supabase_url="", supabase_key="")

        # Fill 45 worker + 50 user = 95 total
        for _ in range(45):
            manager.reserve(is_user=False, cost=1)
        for _ in range(50):
            manager.reserve(is_user=True, cost=1)

        status = manager.get_status()
        assert status["total_used"] == 95
        assert status["safety_buffer"] == 5

        # Any further request must fail
        with pytest.raises(QuotaExceededError):
            manager.reserve(is_user=True, cost=1)
        with pytest.raises(QuotaExceededError):
            manager.reserve(is_user=False, cost=1)

    def test_concurrent_reservation_safety(self):
        """Simultaneous concurrent requests must not exceed budget."""
        manager = CentralQuotaManager(supabase_url="", supabase_key="")

        # Concurrently fire 40 worker reservations from 10 threads
        def make_call():
            try:
                manager.reserve(is_user=False, cost=1)
                return True
            except QuotaExceededError:
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_call) for _ in range(50)]
            results = [f.result() for f in futures]

        status = manager.get_status()
        # Exactly 45 should succeed and 5 should fail
        successful = sum(1 for r in results if r is True)
        assert successful == 45, f"Expected exactly 45 successful worker reservations, got {successful}"
        assert status["worker_used"] == 45

    def test_no_filesystem_quota_leaks(self):
        """Ensure no local .cache/api_quota.json or local budget file is created."""
        cache_file = os.path.join(REPO_ROOT, ".cache", "api_quota.json")
        manager = CentralQuotaManager(supabase_url="", supabase_key="")
        manager.reserve(is_user=False, cost=1)
        manager.reserve(is_user=True, cost=1)

        assert not os.path.exists(cache_file), (
            f"VIOLATION: Quota operation created local filesystem file at {cache_file}!"
        )

    def test_migration_006_sql_syntax(self):
        """Verify 006_quota_governance.sql contains atomic function and correct grants."""
        migration_file = os.path.join(REPO_ROOT, "supabase", "migrations", "006_quota_governance.sql")
        assert os.path.exists(migration_file)

        with open(migration_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "CREATE OR REPLACE FUNCTION public.reserve_api_quota" in content
        assert "daily_limit" in content
        assert "user_reserve" in content
        assert "worker_budget" in content
        assert "FOR UPDATE" in content
        assert "get_api_quota_status" in content
