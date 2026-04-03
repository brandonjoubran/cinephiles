from unittest.mock import MagicMock, patch
from models.film_log import FilmLog
from repository.film_log_repository import get_all_film_logs, get_film_logs_for_user

FAKE_ROWS = [
    {
        "USERNAME": "bjoubs",
        "SLUG": "the-substance",
        "TITLE": "The Substance",
        "RATING": 4.0,
        "HAS_REVIEW": True,
        "WORD_COUNT": 120,
        "REVIEW_LINK": "https://letterboxd.com/bjoubs/film/the-substance/",
        "UPDATED_AT": "2025-03-01",
    },
    {
        "USERNAME": "kingkrab",
        "SLUG": "dune-part-two",
        "TITLE": "Dune: Part Two",
        "RATING": 4.5,
        "HAS_REVIEW": False,
        "WORD_COUNT": 0,
        "REVIEW_LINK": "",
        "UPDATED_AT": "2025-03-02",
    },
    {
        "USERNAME": "bjoubs",
        "SLUG": "dune-part-two",
        "TITLE": "Dune: Part Two",
        "RATING": 3.5,
        "HAS_REVIEW": False,
        "WORD_COUNT": 0,
        "REVIEW_LINK": "",
        "UPDATED_AT": "2025-03-02",
    },
]


def fake_worksheet(records):
    sheet = MagicMock()
    sheet.get_all_records.return_value = records
    return sheet


def test_get_all_film_logs_returns_models():
    with patch("repository.film_log_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_all_film_logs()
    assert len(result) == 3
    assert all(isinstance(r, FilmLog) for r in result)


def test_get_all_film_logs_maps_fields_correctly():
    with patch("repository.film_log_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_all_film_logs()
    assert result[0].username == "bjoubs"
    assert result[0].slug == "the-substance"
    assert result[0].rating == 4.0
    assert result[0].has_review is True
    assert result[0].word_count == 120


def test_get_all_film_logs_empty_sheet():
    with patch("repository.film_log_repository.get_worksheet", return_value=fake_worksheet([])):
        assert get_all_film_logs() == []


def test_get_film_logs_for_user_filters_by_username():
    with patch("repository.film_log_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_film_logs_for_user("bjoubs")
    assert len(result) == 2
    assert all(r.username == "bjoubs" for r in result)


def test_get_film_logs_for_user_no_matches():
    with patch("repository.film_log_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_film_logs_for_user("nobody")
    assert result == []
