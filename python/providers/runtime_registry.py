"""Allowed runtime data providers after API-Football removal.

A1/A3/A4 will register real clients. This module only records the allowlist
so decision code cannot silently grow an API-Football dependency.
"""

from __future__ import annotations

ALLOWED_RUNTIME_PROVIDERS: tuple[str, ...] = (
    "football_data_org",
    "football_data_uk",
    "odds_api",
    "manual_lineup",
)

# Historical rows may still carry this id. New runtime calls must not.
RETIRED_PROVIDERS: frozenset[str] = frozenset(
    {"api_football", "api-football", "api-sports"}
)


class ProviderNotAllowed(RuntimeError):
    pass


def assert_provider_allowed(name: str) -> str:
    if name in RETIRED_PROVIDERS or "api-football" in name or "api_football" in name:
        raise ProviderNotAllowed(
            f"Provider {name!r} is retired. See docs/RECOVERY_STATUS.md phase A0."
        )
    if name not in ALLOWED_RUNTIME_PROVIDERS:
        raise ProviderNotAllowed(
            f"Provider {name!r} is not in the v1 allowlist {ALLOWED_RUNTIME_PROVIDERS}."
        )
    return name


def runtime_provider_names() -> tuple[str, ...]:
    for name in ALLOWED_RUNTIME_PROVIDERS:
        assert_provider_allowed(name)
    return ALLOWED_RUNTIME_PROVIDERS
