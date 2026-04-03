from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from models.user import User

client = TestClient(app)

FAKE_USERS = [
    User(username="bjoubs", join_date="2024-01-01"),
    User(username="kingkrab", join_date="2024-02-15"),
]


def test_list_users_returns_200():
    with patch("service.users_service.users_repo.get_users", return_value=FAKE_USERS):
        response = client.get("/users")
    assert response.status_code == 200


def test_list_users_returns_user_list():
    with patch("service.users_service.users_repo.get_users", return_value=FAKE_USERS):
        response = client.get("/users")
    data = response.json()
    assert len(data) == 2
    assert data[0]["username"] == "bjoubs"
    assert data[0]["join_date"] == "2024-01-01"


def test_list_usernames_returns_200():
    with patch("service.users_service.users_repo.get_usernames", return_value=["bjoubs", "kingkrab"]):
        response = client.get("/users/usernames")
    assert response.status_code == 200
    assert response.json() == ["bjoubs", "kingkrab"]


def test_list_join_dates_returns_200():
    expected = {"bjoubs": "2024-01-01", "kingkrab": "2024-02-15"}
    with patch("service.users_service.users_repo.get_join_dates", return_value=expected):
        response = client.get("/users/join-dates")
    assert response.status_code == 200
    assert response.json() == expected


def test_add_user_returns_200():
    with patch("service.users_service.users_repo.add_user") as mock_add:
        response = client.post("/users/add-user", json={"username": "newuser", "join_date": "2025-01-01"})
    assert response.status_code == 200
    mock_add.assert_called_once_with(User(username="newuser", join_date="2025-01-01"))
