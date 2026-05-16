from unittest.mock import MagicMock, patch

from models.film_log import FilmLog
from repository.film_log_repository import save_film_log

SAMPLE_LOG = FilmLog(
    username="bjoubs",
    slug="the-substance",
    title="The Substance",
    rating=4.0,
    has_review=True,
    word_count=10,
    review_link="https://letterboxd.com/bjoubs/film/the-substance/",
    updated_at="2025-03-10",
)


def test_save_film_log_updates_existing_row():
    sheet = MagicMock()
    sheet.row_values.return_value = [
        "USERNAME", "SLUG", "TITLE", "RATING", "HAS_REVIEW", "WORD_COUNT", "REVIEW_LINK", "UPDATED_AT",
    ]
    sheet.get_all_records.return_value = [
        {"USERNAME": "bjoubs", "SLUG": "the-substance"},
    ]

    with patch("repository.film_log_repository.get_worksheet", return_value=sheet):
        save_film_log(SAMPLE_LOG)

    sheet.update.assert_called_once()
    sheet.append_row.assert_not_called()


def test_save_film_log_appends_when_missing():
    sheet = MagicMock()
    sheet.row_values.return_value = [
        "USERNAME", "SLUG", "TITLE", "RATING", "HAS_REVIEW", "WORD_COUNT", "REVIEW_LINK", "UPDATED_AT",
    ]
    sheet.get_all_records.return_value = []

    with patch("repository.film_log_repository.get_worksheet", return_value=sheet):
        save_film_log(SAMPLE_LOG)

    sheet.append_row.assert_called_once()
    sheet.update.assert_not_called()
