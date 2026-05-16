"""
Integration tests — Movies sheet lifecycle (add / complete / delete).
"""
import pytest

import repository.movies_repository as movies_repo
from models.movie import Movie, MovieStatus
from service.movies_service import complete_movie
from tests.integration.sheet_helpers import MOVIES_HEADERS, assert_headers, open_tab

pytestmark = pytest.mark.integration


def test_movies_tab_has_expected_headers(require_integration_env):
    assert_headers(open_tab("Movies"), MOVIES_HEADERS, forbidden=["ROTW"])


def test_movies_every_row_parses(require_integration_env):
    """Full sheet load via repository — any bad row or column drift fails here."""
    movies_repo.get_all_movies()


def test_add_complete_and_cleanup_movie(integration_movie_slug):
    slug = integration_movie_slug

    movies_repo.add_movie(Movie(
        title="IT Integration Film",
        slug=slug,
        url=f"https://letterboxd.com/film/{slug}/",
        added_by="it-user",
        date_added="01/01/2025",
        poster="https://example.com/poster.jpg",
        status=MovieStatus.SELECTED,
        nominated_by="",
        voted_by=[],
        watched_date="",
    ))

    found = movies_repo.get_movie_by_slug(slug)
    assert found is not None
    assert found.status == MovieStatus.SELECTED

    completed = complete_movie(slug)
    assert completed.status == MovieStatus.WATCHED
    assert completed.watched_date

    after = movies_repo.get_movie_by_slug(slug)
    assert after.status == MovieStatus.WATCHED
