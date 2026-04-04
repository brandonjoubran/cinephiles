from unittest.mock import patch
from models.movie import Movie, MovieStatus
from repository.selected_repository import get_selected_slugs, get_rotw_winners


def _movie(slug, rotw="", status="watched"):
    return Movie(
        title=slug.replace("-", " ").title(),
        slug=slug,
        url=f"https://letterboxd.com/film/{slug}/",
        added_by="bjoubs",
        date_added="01/01/2025",
        poster="",
        status=status,
        nominated_by="",
        voted_by="",
        watched_date="02/01/2025",
        rotw=rotw,
    )


WATCHED_MOVIES = [
    _movie("the-substance", rotw="bjoubs"),
    _movie("dune-part-two", rotw="bjoubs, KingKrab"),
    _movie("anora", rotw=""),
]


# ── get_selected_slugs ────────────────────────────────────────────────────────

def test_get_selected_slugs_returns_watched_slugs():
    with patch("repository.selected_repository.movies_repo.get_movies_by_status", return_value=WATCHED_MOVIES):
        result = get_selected_slugs()
    assert result == ["the-substance", "dune-part-two", "anora"]


def test_get_selected_slugs_empty():
    with patch("repository.selected_repository.movies_repo.get_movies_by_status", return_value=[]):
        assert get_selected_slugs() == []


# ── get_rotw_winners ──────────────────────────────────────────────────────────

def test_get_rotw_winners_returns_flat_list():
    with patch("repository.selected_repository.movies_repo.get_movies_by_status", return_value=WATCHED_MOVIES):
        result = get_rotw_winners()
    assert result == ["bjoubs", "bjoubs", "KingKrab"]


def test_get_rotw_winners_empty():
    with patch("repository.selected_repository.movies_repo.get_movies_by_status", return_value=[]):
        assert get_rotw_winners() == []


def test_get_rotw_winners_no_rotw():
    movies = [_movie("anora", rotw="")]
    with patch("repository.selected_repository.movies_repo.get_movies_by_status", return_value=movies):
        assert get_rotw_winners() == []
