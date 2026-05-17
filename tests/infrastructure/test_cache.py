from pathlib import Path

from infrastructure.cache import Cache
from models.movie import Movie, MovieStatus


def test_get_returns_none_when_empty(tmp_path: Path):
    c = Cache(tmp_path / "cache.json")
    assert c.get("anything") is None


def test_set_then_get_returns_value(tmp_path: Path):
    c = Cache(tmp_path / "cache.json")
    c.set("key", [1, 2, 3])
    assert c.get("key") == [1, 2, 3]


def test_get_returns_cached_value_indefinitely(tmp_path: Path):
    c = Cache(tmp_path / "cache.json")
    c.set("key", "value")
    assert c.get("key") == "value"


def test_clear_removes_all_entries(tmp_path: Path):
    c = Cache(tmp_path / "cache.json")
    c.set("a", 1)
    c.set("b", 2)
    c.clear()
    assert c.get("a") is None
    assert c.get("b") is None
    assert not (tmp_path / "cache.json").exists()


def test_set_overwrites_existing_value(tmp_path: Path):
    c = Cache(tmp_path / "cache.json")
    c.set("key", "old")
    c.set("key", "new")
    assert c.get("key") == "new"


def test_clear_then_get_returns_models_not_dicts(tmp_path: Path):
    """Regression: clear() used to skip model registration on the next get()."""
    path = tmp_path / "cache.json"
    movie = Movie(
        title="Test",
        slug="test",
        url="https://letterboxd.com/film/test/",
        added_by="alice",
        date_added="2025-01-01",
        poster="",
        status=MovieStatus.BACKLOG,
        nominated_by="",
        voted_by=[],
        watched_date="",
    )
    c = Cache(path)
    c.clear()
    c.set("movies", [movie])
    loaded = c.get("movies")
    assert isinstance(loaded[0], Movie)
    assert loaded[0].slug == "test"


def test_persists_to_disk_and_survives_new_instance(tmp_path: Path):
    path = tmp_path / "cache.json"
    movie = Movie(
        title="Test",
        slug="test",
        url="https://letterboxd.com/film/test/",
        added_by="alice",
        date_added="2025-01-01",
        poster="",
        status=MovieStatus.BACKLOG,
        nominated_by="",
        voted_by=[],
        watched_date="",
    )
    c1 = Cache(path)
    c1.set("movies", [movie])

    c2 = Cache(path)
    loaded = c2.get("movies")
    assert len(loaded) == 1
    assert loaded[0].slug == "test"
    assert loaded[0].status == MovieStatus.BACKLOG
