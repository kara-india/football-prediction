from typing import Optional
from .base import OddsProvider, ProviderHealth

class ProviderRegistry:
    def __init__(self):
        self._providers = []

    def register(self, provider: OddsProvider, priority: int):
        self._providers.append((priority, provider))
        self._providers.sort(key=lambda x: x[0])

    def get_active_providers(self) -> list[OddsProvider]:
        return [p[1] for p in self._providers]

    async def get_1xbet_provider(self) -> Optional[OddsProvider]:
        for _, provider in self._providers:
            try:
                health = await provider.health_check()
                if health.is_1xbet_confirmed:
                    return provider
            except Exception:
                pass
        return None

    async def run_health_checks(self) -> list[ProviderHealth]:
        results = []
        for _, provider in self._providers:
            try:
                results.append(await provider.health_check())
            except Exception:
                pass
        return results

    async def get_health_status(self) -> dict:
        healths = await self.run_health_checks()
        return {
            "providers": [
                {
                    "provider": h.provider,
                    "authenticated": h.authenticated,
                    "reachable": h.reachable,
                    "live_odds_supported": h.live_odds_supported,
                    "prematch_supported": h.prematch_supported,
                    "request_limit": h.request_limit,
                    "requests_remaining": h.requests_remaining,
                    "last_success": h.last_success.isoformat() if h.last_success else None,
                    "last_error": h.last_error,
                    "supported_markets": h.supported_markets,
                    "is_1xbet_confirmed": h.is_1xbet_confirmed,
                }
                for h in healths
            ]
        }
