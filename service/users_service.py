import repository.users_repository as users_repo
from models.user import User


def get_users():
    return users_repo.get_users()


def get_usernames():
    return users_repo.get_usernames()


def get_join_dates():
    return users_repo.get_join_dates()

def add_user(user: User):
    return users_repo.add_user(user)