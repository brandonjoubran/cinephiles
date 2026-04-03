from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from models.user_stats import UserStats
from models.club_stats import ClubStats, FilmHighlight

client = TestClient(app)

FAKE_STATS = [
    UserStats(username="bjoubs", movies_watched=50, average_rating=3.75, num_reviews=10, avg_words_per_review=85.5, streak=5),
    UserStats(username="kingkrab", movies_watched=30, average_rating=4.0, num_reviews=5, avg_words_per_review=60.0, streak=3),
]

FAKE_CLUB_STATS = ClubStats(
    total_movies=10,
    total_reviews=5,
    average_rating=3.5,
    highest_rated=FilmHighlight(title="The Substance", slug="the-substance", value=4.5),
    lowest_rated=FilmHighlight(title="Dune: Part Two", slug="dune-part-two", value=2.0),
    most_divisive=FilmHighlight(title="Dune: Part Two", slug="dune-part-two", value=1.5),
    longest_review=FilmHighlight(title="The Substance", slug="the-substance", value=300),
)


def test_list_user_stats_returns_200():
    with (
        patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=[]),
        patch("service.stats_service.users_repo.get_usernames", return_value=[]),
        patch("service.stats_service.selected_repo.get_selected_slugs", return_value=[]),
    ):
        response = client.get("/stats")
    assert response.status_code == 200


def test_list_user_stats_returns_list():
    with patch("service.stats_service.get_all_user_stats", return_value=FAKE_STATS):
        response = client.get("/stats")
    data = response.json()
    assert len(data) == 2
    assert data[0]["username"] == "bjoubs"
    assert data[0]["movies_watched"] == 50
    assert data[0]["average_rating"] == 3.75
    assert data[1]["username"] == "kingkrab"


def test_club_stats_returns_200():
    with patch("service.stats_service.get_club_stats", return_value=FAKE_CLUB_STATS):
        response = client.get("/stats/club")
    assert response.status_code == 200


def test_club_stats_returns_correct_shape():
    with patch("service.stats_service.get_club_stats", return_value=FAKE_CLUB_STATS):
        response = client.get("/stats/club")
    data = response.json()
    assert data["total_movies"] == 10
    assert data["highest_rated"]["title"] == "The Substance"
    assert data["most_divisive"]["slug"] == "dune-part-two"
