from unittest.mock import patch
from models.user import User
import service.users_service as users_service

FAKE_USERS = [
    User(username="bjoubs", join_date="2024-01-01"),
    User(username="kingkrab", join_date="2024-02-15"),
]


def test_get_users_delegates_to_repo():
    with patch("service.users_service.users_repo.get_users", return_value=FAKE_USERS):
        result = users_service.get_users()
    assert result == FAKE_USERS


def test_get_usernames_delegates_to_repo():
    with patch("service.users_service.users_repo.get_usernames", return_value=["bjoubs", "kingkrab"]):
        result = users_service.get_usernames()
    assert result == ["bjoubs", "kingkrab"]


def test_get_join_dates_delegates_to_repo():
    expected = {"bjoubs": "2024-01-01", "kingkrab": "2024-02-15"}
    with patch("service.users_service.users_repo.get_join_dates", return_value=expected):
        result = users_service.get_join_dates()
    assert result == expected


def test_add_user_delegates_to_repo():
    user = User(username="newuser", join_date="2025-01-01")
    with patch("service.users_service.users_repo.add_user") as mock_add:
        users_service.add_user(user)
    mock_add.assert_called_once_with(user)
