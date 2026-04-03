import pytest
from pydantic import ValidationError
from models.film_log import FilmLog


VALID = {
    "username": "bjoubs",
    "slug": "the-substance",
    "title": "The Substance",
    "rating": 4.0,
    "has_review": True,
    "word_count": 120,
    "review_link": "https://letterboxd.com/bjoubs/film/the-substance/",
    "updated_at": "2025-03-01",
}


# ── Construction ──────────────────────────────────────────────────────────────

def test_film_log_creation():
    r = FilmLog(**VALID)
    assert r.username == "bjoubs"
    assert r.slug == "the-substance"
    assert r.title == "The Substance"
    assert r.rating == 4.0
    assert r.has_review is True
    assert r.word_count == 120


def test_film_log_missing_required_field_raises():
    with pytest.raises(ValidationError):
        FilmLog(username="bjoubs", slug="the-substance")


# ── Username validation ───────────────────────────────────────────────────────

def test_username_empty_raises():
    with pytest.raises(ValidationError, match="username cannot be empty"):
        FilmLog(**{**VALID, "username": ""})


def test_username_whitespace_only_raises():
    with pytest.raises(ValidationError, match="username cannot be empty"):
        FilmLog(**{**VALID, "username": "   "})


def test_username_is_stripped():
    r = FilmLog(**{**VALID, "username": "  bjoubs  "})
    assert r.username == "bjoubs"


# ── Slug validation ───────────────────────────────────────────────────────────

def test_slug_empty_raises():
    with pytest.raises(ValidationError, match="slug cannot be empty"):
        FilmLog(**{**VALID, "slug": ""})


def test_slug_whitespace_only_raises():
    with pytest.raises(ValidationError, match="slug cannot be empty"):
        FilmLog(**{**VALID, "slug": "   "})


# ── Rating validation ────────────────────────────────────────────────────────

def test_rating_below_zero_raises():
    with pytest.raises(ValidationError, match="rating must be between 0 and 5"):
        FilmLog(**{**VALID, "rating": -1})


def test_rating_above_five_raises():
    with pytest.raises(ValidationError, match="rating must be between 0 and 5"):
        FilmLog(**{**VALID, "rating": 5.5})


def test_rating_empty_string_defaults_to_zero():
    r = FilmLog(**{**VALID, "rating": ""})
    assert r.rating == 0.0


def test_rating_none_defaults_to_zero():
    r = FilmLog(**{**VALID, "rating": None})
    assert r.rating == 0.0


def test_rating_zero_is_valid():
    r = FilmLog(**{**VALID, "rating": 0})
    assert r.rating == 0


def test_rating_five_is_valid():
    r = FilmLog(**{**VALID, "rating": 5})
    assert r.rating == 5


# ── Word count validation ─────────────────────────────────────────────────────

def test_word_count_negative_raises():
    with pytest.raises(ValidationError, match="word_count cannot be negative"):
        FilmLog(**{**VALID, "word_count": -1})


def test_word_count_zero_is_valid():
    r = FilmLog(**{**VALID, "word_count": 0})
    assert r.word_count == 0


# ── Serialization ─────────────────────────────────────────────────────────────

def test_film_log_serializes_to_dict():
    r = FilmLog(**VALID)
    d = r.model_dump()
    assert d["username"] == "bjoubs"
    assert d["slug"] == "the-substance"
    assert d["rating"] == 4.0
