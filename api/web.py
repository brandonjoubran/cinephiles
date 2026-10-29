"""
HTML UI routes — same URLs and templates as the old Flask app, backed by V2 services.
"""
from datetime import datetime

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import repository.selected_repository as selected_repo
import service.leaderboard_service as leaderboard_service
import service.meetings_service as meetings_service
import service.movies_service as movies_service
import service.nominators_service as nominators_service
import service.stats_page_service as stats_page_service
import service.watchlist_page_service as watchlist_page_service
import service.letterboxd_service as letterboxd_service
import service.users_service as users_service
from models.meeting import Meeting

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="templates")


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


def _meeting_to_row(meeting) -> dict:
    return {
        "DATE": meeting.date,
        "MOVIE_NAME": meeting.movie_name,
        "MOVIE_SLUG": meeting.movie_slug,
        "START_TIME": meeting.start_time,
        "END_TIME": meeting.end_time,
        "PARTICIPANTS": ", ".join(meeting.participants) if meeting.participants else "",
        "DURATION": _meeting_duration(meeting.start_time, meeting.end_time),
    }


def _selected_movie_options() -> list[dict]:
    return [
        {"TITLE": film.title, "SLUG": film.slug}
        for film in selected_repo.get_all_selected()
    ]


@router.get("/", response_class=HTMLResponse, name="index")
def index(request: Request):
    ctx = stats_page_service.build_stats_page_context()
    return templates.TemplateResponse(request, "index.html", {"request": request, **ctx})


@router.post("/refresh/{username}", name="refresh_user")
def refresh_user(username: str):
    letterboxd_service.refresh_user_film_logs(username)
    return RedirectResponse(url="/", status_code=303)


@router.get("/watchlist", response_class=HTMLResponse, name="watchlist")
def watchlist(request: Request):
    return templates.TemplateResponse(
        request,
        "watchlist.html",
        {
            "request": request,
            "movies": watchlist_page_service.get_watchlist_movies(),
            "usernames": users_service.get_usernames(),
        },
    )


@router.post("/add-movie", name="add_movie")
def add_movie(url: str = Form(...), username: str = Form(...)):
    movies_service.add_movie_from_letterboxd_link(url, username)
    return RedirectResponse(url="/watchlist", status_code=303)


@router.post("/delete_movie", name="delete_movie")
def delete_movie(slug: str = Form(...)):
    movies_service.delete_movie(slug)
    return RedirectResponse(url="/watchlist", status_code=303)


@router.post("/nominate", name="nominate_movie")
def nominate_movie(slug: str = Form(...), username: str = Form(...)):
    from models.movie import MovieStatus

    movie = movies_service.get_movie_by_slug(slug)
    if movie.status == MovieStatus.BACKLOG:
        movies_service.toggle_nomination(slug, username)
    return RedirectResponse(url="/watchlist", status_code=303)


@router.post("/remove_nomination", name="remove_nomination")
def remove_nomination(slug: str = Form(...)):
    from models.movie import MovieStatus

    movie = movies_service.get_movie_by_slug(slug)
    if movie.status == MovieStatus.NOMINATED:
        movies_service.toggle_nomination(slug, movie.nominated_by or "x")
    return RedirectResponse(url="/watchlist", status_code=303)


@router.post("/vote_movie", name="vote_movie")
def vote_movie(slug: str = Form(...), username: str = Form(...)):
    movies_service.toggle_vote(slug, username)
    return RedirectResponse(url="/watchlist", status_code=303)


@router.post("/winning_movie", name="winning_movie")
def winning_movie(slug: str = Form(...)):
    movies_service.toggle_selection(slug)
    return RedirectResponse(url="/watchlist", status_code=303)


@router.post("/mark-watched/{movie_slug}", name="mark_watched")
async def mark_watched(movie_slug: str, request: Request):
    from models.movie import MovieStatus

    form = await request.form()
    slug = form.get("slug") or movie_slug
    rotw = form.getlist("review_of_week[]")
    movie = movies_service.get_movie_by_slug(slug)
    if movie.status == MovieStatus.SELECTED:
        movies_service.complete_movie(slug, rotw=rotw)
    else:
        movies_service.mark_watched(slug)
    return RedirectResponse(url="/watchlist", status_code=303)


@router.post("/mark-unwatched/{movie_slug}", name="mark_unwatched")
def mark_unwatched(movie_slug: str):
    movies_service.mark_unwatched(movie_slug)
    return RedirectResponse(url="/watchlist", status_code=303)


@router.get("/generate-voters", name="generate_voters")
def generate_voters():
    """JSON for watchlist dice button (old response shape: { voters: [...] })."""
    try:
        _, nominators = nominators_service.generate_nominators()
        return JSONResponse({"voters": nominators})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@router.get("/meetings", response_class=HTMLResponse, name="meetings")
def meetings(request: Request):
    meetings_list = meetings_service.get_all_meetings()
    rows = [_meeting_to_row(m) for m in meetings_list]
    rows.sort(key=lambda m: m.get("DATE", ""))
    return templates.TemplateResponse(
        request,
        "meetings.html",
        {
            "request": request,
            "meetings": rows,
            "selected_movies": _selected_movie_options(),
            "usernames": users_service.get_usernames(),
            "now": datetime.now(),
        },
    )


@router.post("/add_meeting", name="add_meeting")
def add_meeting(
    movie_slug: str = Form(...),
    date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    participants: str = Form(""),
):
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    date_str = date_obj.strftime("%m/%d/%Y")
    film = next((f for f in selected_repo.get_all_selected() if f.slug == movie_slug), None)
    movie_name = film.title if film else movie_slug
    participant_list = [p.strip() for p in participants.split(",") if p.strip()]
    meetings_service.add_meeting(Meeting(
        date=date_str,
        movie_name=movie_name,
        movie_slug=movie_slug,
        start_time=start_time,
        end_time=end_time,
        participants=participant_list,
    ))
    return RedirectResponse(url="/meetings", status_code=303)


@router.get("/leaderboard", response_class=HTMLResponse, name="leaderboard")
def leaderboard(request: Request):
    return templates.TemplateResponse(
        request,
        "leaderboard.html",
        {
            "request": request,
            "leaderboard": leaderboard_service.get_leaderboard(),
        },
    )
