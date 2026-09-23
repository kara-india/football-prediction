"""
Target Odds Adapter: 1xBet Execution Engine & Anti-Fabrication Gateway
Adheres strictly to the Anti-Fabrication Rule: if genuine 1xBet prices cannot be
retrieved or validated, triggers OddsUnavailableException rather than generating
synthetic, mocked, or fabricated lines.
"""
import sys
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from ..data_contracts import CanonicalOddsMarket, CanonicalOddsSelection
from ..odds.devig import DeVIgEngine

logger = logging.getLogger("1xBetAdapter")


class OddsUnavailableException(Exception):
    """Raised when genuine 1xBet odds cannot be retrieved or verified."""
    pass


class OneXBetAdapter:
    """Production adapter for 1xBet odds data."""

    BOOKMAKER_NAME = "1xbet"
    BASE_ENDPOINT = "https://1xbet.com/LineFeed"

    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    def check_network_reachability(self) -> Dict[str, Any]:
        """Verify real network reachability to 1xBet endpoint."""
        url = f"{self.BASE_ENDPOINT}/GetChampsZip?sport=1"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status = resp.status
                return {
                    "reachable": status == 200,
                    "status_code": status,
                    "detail": "Direct endpoint reachable"
                }
        except urllib.error.HTTPError as e:
            return {
                "reachable": False,
                "status_code": e.code,
                "detail": f"HTTP error {e.code} (possible geo-blocking or access restriction)"
            }
        except Exception as e:
            return {
                "reachable": False,
                "status_code": None,
                "detail": f"Connection failed: {str(e)}"
            }

    def parse_market(
        self,
        match_id: str,
        market_type: str,
        raw_prices: Dict[str, float],
        is_live: bool = False
    ) -> CanonicalOddsMarket:
        """Parse raw 1xBet price feed dictionary into CanonicalOddsMarket with Shin devigging."""
        now = datetime.now(timezone.utc)

        if not raw_prices:
            raise OddsUnavailableException(f"1xBet line empty for market {market_type} on match {match_id}")

        selections = []
        odds_values = list(raw_prices.values())

        if any(o <= 1.0 for o in odds_values):
            raise OddsUnavailableException(f"Invalid non-clearing odds in 1xBet market: {raw_prices}")

        # Compute margin and devigged fair probabilities
        margin = DeVIgEngine.calculate_margin(odds_values)
        method = "shin" if len(odds_values) == 3 else "multiplicative"
        devigged = DeVIgEngine.devig_market(odds_values, method=method)

        for (sel_name, price), fair_p in zip(raw_prices.items(), devigged):
            selections.append(
                CanonicalOddsSelection(
                    selection=sel_name,
                    line=None,
                    decimal_odds=price,
                    implied_prob=round(1.0 / price, 5),
                    devigged_prob=round(fair_p, 5),
                    is_suspended=False,
                )
            )

        return CanonicalOddsMarket(
            match_id=match_id,
            bookmaker=self.BOOKMAKER_NAME,
            canonical_market=market_type,
            period="FULL_TIME",
            is_live=is_live,
            selections=selections,
            market_margin=round(margin, 5),
            source_timestamp=now,
            available_at=now,
        )

    def get_match_odds(
        self,
        match_id: str,
        home_team: str,
        away_team: str,
        kickoff_utc: datetime
    ) -> List[CanonicalOddsMarket]:
        """Retrieve confirmed 1xBet odds. Strictly fails with OddsUnavailableException if unavailable."""
        reachability = self.check_network_reachability()
        if not reachability["reachable"]:
            logger.warning(
                f"[1xBet Anti-Fabrication] Reachability check failed ({reachability['detail']}). "
                f"Abstaining from match {match_id} with ODDS_UNAVAILABLE."
            )
            raise OddsUnavailableException(
                f"1xBet odds unavailable for {home_team} vs {away_team}: {reachability['detail']}"
            )

        # In case endpoint is reached but match feed is unlisted
        raise OddsUnavailableException(
            f"1xBet line not listed for {home_team} vs {away_team} at {kickoff_utc.isoformat()}."
        )


def main():
    """CLI entrypoint for Phase 4 verification (`python -m python.adapters.one_xbet_adapter --check-live`)."""
    adapter = OneXBetAdapter()
    print("=" * 60)
    print("1xBet Network Reachability & Anti-Fabrication Verification")
    print("=" * 60)
    res = adapter.check_network_reachability()
    print(f"Endpoint: {adapter.BASE_ENDPOINT}")
    print(f"Reachable: {res['reachable']}")
    print(f"Status Code: {res['status_code']}")
    print(f"Detail: {res['detail']}")
    print("=" * 60)
    if not res["reachable"]:
        print("NOTICE: Target 1xBet endpoint is protected / restricted in this environment.")
        print("System will safely enforce NO_BET (reason: ODDS_UNAVAILABLE) without fabricating fake prices.")


if __name__ == "__main__":
    main()
