"""Phase 2 quota governor tests.

These tests exercise the application client against a fake atomic RPC service.
They deliberately do not maintain a local usage counter because quota authority
must remain centralized in PostgreSQL.
"""
import concurrent.futures
import os
import threading

import pytest

from python.adapters.quota_manager import CentralQuotaManager, QuotaExceededError

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class FakeQuotaRPC:
    def __init__(self):
        self.lock = threading.Lock()
        self.user_used = 0
        self.worker_used = 0
        self.date_utc = "2026-09-26"

    def __call__(self, function_name, payload):
        with self.lock:
            assert function_name in {"reserve_api_quota", "get_api_quota_status"}

            if function_name == "get_api_quota_status":
                return {
                    "available": True,
                    "provider": payload["p_provider"],
                    "date_utc": self.date_utc,
                    "user_requests_made": self.user_used,
                    "worker_requests_made": self.worker_used,
                    "total_used": self.user_used + self.worker_used,
                    "daily_limit": 95,
                    "user_reserve": 50,
                    "worker_budget": 45,
                    "safety_buffer": 5,
                    "remaining_user": 50 - self.user_used,
                    "remaining_worker": 45 - self.worker_used,
                }

            cost = payload["p_cost"]
            is_user = payload["p_is_user"]
            total = self.user_used + self.worker_used

            if total + cost > 95:
                return {
                    "allowed": False,
                    "reason": "Hard safety stop",
                    "remaining_user": 50 - self.user_used,
                    "remaining_worker": 45 - self.worker_used,
                    "total_used": total,
                    "date_utc": self.date_utc,
                }

            if is_user and self.user_used + cost > 50:
                return {
                    "allowed": False,
                    "reason": "User analysis quota reached",
                    "remaining_user": 0,
                    "remaining_worker": 45 - self.worker_used,
                    "total_used": total,
                    "date_utc": self.date_utc,
                }

            if not is_user and self.worker_used + cost > 45:
                return {
                    "allowed": False,
                    "reason": "Automated worker budget exhausted",
                    "remaining_user": 50 - self.user_used,
                    "remaining_worker": 0,
                    "total_used": total,
                    "date_utc": self.date_utc,
                }

            if is_user:
                self.user_used += cost
            else:
                self.worker_used += cost

            return {
                "allowed": True,
                "remaining_user": 50 - self.user_used,
                "remaining_worker": 45 - self.worker_used,
                "total_used": self.user_used + self.worker_used,
                "date_utc": self.date_utc,
            }


def build_manager(fake=None):
    return CentralQuotaManager(
        supabase_url="https://quota.test",
        supabase_key="service-role-test",
        rpc_call=fake or FakeQuotaRPC(),
    )


def test_worker_budget_cap_at_45():
    fake = FakeQuotaRPC()
    manager = build_manager(fake)

    for _ in range(45):
        assert manager.reserve(is_user=False, cost=1)["allowed"] is True

    with pytest.raises(QuotaExceededError, match="worker budget exhausted"):
        manager.reserve(is_user=False, cost=1)

    status = manager.get_status()
    assert status["worker_used"] == 45
    assert status["remaining_worker"] == 0


def test_user_reserve_cap_at_50():
    fake = FakeQuotaRPC()
    manager = build_manager(fake)

    for _ in range(50):
        assert manager.reserve(is_user=True, cost=1)["allowed"] is True

    with pytest.raises(QuotaExceededError, match="user analysis quota reached"):
        manager.reserve(is_user=True, cost=1)

    status = manager.get_status()
    assert status["user_used"] == 50
    assert status["remaining_user"] == 0


def test_hard_stop_at_95():
    fake = FakeQuotaRPC()
    manager = build_manager(fake)

    for _ in range(45):
        manager.reserve(is_user=False, cost=1)
    for _ in range(50):
        manager.reserve(is_user=True, cost=1)

    assert manager.get_status()["total_used"] == 95

    with pytest.raises(QuotaExceededError):
        manager.reserve(is_user=True, cost=1)


def test_concurrent_reservations_are_atomic():
    fake = FakeQuotaRPC()
    manager = build_manager(fake)

    def make_call(_):
        try:
            manager.reserve(is_user=False, cost=1)
            return True
        except QuotaExceededError:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(make_call, range(20)))

    assert sum(results) == 20
    assert fake.worker_used == 20


def test_concurrent_worker_cap():
    fake = FakeQuotaRPC()
    manager = build_manager(fake)

    def make_call(_):
        try:
            manager.reserve(is_user=False, cost=1)
            return True
        except QuotaExceededError:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(make_call, range(50)))

    assert sum(results) == 45
    assert fake.worker_used == 45


def test_missing_governor_fails_closed():
    manager = CentralQuotaManager(supabase_url="", supabase_key="")

    with pytest.raises(QuotaExceededError, match="QUOTA_GOVERNOR_UNCONFIGURED"):
        manager.reserve(is_user=False, cost=1)


def test_invalid_cost_fails_closed():
    manager = build_manager()

    with pytest.raises(QuotaExceededError, match="INVALID_QUOTA_COST"):
        manager.reserve(is_user=False, cost=0)


def test_no_local_quota_file():
    fake = FakeQuotaRPC()
    manager = build_manager(fake)
    manager.reserve(is_user=False, cost=1)
    manager.reserve(is_user=True, cost=1)

    assert not os.path.exists(os.path.join(REPO_ROOT, ".cache", "api_quota.json"))
    assert not os.path.exists(os.path.join(REPO_ROOT, "request_budget.json"))


def test_migration_uses_dedicated_ledger_and_service_role_only():
    migration_file = os.path.join(
        REPO_ROOT, "supabase", "migrations", "006_quota_governance.sql"
    )
    with open(migration_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "CREATE TABLE IF NOT EXISTS public.api_quota_usage" in content
    assert "FOR UPDATE" in content
    assert "REVOKE ALL ON FUNCTION public.reserve_api_quota" in content
    assert "GRANT EXECUTE ON FUNCTION public.reserve_api_quota" in content
    assert "CREATE TABLE IF NOT EXISTS public.provider_usage" not in content
    assert "(NOW() AT TIME ZONE 'UTC')::DATE" in content
