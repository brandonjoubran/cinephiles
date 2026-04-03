from unittest.mock import MagicMock, patch
from models.user import User
from repository.users_repository import get_users, get_usernames, get_join_dates, add_user

FAKE_ROWS = [
    {"USERNAME": "bjoubs", "DATE_JOINED": "2024-01-01"},
    {"USERNAME": "kingkrab", "DATE_JOINED": "2024-02-15"},
]

FAKE_USERS = [
    User(username="bjoubs", join_date="2024-01-01"),
    User(username="kingkrab", join_date="2024-02-15"),
]


def fake_worksheet(records):
    sheet = MagicMock()
    sheet.get_all_records.return_value = records
    return sheet


def test_get_users_returns_user_models():
    with patch("repository.users_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_users()
    assert result == FAKE_USERS


def test_get_users_maps_fields_correctly():
    with patch("repository.users_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_users()
    assert result[0].username == "bjoubs"
    assert result[0].join_date == "2024-01-01"


def test_get_users_empty_sheet():
    with patch("repository.users_repository.get_worksheet", return_value=fake_worksheet([])):
        assert get_users() == []


def test_get_usernames():
    with patch("repository.users_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        assert get_usernames() == ["bjoubs", "kingkrab"]


def test_get_join_dates():
    with patch("repository.users_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        assert get_join_dates() == {
            "bjoubs": "2024-01-01",
            "kingkrab": "2024-02-15",
        }


def test_add_user_appends_row():
    sheet = fake_worksheet([])
    user = User(username="newuser", join_date="2025-01-01")
    with patch("repository.users_repository.get_worksheet", return_value=sheet):
        add_user(user)
    sheet.append_row.assert_called_once_with(["newuser", "2025-01-01"])
