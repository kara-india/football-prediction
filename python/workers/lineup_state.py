import hashlib
import json
from typing import Any, Dict


def canonical_lineup_hash(lineup: Dict[str, Any]) -> str:
    payload = {
        "home": {"formation": lineup.get("home", {}).get("formation"), "starters": lineup.get("home", {}).get("starters", [])},
        "away": {"formation": lineup.get("away", {}).get("formation"), "starters": lineup.get("away", {}).get("starters", [])},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def next_lineup_version(existing_versions: list[int]) -> int:
    return max(existing_versions or [0]) + 1
