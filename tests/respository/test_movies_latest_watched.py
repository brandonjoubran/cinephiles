from datetime import date
from unittest.mock import patch

from models.movie import Movie, MovieStatus
from repository.movies_repository import get_latest_watched_date


def _watched(slug: str, watched_date: str) -> Movie:
    return Movie(
        title=slug,
        slug=slug,
        url="",
        added_by="",
        date_added="",
        poster="",
        status=MovieStatus.WATCHED,
        nominated_by="",
        voted_by=[],
        watched_date=watched_date,
    )


def test_get_latest_watched_date_returns_most_recent():
    movies = [_watched("old", "01/01/2025"), _watched("recent", "02/15/2025")]
    with patch("repository.movies_repository.get_movies_by_status", return_value=movies):
        assert get_latest_watched_date() == date(2025, 2, 15)


def test_get_latest_watched_date_excludes_slug():
    movies = [_watched("current", "03/01/2025"), _watched("prior", "02/01/2025")]
    with patch("repository.movies_repository.get_movies_by_status", return_value=movies):
        assert get_latest_watched_date(exclude_slug="current") == date(2025, 2, 1)
