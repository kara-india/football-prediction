"""
Database and In-Memory Idempotency Deduplicator
Provides deterministic natural keys, PostgreSQL advisory lock hash keys,
stateless in-memory stream filtering, and batch upsert query formatting.
"""
import hashlib
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union


def _extract_val(obj: Any, *keys: str) -> Any:
    """Helper to extract a value from either a dictionary or object attribute."""
    if isinstance(obj, dict):
        for k in keys:
            if k in obj:
                return obj[k]
        return None
    for k in keys:
        if hasattr(obj, k):
            return getattr(obj, k)
    return None


def _normalize_timestamp(ts: Any, truncate_to_minute: bool = False) -> str:
    """
    Normalize timestamp into a deterministic UTC string representation.
    Optionally truncates seconds/microseconds to enable minute-window deduplication.
    """
    if ts is None:
        return "none"

    if isinstance(ts, (int, float)):
        # Treat as epoch timestamp
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    elif isinstance(ts, datetime):
        if ts.tzinfo is None:
            dt = ts.replace(tzinfo=timezone.utc)
        else:
            dt = ts.astimezone(timezone.utc)
    elif isinstance(ts, str):
        # Attempt ISO parsing if string
        try:
            # Handle Z suffix for fromisoformat in older pythons
            clean_ts = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
        except Exception:
            return ts.strip().lower()
    else:
        return str(ts)

    if truncate_to_minute:
        dt = dt.replace(second=0, microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_line(line: Any) -> Optional[float]:
    """Normalize line to 4 decimal places float or None."""
    if line is None or line == "" or line == "none":
        return None
    try:
        return round(float(line), 4)
    except (ValueError, TypeError):
        return None


def get_match_natural_key(match: Any) -> Tuple[str, Any]:
    """
    Natural key for matches: (provider, provider_fixture_id)
    """
    provider = _extract_val(match, "provider", "provider_id", "source") or "unknown"
    fixture_id = _extract_val(match, "provider_fixture_id", "fixture_id", "api_football_id")
    if fixture_id is None:
        fixture_id = _extract_val(match, "id", "match_id")
    return (str(provider).strip().lower(), str(fixture_id) if fixture_id is not None else "none")


def get_odds_natural_key(odds: Any, truncate_to_minute: bool = False) -> Tuple[str, str, str, str, Optional[float], str]:
    """
    Natural key for odds: (match_id, bookmaker, canonical_market, selection, line, source_timestamp)
    """
    match_id = str(_extract_val(odds, "match_id") or "none").strip()
    bookmaker = str(_extract_val(odds, "bookmaker") or "1xbet").strip().lower()
    market = str(_extract_val(odds, "canonical_market", "market", "market_id") or "none").strip().upper()
    selection = str(_extract_val(odds, "selection") or "none").strip()
    line = _normalize_line(_extract_val(odds, "line"))
    raw_ts = _extract_val(odds, "source_timestamp", "fetched_at", "timestamp")
    norm_ts = _normalize_timestamp(raw_ts, truncate_to_minute=truncate_to_minute)

    return (match_id, bookmaker, market, selection, line, norm_ts)


def get_prediction_natural_key(pred: Any, truncate_to_minute: bool = False) -> Tuple[str, str, str, Optional[float], str]:
    """
    Natural key for predictions: (match_id, market, selection, line, prediction_timestamp)
    """
    match_id = str(_extract_val(pred, "match_id") or "none").strip()
    market = str(_extract_val(pred, "market", "canonical_market") or "none").strip().upper()
    selection = str(_extract_val(pred, "selection") or "none").strip()
    line = _normalize_line(_extract_val(pred, "line"))
    raw_ts = _extract_val(pred, "prediction_timestamp", "predicted_at", "timestamp")
    norm_ts = _normalize_timestamp(raw_ts, truncate_to_minute=truncate_to_minute)

    return (match_id, market, selection, line, norm_ts)


def get_result_natural_key(res: Any) -> Tuple[str, str]:
    """
    Natural key for results: (prediction_id, match_id)
    """
    pred_id = str(_extract_val(res, "prediction_id") or "none").strip()
    match_id = str(_extract_val(res, "match_id") or "none").strip()
    return (pred_id, match_id)


def compute_sha256_key(natural_key: Union[str, Tuple[Any, ...]]) -> str:
    """Computes deterministic 64-character SHA-256 hex string for a given natural key."""
    if isinstance(natural_key, tuple):
        key_str = "|".join(str(item) for item in natural_key)
    else:
        key_str = str(natural_key)
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()


def compute_advisory_lock_id(natural_key: Union[str, Tuple[Any, ...]]) -> int:
    """
    Generates a deterministic signed 64-bit integer suitable for PostgreSQL
    advisory locking: pg_advisory_xact_lock(hash_id).
    Valid range: [-2^63, 2^63 - 1] (i.e. -9223372036854775808 to 9223372036854775807).
    """
    if isinstance(natural_key, tuple):
        key_str = "|".join(str(item) for item in natural_key)
    else:
        key_str = str(natural_key)
    digest = hashlib.sha256(key_str.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=True)


def filter_stream(stream: Iterable[Any], key_fn: Callable[[Any], Any]) -> List[Any]:
    """
    Generic high-performance in-memory duplicate filter.
    Preserves original order, drops subsequent items with identical natural keys.
    Stateless with zero leaks across consecutive invocations.
    """
    seen: Set[Any] = set()
    unique_items: List[Any] = []
    for item in stream:
        k = key_fn(item)
        if k not in seen:
            seen.add(k)
            unique_items.append(item)
    return unique_items


def filter_duplicate_matches(stream: Iterable[Any]) -> List[Any]:
    """Filter duplicate match entities from an incoming stream."""
    return filter_stream(stream, get_match_natural_key)


def filter_duplicate_odds(stream: Iterable[Any], truncate_to_minute: bool = False) -> List[Any]:
    """
    Filter duplicate odds records from an incoming stream.
    Supports minute-level tick rounding when truncate_to_minute=True.
    """
    return filter_stream(stream, lambda o: get_odds_natural_key(o, truncate_to_minute=truncate_to_minute))


def filter_duplicate_predictions(stream: Iterable[Any], truncate_to_minute: bool = False) -> List[Any]:
    """Filter duplicate model predictions from an incoming stream."""
    return filter_stream(stream, lambda p: get_prediction_natural_key(p, truncate_to_minute=truncate_to_minute))


def filter_duplicate_results(stream: Iterable[Any]) -> List[Any]:
    """Filter duplicate settlement results from an incoming stream."""
    return filter_stream(stream, get_result_natural_key)


def format_upsert_sql(
    table: str,
    conflict_columns: List[str],
    update_columns: Optional[List[str]] = None,
    do_nothing: bool = False,
) -> str:
    """
    Format PostgreSQL ON CONFLICT clause for idempotent batch upserts.
    """
    if not conflict_columns:
        raise ValueError("conflict_columns must not be empty")

    cols_clause = ", ".join(conflict_columns)
    if do_nothing or not update_columns:
        return f"ON CONFLICT ({cols_clause}) DO NOTHING"

    set_clauses = [f"{col} = EXCLUDED.{col}" for col in update_columns]
    return f"ON CONFLICT ({cols_clause}) DO UPDATE SET {', '.join(set_clauses)}"


def format_postgrest_upsert_params(
    on_conflict: str,
    ignore_duplicates: bool = True,
) -> Dict[str, str]:
    """
    Format headers and query parameters for Supabase / PostgREST batch upserts.
    """
    resolution = "ignore-duplicates" if ignore_duplicates else "merge-duplicates"
    return {
        "on_conflict": on_conflict,
        "Prefer": f"resolution={resolution}",
    }


class IdempotencyDeduplicator:
    """
    Unified Idempotency and Deduplication manager.
    Can be used statically or instantiated per-pipeline.
    """

    @staticmethod
    def match_key(match: Any) -> Tuple[str, Any]:
        return get_match_natural_key(match)

    @staticmethod
    def odds_key(odds: Any, truncate_to_minute: bool = False) -> Tuple[str, str, str, str, Optional[float], str]:
        return get_odds_natural_key(odds, truncate_to_minute=truncate_to_minute)

    @staticmethod
    def prediction_key(pred: Any, truncate_to_minute: bool = False) -> Tuple[str, str, str, Optional[float], str]:
        return get_prediction_natural_key(pred, truncate_to_minute=truncate_to_minute)

    @staticmethod
    def result_key(res: Any) -> Tuple[str, str]:
        return get_result_natural_key(res)

    @staticmethod
    def lock_id(natural_key: Union[str, Tuple[Any, ...]]) -> int:
        return compute_advisory_lock_id(natural_key)

    @staticmethod
    def hash_key(natural_key: Union[str, Tuple[Any, ...]]) -> str:
        return compute_sha256_key(natural_key)

    @staticmethod
    def advisory_lock_sql(natural_key: Union[str, Tuple[Any, ...]]) -> str:
        """Format PostgreSQL advisory lock query."""
        lid = compute_advisory_lock_id(natural_key)
        return f"SELECT pg_advisory_xact_lock({lid});"

    @staticmethod
    def filter_odds(stream: Iterable[Any], truncate_to_minute: bool = False) -> List[Any]:
        return filter_duplicate_odds(stream, truncate_to_minute=truncate_to_minute)

    @staticmethod
    def filter_predictions(stream: Iterable[Any], truncate_to_minute: bool = False) -> List[Any]:
        return filter_duplicate_predictions(stream, truncate_to_minute=truncate_to_minute)

    @staticmethod
    def filter_matches(stream: Iterable[Any]) -> List[Any]:
        return filter_duplicate_matches(stream)

    @staticmethod
    def filter_results(stream: Iterable[Any]) -> List[Any]:
        return filter_duplicate_results(stream)

    @staticmethod
    def build_upsert_query(
        table: str,
        columns: List[str],
        conflict_columns: List[str],
        update_columns: Optional[List[str]] = None,
        do_nothing: bool = False,
    ) -> str:
        """
        Construct full PostgreSQL INSERT ... ON CONFLICT statement skeleton.
        """
        cols_str = ", ".join(columns)
        placeholders = ", ".join([f"%({col})s" for col in columns])
        conflict_sql = format_upsert_sql(table, conflict_columns, update_columns, do_nothing=do_nothing)
        return f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders}) {conflict_sql};"
