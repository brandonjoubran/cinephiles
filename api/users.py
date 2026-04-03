from fastapi import APIRouter
import service.users_service as users_service
from models.user import User

router = APIRouter()

@router.get("/users")
def list_users() -> list[User]:
    return users_service.get_users()


@router.get("/users/usernames")
def list_usernames():
    return users_service.get_usernames()


@router.get("/users/join-dates")
def list_join_dates():
    return users_service.get_join_dates()


@router.post("/users/add-user")
def add_user(user: User):
    return users_service.add_user(user)