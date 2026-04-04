import pytest
from unittest.mock import patch
from fastapi import HTTPException
from models.meeting import Meeting
from service.meetings_service import get_all_meetings, update_meeting, delete_meeting

FAKE_MEETINGS = [
    Meeting(date="01/15/2025", movie_name="The Substance", movie_slug="the-substance", start_time="19:00", end_time="21:30", participants=["bjoubs", "KingKrab"]),
    Meeting(date="01/22/2025", movie_name="Anora", movie_slug="anora", start_time="20:00", end_time="22:00", participants=["bjoubs"]),
]


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
