"""JSON payloads for the React UI (same shape as the old Jinja templates)."""
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

import repository.selected_repository as selected_repo
import service.leaderboard_service as leaderboard_service
import service.letterboxd_service as letterboxd_service
import service.meetings_service as meetings_service
import service.stats_page_service as stats_page_service
import service.users_service as users_service
import service.watchlist_page_service as watchlist_page_service
from models.meeting import Meeting

router = APIRouter(prefix="/view", tags=["view"])


def _meeting_sort_date(meeting: dict) -> datetime:
    """DATE is stored as MM/DD/YYYY. Sorting that string groups meetings by month."""
    raw = str(meeting.get("DATE") or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return datetime.min


def _parse_time(value: str):
    try:
        return datetime.strptime(value, "%H:%M")
    except Exception:
        return None


def _meeting_duration(start: str, end: str) -> str:
    start_t = _parse_time(start)
    end_t = _parse_time(end)
    if not start_t or not end_t:
        return "—"
    duration = end_t - start_t
    total_minutes = int(duration.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0:
        if minutes > 0:
            return f"{hours} hr {minutes} min"
        return f"{hours} hr"
    return f"{minutes} min"


@router.get("/stats")
def stats_page():
    return stats_page_service.build_stats_page_context()


@router.post("/stats/refresh/{username}")
def refresh_user_stats(username: str):
    saved = letterboxd_service.refresh_user_film_logs(username)
    return {"username": username, "films_updated": saved}


@router.get("/watchlist")
def watchlist_page():
    return {
        "movies": watchlist_page_service.get_watchlist_movies(),
        "usernames": users_service.get_usernames(),
    }


@router.get("/meetings")
def meetings_page():
    meetings_list = meetings_service.get_all_meetings()
    rows = [
        {
            "DATE": m.date,
            "MOVIE_NAME": m.movie_name,
            "MOVIE_SLUG": m.movie_slug,
            "START_TIME": m.start_time,
            "END_TIME": m.end_time,
            "PARTICIPANTS": ", ".join(m.participants) if m.participants else "",
            "DURATION": _meeting_duration(m.start_time, m.end_time),
            "ROTW": ", ".join(m.rotw) if m.rotw else "",
        }
        for m in meetings_list
    ]
    rows.sort(key=_meeting_sort_date, reverse=True)
    return {
        "meetings": rows,
        "selected_movies": [
            {"TITLE": film.title, "SLUG": film.slug}
            for film in selected_repo.get_all_selected()
        ],
        "usernames": users_service.get_usernames(),
    }


class AddMeetingBody(BaseModel):
    movie_slug: str
    date: str
    start_time: str
    end_time: str
    participants: str = ""


@router.post("/meetings")
def add_meeting_from_ui(body: AddMeetingBody):
    date_obj = datetime.strptime(body.date, "%Y-%m-%d")
    date_str = date_obj.strftime("%m/%d/%Y")
    film = next((f for f in selected_repo.get_all_selected() if f.slug == body.movie_slug), None)
    movie_name = film.title if film else body.movie_slug
    participant_list = [p.strip() for p in body.participants.split(",") if p.strip()]
    meetings_service.add_meeting(Meeting(
        date=date_str,
        movie_name=movie_name,
        movie_slug=body.movie_slug,
        start_time=body.start_time,
        end_time=body.end_time,
        participants=participant_list,
    ))
    return {"message": "Meeting added"}


@router.get("/leaderboard")
def leaderboard_page():
    return {"leaderboard": leaderboard_service.get_leaderboard()}
