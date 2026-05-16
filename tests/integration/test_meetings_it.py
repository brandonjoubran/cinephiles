"""
Integration tests — Meetings sheet including ROTW column.
"""
import pytest

import repository.meetings_repository as meetings_repo
import repository.movies_repository as movies_repo
from models.meeting import Meeting
from models.movie import Movie, MovieStatus
from tests.integration.sheet_helpers import MEETINGS_HEADERS, assert_headers, open_tab

pytestmark = pytest.mark.integration


def test_meetings_tab_has_expected_headers(require_integration_env):
    assert_headers(open_tab("Meetings"), MEETINGS_HEADERS)


def test_meetings_every_row_parses(require_integration_env):
    meetings_repo.get_all_meetings()


def test_meeting_rotw_round_trip(integration_movie_slug):
    """Add meeting with ROTW on a selected movie, read back, update, then cleanup."""
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

    meetings_repo.add_meeting(Meeting(
        date="01/15/2025",
        movie_name="IT Integration Film",
        movie_slug=slug,
        start_time="19:00",
        end_time="21:00",
        participants=["it-user"],
        rotw=["it-rotw-a"],
    ))

    meetings = meetings_repo.get_all_meetings()
    row = next(m for m in meetings if m.movie_slug == slug)
    assert row.rotw == ["it-rotw-a"]

    assert "it-rotw-a" in meetings_repo.get_rotw_winners()

    meetings_repo.update_meeting(slug, rotw=["it-rotw-b", "it-rotw-c"])

    updated = next(m for m in meetings_repo.get_all_meetings() if m.movie_slug == slug)
    assert updated.rotw == ["it-rotw-b", "it-rotw-c"]
    assert meetings_repo.get_rotw_winners().count("it-rotw-b") == 1
