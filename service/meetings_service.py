from fastapi import HTTPException
import repository.meetings_repository as meetings_repo
from models.meeting import Meeting


def get_all_meetings() -> list[Meeting]:
    return meetings_repo.get_all_meetings()


def add_meeting(meeting: Meeting):
    meetings_repo.add_meeting(meeting)


def update_meeting(movie_slug: str, **fields):
    meetings = meetings_repo.get_all_meetings()
    exists = any(m.movie_slug == movie_slug for m in meetings)
    if not exists:
        raise HTTPException(status_code=404, detail=f"Meeting for '{movie_slug}' not found")
    meetings_repo.update_meeting(movie_slug, **fields)


def delete_meeting(movie_slug: str):
    meetings = meetings_repo.get_all_meetings()
    exists = any(m.movie_slug == movie_slug for m in meetings)
    if not exists:
        raise HTTPException(status_code=404, detail=f"Meeting for '{movie_slug}' not found")
    meetings_repo.delete_meeting(movie_slug)
