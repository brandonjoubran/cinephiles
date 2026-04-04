import pytest
from pydantic import ValidationError
from models.movie import Movie, MovieStatus


def _movie(**overrides):
    defaults = {
        "title": "The Substance",
        "slug": "the-substance",
        "url": "https://letterboxd.com/film/the-substance/",
        "added_by": "bjoubs",
        "date_added": "01/15/2025",
        "poster": "https://image.tmdb.org/t/p/w500/poster.jpg",
        "status": "backlog",
        "nominated_by": "",
        "voted_by": "",
        "watched_date": "",
        "rotw": "",
    }
    defaults.update(overrides)
    return Movie(**defaults)


# ── Status ────────────────────────────────────────────────────────────────────

def test_status_backlog():
    movie = _movie(status="backlog")
    assert movie.status == MovieStatus.BACKLOG


def test_status_nominated():
    movie = _movie(status="nominated")
    assert movie.status == MovieStatus.NOMINATED


def test_status_selected():
    movie = _movie(status="selected")
    assert movie.status == MovieStatus.SELECTED


def test_status_watched():
    movie = _movie(status="watched")
    assert movie.status == MovieStatus.WATCHED


def test_empty_status_defaults_to_backlog():
    movie = _movie(status="")
    assert movie.status == MovieStatus.BACKLOG


def test_invalid_status_raises():
    with pytest.raises(ValidationError):
        _movie(status="deleted")


# ── Comma-separated parsing ──────────────────────────────────────────────────

def test_voted_by_parses_comma_separated_string():
    movie = _movie(voted_by="bjoubs, KingKrab, GeoMoD")
    assert movie.voted_by == ["bjoubs", "KingKrab", "GeoMoD"]


def test_voted_by_empty_string_returns_empty_list():
    movie = _movie(voted_by="")
    assert movie.voted_by == []


def test_voted_by_accepts_list():
    movie = _movie(voted_by=["bjoubs", "KingKrab"])
    assert movie.voted_by == ["bjoubs", "KingKrab"]


def test_rotw_parses_comma_separated_string():
    movie = _movie(rotw="bjoubs, KingKrab")
    assert movie.rotw == ["bjoubs", "KingKrab"]


def test_rotw_single_winner():
    movie = _movie(rotw="bjoubs")
    assert movie.rotw == ["bjoubs"]


def test_rotw_empty_string_returns_empty_list():
    movie = _movie(rotw="")
    assert movie.rotw == []


# ── Validation ────────────────────────────────────────────────────────────────

def test_empty_title_raises():
    with pytest.raises(ValidationError):
        _movie(title="")


def test_empty_slug_raises():
    with pytest.raises(ValidationError):
        _movie(slug="")


def test_title_is_stripped():
    movie = _movie(title="  The Substance  ")
    assert movie.title == "The Substance"


def test_slug_is_stripped():
    movie = _movie(slug="  the-substance  ")
    assert movie.slug == "the-substance"


# ── Serialization ─────────────────────────────────────────────────────────────

def test_serializes_to_dict():
    movie = _movie(status="watched", voted_by="bjoubs, KingKrab", rotw="bjoubs")
    d = movie.model_dump()
    assert d["status"] == MovieStatus.WATCHED
    assert d["voted_by"] == ["bjoubs", "KingKrab"]
    assert d["rotw"] == ["bjoubs"]
