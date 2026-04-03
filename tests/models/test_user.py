import pytest
from pydantic import ValidationError
from models.user import User


# ── Construction ──────────────────────────────────────────────────────────────

def test_user_creation():
    user = User(username="bjoubs", join_date="02/11/2025")
    assert user.username == "bjoubs"
    assert user.join_date == "02/11/2025"


def test_user_missing_username_raises():
    with pytest.raises(ValidationError):
        User(join_date="02/11/2025")


def test_user_missing_join_date_raises():
    with pytest.raises(ValidationError):
        User(username="bjoubs")


# ── Username validation ───────────────────────────────────────────────────────

def test_username_empty_string_raises():
    with pytest.raises(ValidationError, match="username cannot be empty"):
        User(username="", join_date="02/11/2025")


def test_username_whitespace_only_raises():
    with pytest.raises(ValidationError, match="username cannot be empty"):
        User(username="   ", join_date="02/11/2025")


def test_username_is_stripped():
    user = User(username="  bjoubs  ", join_date="02/11/2025")
    assert user.username == "bjoubs"


# ── join_date validation ──────────────────────────────────────────────────────

def test_join_date_valid_format():
    user = User(username="bjoubs", join_date="02/11/2025")
    assert user.join_date == "02/11/2025"


def test_join_date_wrong_format_raises():
    with pytest.raises(ValidationError, match="MM/DD/YYYY"):
        User(username="bjoubs", join_date="2025-02-11")


def test_join_date_iso_format_raises():
    with pytest.raises(ValidationError, match="MM/DD/YYYY"):
        User(username="bjoubs", join_date="2025/02/11")


def test_join_date_partial_raises():
    with pytest.raises(ValidationError, match="MM/DD/YYYY"):
        User(username="bjoubs", join_date="02/2025")


def test_join_date_invalid_day_raises():
    with pytest.raises(ValidationError, match="MM/DD/YYYY"):
        User(username="bjoubs", join_date="02/99/2025")


def test_join_date_invalid_month_raises():
    with pytest.raises(ValidationError, match="MM/DD/YYYY"):
        User(username="bjoubs", join_date="13/01/2025")


# ── Serialization ─────────────────────────────────────────────────────────────

def test_user_serializes_to_dict_with_lowercase_keys():
    user = User(username="bjoubs", join_date="02/11/2025")
    assert user.model_dump() == {"username": "bjoubs", "join_date": "02/11/2025"}


def test_user_deserializes_from_dict():
    user = User.model_validate({"username": "bjoubs", "join_date": "02/11/2025"})
    assert user.username == "bjoubs"


def test_user_deserializes_from_json():
    user = User.model_validate_json('{"username": "bjoubs", "join_date": "02/11/2025"}')
    assert user.username == "bjoubs"
    assert user.join_date == "02/11/2025"
