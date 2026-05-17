from unittest.mock import patch

from models.selected_film import SelectedFilm
from repository.selected_repository import get_selected_slugs


def _film(slug: str, watched_date: str) -> SelectedFilm:
    return SelectedFilm(
        title=slug,
        slug=slug,
        url=f"https://letterboxd.com/film/{slug}/",
        added_by="bjoubs",
        date_added="01/01/2025",
        poster="",
        nominated_by="",
        voted_by=[],
        watched_date=watched_date,
    )


def test_get_selected_slugs_sorted_by_watched_date():
    films = [
        _film("newest", "03/15/2025"),
        _film("oldest", "01/01/2024"),
        _film("middle", "06/01/2024"),
    ]
    with patch("repository.selected_repository.get_all_selected", return_value=films):
        assert get_selected_slugs() == ["oldest", "middle", "newest"]


def test_get_selected_slugs_empty():
    with patch("repository.selected_repository.get_all_selected", return_value=[]):
        assert get_selected_slugs() == []
