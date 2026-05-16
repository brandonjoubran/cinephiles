from infrastructure.sheets_client import get_worksheet
from infrastructure.sheet_rows import append_row_by_headers
from infrastructure.cache import cache
from models.user import User


def get_users():
    cached = cache.get("users")
    if cached is not None:
        return cached

    rows = get_worksheet("Users").get_all_records()
    users = [User(username=row["USERNAME"], join_date=row["DATE_JOINED"]) for row in rows]
    cache.set("users", users)
    return users


def get_usernames():
    return [user.username for user in get_users()]


def get_join_dates():
    return {user.username: user.join_date for user in get_users()}


def add_user(user: User):
    cache.clear()
    sheet = get_worksheet("Users")
    append_row_by_headers(sheet, {
        "username": user.username,
        "date_joined": user.join_date,
    })