import pytest
from pydantic import ValidationError
from models.meeting import Meeting


def _meeting(**overrides):
    defaults = {
        "date": "01/15/2025",
        "movie_name": "The Substance",
        "movie_slug": "the-substance",
        "start_time": "19:00",
        "end_time": "21:30",
        "participants": "bjoubs, KingKrab, GeoMoD",
    }
    defaults.update(overrides)
    return Meeting(**defaults)


def test_valid_meeting():
    meeting = _meeting()
    assert meeting.movie_slug == "the-substance"
    assert meeting.date == "01/15/2025"


def test_participants_parses_comma_separated():
    meeting = _meeting(participants="bjoubs, KingKrab, GeoMoD")
    assert meeting.participants == ["bjoubs", "KingKrab", "GeoMoD"]


def test_participants_accepts_list():
    meeting = _meeting(participants=["bjoubs", "KingKrab"])
    assert meeting.participants == ["bjoubs", "KingKrab"]


def test_participants_empty_string_returns_empty_list():
    meeting = _meeting(participants="")
    assert meeting.participants == []


def test_empty_movie_slug_raises():
    with pytest.raises(ValidationError):
        _meeting(movie_slug="")


def test_invalid_date_format_raises():
    with pytest.raises(ValidationError):
        _meeting(date="2025-01-15")


def test_serializes_to_dict():
    meeting = _meeting()
    d = meeting.model_dump()
    assert d["participants"] == ["bjoubs", "KingKrab", "GeoMoD"]
    assert d["movie_slug"] == "the-substance"
