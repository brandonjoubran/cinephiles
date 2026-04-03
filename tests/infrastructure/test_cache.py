from infrastructure.cache import Cache


def test_get_returns_none_when_empty():
    c = Cache()
    assert c.get("anything") is None


def test_set_then_get_returns_value():
    c = Cache()
    c.set("key", [1, 2, 3])
    assert c.get("key") == [1, 2, 3]


def test_get_returns_cached_value_indefinitely():
    c = Cache()
    c.set("key", "value")
    assert c.get("key") == "value"


def test_clear_removes_all_entries():
    c = Cache()
    c.set("a", 1)
    c.set("b", 2)
    c.clear()
    assert c.get("a") is None
    assert c.get("b") is None


def test_set_overwrites_existing_value():
    c = Cache()
    c.set("key", "old")
    c.set("key", "new")
    assert c.get("key") == "new"
