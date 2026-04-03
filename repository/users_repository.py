from infrastructure.sheets_client import get_worksheet
from models.user import User

def get_users():
    rows = get_worksheet("Users").get_all_records()
    return [User(username=row["USERNAME"], join_date=row["DATE_JOINED"]) for row in rows]


def get_usernames():
    return [user.username for user in get_users()]


def get_join_dates():
    return {user.username: user.join_date for user in get_users()}


def add_user(user: User):
    return get_worksheet("Users").append_row([user.username, user.join_date])