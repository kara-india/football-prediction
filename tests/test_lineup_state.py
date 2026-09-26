from python.workers.lineup_state import canonical_lineup_hash, next_lineup_version


def test_lineup_hash_is_stable():
    a = {"home": {"formation": "4-3-3", "starters": [{"id": 1}]}, "away": {"formation": "4-4-2", "starters": [{"id": 2}]}}
    b = {"away": {"starters": [{"id": 2}], "formation": "4-4-2"}, "home": {"starters": [{"id": 1}], "formation": "4-3-3"}}
    assert canonical_lineup_hash(a) == canonical_lineup_hash(b)


def test_lineup_hash_changes_with_starter():
    a = {"home": {"formation": "4-3-3", "starters": [{"id": 1}]}, "away": {"starters": []}}
    b = {"home": {"formation": "4-3-3", "starters": [{"id": 2}]}, "away": {"starters": []}}
    assert canonical_lineup_hash(a) != canonical_lineup_hash(b)


def test_next_lineup_version_is_monotonic():
    assert next_lineup_version([]) == 1
    assert next_lineup_version([1]) == 2
    assert next_lineup_version([1, 2, 3]) == 4
