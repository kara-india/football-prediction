from python.workers.lineup_state import canonical_lineup_hash, lineup_version


def test_lineup_hash_is_order_stable_for_dict_keys():
    a = {"home": {"formation": "4-3-3", "starters": [{"id": 1}, {"id": 2}]}, "away": {"formation": "4-4-2", "starters": [{"id": 3}]}}
    b = {"away": {"starters": [{"id": 3}], "formation": "4-4-2"}, "home": {"starters": [{"id": 1}, {"id": 2}], "formation": "4-3-3"}}
    assert canonical_lineup_hash(a) == canonical_lineup_hash(b)


def test_lineup_hash_changes_when_starter_changes():
    a = {"home": {"formation": "4-3-3", "starters": [{"id": 1}]}, "away": {"formation": "4-4-2", "starters": []}}
    b = {"home": {"formation": "4-3-3", "starters": [{"id": 2}]}, "away": {"formation": "4-4-2", "starters": []}}
    assert canonical_lineup_hash(a) != canonical_lineup_hash(b)


def test_lineup_version_is_idempotent_for_duplicate_hash():
    assert lineup_version(["a", "b"], "b") == 2
    assert lineup_version(["a", "b"], "c") == 3
