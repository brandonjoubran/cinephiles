import pytest
from unittest.mock import patch
from fastapi import HTTPException
from models.meeting import Meeting
from models.movie import Movie, MovieStatus
from service.meetings_service import get_all_meetings, add_meeting, update_meeting, delete_meeting

FAKE_MEETINGS = [
    Meeting(date="01/15/2025", movie_name="The Substance", movie_slug="the-substance", start_time="19:00", end_time="21:30", participants=["bjoubs", "KingKrab"], rotw=[]),
    Meeting(date="01/22/2025", movie_name="Anora", movie_slug="anora", start_time="20:00", end_time="22:00", participants=["bjoubs"], rotw=["bjoubs"]),
]

SELECTED_MOVIE = Movie(
    title="The Substance",
    slug="the-substance",
    url="https://letterboxd.com/film/the-substance/",
    added_by="bjoubs",
    date_added="01/01/2025",
    poster="poster.jpg",
    status=MovieStatus.SELECTED,
    nominated_by="",
    voted_by=[],
    watched_date="",
)


def test_add_meeting_before_complete_allowed():
    meeting = Meeting(
        date="03/01/2025",
        movie_name="The Substance",
        movie_slug="the-substance",
        start_time="19:00",
        end_time="21:30",
        participants=["bjoubs"],
        rotw=["KingKrab"],
    )
    with (
        patch("service.meetings_service.movies_repo.get_movie_by_slug", return_value=SELECTED_MOVIE),
        patch("service.meetings_service.meetings_repo.add_meeting") as mock_add,
    ):
        add_meeting(meeting)
    mock_add.assert_called_once_with(meeting)


def test_add_meeting_unknown_movie_raises_404():
    meeting = Meeting(
        date="03/01/2025",
        movie_name="Missing",
        movie_slug="missing",
        start_time="19:00",
        end_time="21:30",
        participants=["bjoubs"],
    )
    with patch("service.meetings_service.movies_repo.get_movie_by_slug", return_value=None):
        with pytest.raises(HTTPException) as exc:
            add_meeting(meeting)
        assert exc.value.status_code == 404


def test_get_all_meetings():
    with patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS):
        result = get_all_meetings()
    assert len(result) == 2


def test_update_meeting_calls_repo():
    with (
        patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS),
        patch("service.meetings_service.meetings_repo.update_meeting") as mock_update,
    ):
        update_meeting("the-substance", start_time="18:30")
    mock_update.assert_called_once_with("the-substance", start_time="18:30")


def test_update_meeting_not_found_raises_404():
    with patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS):
        with pytest.raises(HTTPException) as exc:
            update_meeting("nonexistent", start_time="18:30")
        assert exc.value.status_code == 404


def test_delete_meeting_calls_repo():
    with (
        patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS),
        patch("service.meetings_service.meetings_repo.delete_meeting") as mock_delete,
    ):
        delete_meeting("anora")
    mock_delete.assert_called_once_with("anora")


def test_delete_meeting_not_found_raises_404():
    with patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS):
        with pytest.raises(HTTPException) as exc:
            delete_meeting("nonexistent")
        assert exc.value.status_code == 404
