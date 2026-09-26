"""
Central PostgreSQL-backed API quota governor.

There is intentionally no process-local quota fallback. A local counter cannot
enforce a provider-wide daily cap across multiple serverless instances,
workers, or concurrent processes. If the authoritative Supabase governor is
unavailable, the safe behavior is to abstain from the external API request.
"""
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("QuotaManager")

DEFAULT_PROVIDER = "api-football"


class QuotaExceededError(Exception):
    """Raised when an API call must be rejected by the quota governor."""
    pass


class CentralQuotaManager:
    HARD_STOP_LIMIT = 95
    USER_RESERVE = 50
    WORKER_BUDGET = 45
    SAFETY_BUFFER = 5

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        provider: str = DEFAULT_PROVIDER,
        rpc_call: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None,
    ):
        self.provider = provider
        self.supabase_url = supabase_url or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self._rpc_call_override = rpc_call

    def _rpc_call(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._rpc_call_override is not None:
            return self._rpc_call_override(function_name, payload)

        if not self.supabase_url or not self.supabase_key:
            raise QuotaExceededError("QUOTA_GOVERNOR_UNCONFIGURED")

        rpc_url = f"{self.supabase_url.rstrip('/')}/rest/v1/rpc/{function_name}"
        request = urllib.request.Request(
            rpc_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise QuotaExceededError(f"QUOTA_GOVERNOR_HTTP_{exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise QuotaExceededError("QUOTA_GOVERNOR_UNAVAILABLE") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise QuotaExceededError("QUOTA_GOVERNOR_INVALID_RESPONSE") from exc

        if not isinstance(data, dict):
            raise QuotaExceededError("QUOTA_GOVERNOR_INVALID_RESPONSE")

        return data

    def reserve(self, is_user: bool = False, cost: int = 1) -> Dict[str, Any]:
        if not isinstance(cost, int) or isinstance(cost, bool) or cost <= 0:
            raise QuotaExceededError("INVALID_QUOTA_COST")

        result = self._rpc_call(
            "reserve_api_quota",
            {
                "p_provider": self.provider,
                "p_cost": cost,
                "p_is_user": is_user,
            },
        )

        if result.get("allowed") is not True:
            raise QuotaExceededError(str(result.get("reason") or "API quota reservation denied"))

        return result

    def get_status(self) -> Dict[str, Any]:
        try:
            result = self._rpc_call(
                "get_api_quota_status",
                {"p_provider": self.provider},
            )
        except QuotaExceededError as exc:
            return {
                "available": False,
                "provider": self.provider,
                "date_utc": None,
                "user_used": 0,
                "worker_used": 0,
                "total_used": 0,
                "daily_limit": self.HARD_STOP_LIMIT,
                "user_reserve": self.USER_RESERVE,
                "worker_budget": self.WORKER_BUDGET,
                "safety_buffer": self.SAFETY_BUFFER,
                "remaining_user": 0,
                "remaining_worker": 0,
                "reason": str(exc),
            }

        if result.get("available") is not True:
            return {
                "available": False,
                "provider": self.provider,
                "date_utc": result.get("date_utc"),
                "reason": str(result.get("reason") or "QUOTA_GOVERNOR_INVALID_RESPONSE"),
            }

        return {
            "available": True,
            "provider": self.provider,
            "date_utc": result.get("date_utc"),
            "user_used": result.get("user_requests_made", 0),
            "worker_used": result.get("worker_requests_made", 0),
            "total_used": result.get("total_used", 0),
            "daily_limit": result.get("daily_limit", self.HARD_STOP_LIMIT),
            "user_reserve": result.get("user_reserve", self.USER_RESERVE),
            "worker_budget": result.get("worker_budget", self.WORKER_BUDGET),
            "safety_buffer": result.get("safety_buffer", self.SAFETY_BUFFER),
            "remaining_user": result.get("remaining_user", 0),
            "remaining_worker": result.get("remaining_worker", 0),
        }
