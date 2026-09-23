"""
Central Quota Manager for Python Pipeline & Background Workers
Enforces the ₹0.00 external data cost mandate via Supabase stored procedure
`reserve_api_quota()` and an in-memory process failsafe.
Hard limits: 95 total / day (50 user on-demand reserve, 45 worker budget, 5 safety buffer).
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

logger = logging.getLogger("QuotaManager")


class QuotaExceededError(Exception):
    """Raised when an API call would exceed daily cost quotas."""
    pass


class CentralQuotaManager:
    """Manages API request allocation between user on-demand and automated workers."""

    HARD_STOP_LIMIT = 95
    USER_RESERVE = 50
    WORKER_BUDGET = 45
    SAFETY_BUFFER = 5

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        provider: str = "api-football"
    ):
        self.provider = provider
        self.supabase_url = supabase_url or os.environ.get(
            "NEXT_PUBLIC_SUPABASE_URL",
            "https://qqcxjjkgvqknesrtnwal.supabase.co"
        )
        self.supabase_key = supabase_key or os.environ.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
        )

        # In-memory failsafe state (per UTC day)
        self._memory_date = self._get_today_utc()
        self._memory_worker_used = 0
        self._memory_user_used = 0

    @staticmethod
    def _get_today_utc() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _check_memory_rollover(self):
        today = self._get_today_utc()
        if self._memory_date != today:
            self._memory_date = today
            self._memory_worker_used = 0
            self._memory_user_used = 0

    def reserve(self, is_user: bool = False, cost: int = 1) -> Dict[str, Any]:
        """Atomically reserve API quota before making an external provider request.

        Args:
            is_user: True if request was triggered on-demand by an interactive user.
                     False if request is from an automated background worker.
            cost: Number of API credits (default 1).

        Returns:
            Dict containing {'allowed': bool, 'remaining_user': int, 'remaining_worker': int, ...}

        Raises:
            QuotaExceededError: If the reservation violates cost constraints.
        """
        self._check_memory_rollover()

        # Attempt atomic reservation via Supabase stored procedure
        if self.supabase_url and self.supabase_key:
            try:
                rpc_url = f"{self.supabase_url}/rest/v1/rpc/reserve_api_quota"
                payload = json.dumps({
                    "p_provider": self.provider,
                    "p_cost": cost,
                    "p_is_user": is_user
                }).encode("utf-8")

                req = urllib.request.Request(
                    rpc_url,
                    data=payload,
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )

                with urllib.request.urlopen(req, timeout=5) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    if isinstance(result, dict) and "allowed" in result:
                        if not result["allowed"]:
                            reason = result.get("reason", "Daily quota exhausted.")
                            logger.warning(f"Quota reservation denied by DB governor: {reason}")
                            raise QuotaExceededError(reason)

                        # Mirror to memory
                        if is_user:
                            self._memory_user_used += cost
                        else:
                            self._memory_worker_used += cost
                        return result
            except urllib.error.HTTPError as http_err:
                logger.debug(f"Supabase RPC unavailable ({http_err.code}), evaluating in-memory failsafe.")
            except Exception as e:
                logger.debug(f"Supabase RPC connection error ({e}), evaluating in-memory failsafe.")

        # In-Memory Strict Failsafe Guard
        total_used = self._memory_user_used + self._memory_worker_used

        if total_used + cost > self.HARD_STOP_LIMIT:
            reason = (
                f"Hard safety stop: daily limit reached ({total_used}/{self.HARD_STOP_LIMIT}). "
                f"Preserving {self.SAFETY_BUFFER} safety buffer to ensure ₹0.00 cost."
            )
            logger.warning(reason)
            raise QuotaExceededError(reason)

        if is_user:
            if self._memory_user_used + cost > self.USER_RESERVE:
                reason = (
                    f"User analysis quota reached ({self._memory_user_used}/{self.USER_RESERVE}). "
                    f"Resets at 00:00 UTC."
                )
                logger.warning(reason)
                raise QuotaExceededError(reason)

            self._memory_user_used += cost
            return {
                "allowed": True,
                "remaining_user": self.USER_RESERVE - self._memory_user_used,
                "remaining_worker": self.WORKER_BUDGET - self._memory_worker_used,
                "total_used": self._memory_user_used + self._memory_worker_used
            }
        else:
            if self._memory_worker_used + cost > self.WORKER_BUDGET:
                reason = (
                    f"Automated worker budget exhausted ({self._memory_worker_used}/{self.WORKER_BUDGET}). "
                    f"Remaining {self.USER_RESERVE} requests strictly reserved for user on-demand analysis."
                )
                logger.warning(reason)
                raise QuotaExceededError(reason)

            self._memory_worker_used += cost
            return {
                "allowed": True,
                "remaining_user": self.USER_RESERVE - self._memory_user_used,
                "remaining_worker": self.WORKER_BUDGET - self._memory_worker_used,
                "total_used": self._memory_user_used + self._memory_worker_used
            }

    def get_status(self) -> Dict[str, Any]:
        """Return current quota usage and remaining allowance."""
        self._check_memory_rollover()
        return {
            "provider": self.provider,
            "date_utc": self._memory_date,
            "user_used": self._memory_user_used,
            "worker_used": self._memory_worker_used,
            "total_used": self._memory_user_used + self._memory_worker_used,
            "daily_limit": self.HARD_STOP_LIMIT,
            "user_reserve": self.USER_RESERVE,
            "worker_budget": self.WORKER_BUDGET,
            "safety_buffer": self.SAFETY_BUFFER,
            "remaining_user": max(0, self.USER_RESERVE - self._memory_user_used),
            "remaining_worker": max(0, self.WORKER_BUDGET - self._memory_worker_used)
        }
