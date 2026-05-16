from fastapi import APIRouter
from pydantic import BaseModel
import service.meetings_service as meetings_service
from models.meeting import Meeting

router = APIRouter()


class UpdateMeetingRequest(BaseModel):
    date: str | None = None
    movie_name: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    participants: list[str] | None = None
    rotw: list[str] | None = None


@router.get("/meetings")
def list_meetings() -> list[Meeting]:
    return meetings_service.get_all_meetings()


@router.post("/meetings")
def add_meeting(meeting: Meeting):
    meetings_service.add_meeting(meeting)
    return {"message": "Meeting added"}


@router.put("/meetings/{movie_slug}")
def update_meeting(movie_slug: str, body: UpdateMeetingRequest):
    fields = body.model_dump(exclude_none=True)
    if not fields:
        return {"message": "No fields to update"}
    meetings_service.update_meeting(movie_slug, **fields)
    return {"message": "Meeting updated"}


@router.delete("/meetings/{movie_slug}")
def delete_meeting(movie_slug: str):
    meetings_service.delete_meeting(movie_slug)
    return {"message": "Meeting deleted"}
