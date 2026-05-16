from unittest.mock import patch
from models.movie import Movie, MovieStatus
from repository.selected_repository import get_selected_slugs


def _movie(slug, status="watched"):
    return Movie(
        title=slug.replace("-", " ").title(),
        slug=slug,
        url=f"https://letterboxd.com/film/{slug}/",
        added_by="bjoubs",
        date_added="01/01/2025",
        poster="",
        status=status,
        nominated_by="",
        voted_by=[],
        watched_date="02/01/2025",
    )


WATCHED_MOVIES = [
    _movie("the-substance"),
    _movie("dune-part-two"),
    _movie("anora"),
]


def test_get_selected_slugs_returns_watched_slugs():
    with patch("repository.selected_repository.movies_repo.get_movies_by_status", return_value=WATCHED_MOVIES):
        result = get_selected_slugs()
    assert result == ["the-substance", "dune-part-two", "anora"]


def test_get_selected_slugs_empty():
    with patch("repository.selected_repository.movies_repo.get_movies_by_status", return_value=[]):
        assert get_selected_slugs() == []
