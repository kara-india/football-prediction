import hashlib
import json
from typing import Any, Dict, List


def canonical_lineup_hash(lineup: Dict[str, Any]) -> str:
    """Stable hash of the football-relevant lineup payload."""
    payload = {
        "home": {
            "formation": lineup.get("home", {}).get("formation"),
            "starters": lineup.get("home", {}).get("starters", []),
        },
        "away": {
            "formation": lineup.get("away", {}).get("formation"),
            "starters": lineup.get("away", {}).get("starters", []),
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def lineup_version(existing_hashes: List[str], new_hash: str) -> int:
    """Return existing version for duplicate hash, otherwise next monotonic version."""
    try:
        return existing_hashes.index(new_hash) + 1
    except ValueError:
        return len(existing_hashes) + 1
