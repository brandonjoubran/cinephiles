import pytest
from pydantic import ValidationError
from models.nomination_log import NominationLog


def test_valid_nomination_log():
    log = NominationLog(slug="the-substance", nominated_by="bjoubs", voted_by="KingKrab, GeoMoD", date_nominated="01/15/2025")
    assert log.slug == "the-substance"
    assert log.nominated_by == "bjoubs"
    assert log.voted_by == ["KingKrab", "GeoMoD"]
    assert log.date_nominated == "01/15/2025"


def test_empty_slug_raises():
    with pytest.raises(ValidationError):
        NominationLog(slug="", nominated_by="bjoubs", voted_by="", date_nominated="01/15/2025")


def test_empty_nominated_by_raises():
    with pytest.raises(ValidationError):
        NominationLog(slug="the-substance", nominated_by="", voted_by="", date_nominated="01/15/2025")


def test_invalid_date_format_raises():
    with pytest.raises(ValidationError):
        NominationLog(slug="the-substance", nominated_by="bjoubs", voted_by="", date_nominated="2025-01-15")


def test_strips_whitespace():
    log = NominationLog(slug="  the-substance  ", nominated_by="  bjoubs  ", voted_by="", date_nominated="01/15/2025")
    assert log.slug == "the-substance"
    assert log.nominated_by == "bjoubs"


def test_voted_by_parses_comma_separated():
    log = NominationLog(slug="anora", nominated_by="bjoubs", voted_by="KingKrab, GeoMoD, bjoubs", date_nominated="01/15/2025")
    assert log.voted_by == ["KingKrab", "GeoMoD", "bjoubs"]


def test_voted_by_empty_string_returns_empty_list():
    log = NominationLog(slug="anora", nominated_by="bjoubs", voted_by="", date_nominated="01/15/2025")
    assert log.voted_by == []


def test_voted_by_accepts_list():
    log = NominationLog(slug="anora", nominated_by="bjoubs", voted_by=["KingKrab"], date_nominated="01/15/2025")
    assert log.voted_by == ["KingKrab"]
