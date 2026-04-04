from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from models.movie import Movie, MovieStatus

client = TestClient(app)


def _movie(slug="the-substance", status="backlog", **overrides):
    defaults = {
        "title": slug.replace("-", " ").title(),
        "slug": slug,
        "url": f"https://letterboxd.com/film/{slug}/",
        "added_by": "bjoubs",
        "date_added": "01/01/2025",
        "poster": "poster.jpg",
        "status": status,
        "nominated_by": "",
        "voted_by": [],
        "watched_date": "",
        "rotw": [],
    }
    defaults.update(overrides)
    return Movie(**defaults)


def test_list_movies_returns_200():
    with patch("service.movies_service.movies_repo.get_all_movies", return_value=[]):
        response = client.get("/movies")
    assert response.status_code == 200
    assert response.json() == []


def test_get_movie_returns_200():
    movie = _movie()
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        response = client.get("/movies/the-substance")
    assert response.status_code == 200
    assert response.json()["slug"] == "the-substance"


def test_get_movie_returns_404():
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=None):
        response = client.get("/movies/nonexistent")
    assert response.status_code == 404


def test_add_movie_returns_200():
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=None),
        patch("service.movies_service.movies_repo.add_movie"),
    ):
        response = client.post("/movies", json={
            "title": "Heat",
            "slug": "heat-1995",
            "url": "https://letterboxd.com/film/heat-1995/",
            "added_by": "bjoubs",
            "poster": "poster.jpg",
        })
    assert response.status_code == 200
    assert response.json()["slug"] == "heat-1995"
    assert response.json()["status"] == "backlog"


def test_add_movie_duplicate_returns_409():
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=_movie()):
        response = client.post("/movies", json={
            "title": "The Substance",
            "slug": "the-substance",
            "url": "url",
            "added_by": "bjoubs",
            "poster": "poster",
        })
    assert response.status_code == 409


def test_nominate_returns_200():
    movie = _movie(status="backlog")
    nominated = _movie(status="nominated", nominated_by="KingKrab")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, nominated]),
        patch("service.movies_service.movies_repo.get_movies_by_status", return_value=[]),
        patch("service.movies_service.movies_repo.update_movie_fields"),
        patch("service.movies_service.nomination_log_repo.add_nomination"),
    ):
        response = client.post("/movies/the-substance/nominate", json={"username": "KingKrab"})
    assert response.status_code == 200
    assert response.json()["status"] == "nominated"


def test_vote_returns_200():
    movie = _movie(status="nominated")
    updated = _movie(status="nominated", voted_by=["bjoubs"])
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, updated]),
        patch("service.movies_service.movies_repo.update_movie_fields"),
    ):
        response = client.post("/movies/the-substance/vote", json={"username": "bjoubs"})
    assert response.status_code == 200
    assert "bjoubs" in response.json()["voted_by"]


def test_select_returns_200():
    movie = _movie(status="nominated")
    selected = _movie(status="selected")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, selected]),
        patch("service.movies_service.movies_repo.update_movie_fields"),
    ):
        response = client.post("/movies/the-substance/select")
    assert response.status_code == 200
    assert response.json()["status"] == "selected"


def test_complete_returns_200():
    movie = _movie(status="selected", nominated_by="KingKrab")
    watched = _movie(status="watched")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, watched]),
        patch("service.movies_service.movies_repo.update_movie_fields"),
        patch("service.movies_service.movies_repo.get_movies_by_status", return_value=[]),
        patch("service.movies_service.nomination_log_repo.add_nomination"),
        patch("service.movies_service.meetings_repo.add_meeting"),
    ):
        response = client.post("/movies/the-substance/complete", json={
            "rotw_winners": ["bjoubs"],
            "meeting_start_time": "19:00",
            "meeting_end_time": "21:30",
            "participants": ["bjoubs", "KingKrab"],
        })
    assert response.status_code == 200
    assert response.json()["status"] == "watched"


def test_delete_movie_returns_200():
    movie = _movie(status="backlog")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie),
        patch("service.movies_service.movies_repo.delete_movie"),
    ):
        response = client.delete("/movies/the-substance")
    assert response.status_code == 200
    assert "deleted" in response.json()["detail"].lower()


def test_delete_movie_rejects_non_backlog():
    movie = _movie(status="nominated")
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        response = client.delete("/movies/the-substance")
    assert response.status_code == 400
