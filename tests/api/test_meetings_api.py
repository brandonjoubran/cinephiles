from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from models.meeting import Meeting

client = TestClient(app)

FAKE_MEETINGS = [
    Meeting(
        date="01/15/2025",
        movie_name="The Substance",
        movie_slug="the-substance",
        start_time="19:00",
        end_time="21:30",
        participants=["bjoubs"],
        rotw=["KingKrab"],
    ),
]


def test_list_meetings_returns_200():
    with patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS):
        response = client.get("/meetings")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_add_meeting_returns_200():
    from models.movie import Movie, MovieStatus
    selected = Movie(
        title="Heat",
        slug="heat-1995",
        url="https://letterboxd.com/film/heat-1995/",
        added_by="bjoubs",
        date_added="01/01/2025",
        poster="poster.jpg",
        status=MovieStatus.SELECTED,
        nominated_by="",
        voted_by=[],
        watched_date="",
    )
    with (
        patch("service.meetings_service.movies_repo.get_movie_by_slug", return_value=selected),
        patch("service.meetings_service.meetings_repo.add_meeting"),
    ):
        response = client.post("/meetings", json={
            "date": "03/01/2025",
            "movie_name": "Heat",
            "movie_slug": "heat-1995",
            "start_time": "19:00",
            "end_time": "22:00",
            "participants": ["bjoubs", "KingKrab"],
            "rotw": ["GeoMoD"],
        })
    assert response.status_code == 200


def test_update_meeting_rotw_returns_200():
    with (
        patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS),
        patch("service.meetings_service.meetings_repo.update_meeting"),
    ):
        response = client.put("/meetings/the-substance", json={"rotw": ["bjoubs", "KingKrab"]})
    assert response.status_code == 200


def test_update_meeting_returns_200():
    with (
        patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS),
        patch("service.meetings_service.meetings_repo.update_meeting"),
    ):
        response = client.put("/meetings/the-substance", json={"start_time": "18:30"})
    assert response.status_code == 200


def test_update_meeting_not_found_returns_404():
    with patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS):
        response = client.put("/meetings/nonexistent", json={"start_time": "18:30"})
    assert response.status_code == 404


def test_delete_meeting_returns_200():
    with (
        patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS),
        patch("service.meetings_service.meetings_repo.delete_meeting"),
    ):
        response = client.delete("/meetings/the-substance")
    assert response.status_code == 200


def test_delete_meeting_not_found_returns_404():
    with patch("service.meetings_service.meetings_repo.get_all_meetings", return_value=FAKE_MEETINGS):
        response = client.delete("/meetings/nonexistent")
    assert response.status_code == 404
