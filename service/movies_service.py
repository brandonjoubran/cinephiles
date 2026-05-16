from datetime import date
from fastapi import HTTPException
import repository.movies_repository as movies_repo
import repository.nomination_log_repository as nomination_log_repo
from models.movie import Movie, MovieStatus
from models.nomination_log import NominationLog
from service.letterboxd_service import record_club_watches_after_complete


def get_all_movies() -> list[Movie]:
    return movies_repo.get_all_movies()


def get_movies_by_status(status: MovieStatus) -> list[Movie]:
    return movies_repo.get_movies_by_status(status)


def get_movie_by_slug(slug: str) -> Movie:
    movie = movies_repo.get_movie_by_slug(slug)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie '{slug}' not found")
    return movie


def add_movie(title: str, slug: str, url: str, added_by: str, poster: str) -> Movie:
    """Add a new movie to the watchlist. Enforces uniqueness and sets defaults."""
    existing = movies_repo.get_movie_by_slug(slug)
    if existing:
        raise HTTPException(status_code=409, detail=f"Movie '{slug}' already exists")

    movie = Movie(
        title=title,
        slug=slug,
        url=url,
        added_by=added_by,
        date_added=date.today().strftime("%m/%d/%Y"),
        poster=poster,
        status=MovieStatus.BACKLOG,
        nominated_by="",
        voted_by=[],
        watched_date="",
    )
    movies_repo.add_movie(movie)
    return movie


def toggle_nomination(slug: str, username: str) -> Movie:
    """Toggle nomination. Backlog -> nominated, nominated -> backlog."""
    movie = get_movie_by_slug(slug)

    if movie.status == MovieStatus.NOMINATED:
        movies_repo.update_movie_fields(slug, status=MovieStatus.BACKLOG.value, nominated_by="", voted_by="")
        return get_movie_by_slug(slug)

    if movie.status != MovieStatus.BACKLOG:
        raise HTTPException(status_code=400, detail=f"Movie must be in backlog or nominated to toggle (current: {movie.status.value})")

    selected = movies_repo.get_movies_by_status(MovieStatus.SELECTED)
    if selected:
        raise HTTPException(status_code=400, detail="Cannot nominate while a movie is selected for watching")

    movies_repo.update_movie_fields(slug, status=MovieStatus.NOMINATED.value, nominated_by=username)

    nomination_log_repo.add_nomination(NominationLog(
        slug=slug,
        nominated_by=username,
        voted_by=[],
        date_nominated=date.today().strftime("%m/%d/%Y"),
    ))

    return get_movie_by_slug(slug)


def toggle_vote(slug: str, username: str) -> Movie:
    movie = get_movie_by_slug(slug)
    if movie.status != MovieStatus.NOMINATED:
        raise HTTPException(status_code=400, detail=f"Movie must be nominated to vote (current: {movie.status.value})")

    voters = list(movie.voted_by)
    if username in voters:
        voters.remove(username)
    else:
        voters.append(username)

    movies_repo.update_movie_fields(slug, voted_by=", ".join(voters))
    return get_movie_by_slug(slug)


def toggle_selection(slug: str) -> Movie:
    """Toggle selection. Nominated -> selected, selected -> nominated."""
    movie = get_movie_by_slug(slug)

    if movie.status == MovieStatus.SELECTED:
        movies_repo.update_movie_fields(slug, status=MovieStatus.NOMINATED.value)
        return get_movie_by_slug(slug)

    if movie.status != MovieStatus.NOMINATED:
        raise HTTPException(status_code=400, detail=f"Movie must be nominated or selected to toggle (current: {movie.status.value})")

    movies_repo.update_movie_fields(slug, status=MovieStatus.SELECTED.value)
    return get_movie_by_slug(slug)


def complete_movie(slug: str) -> Movie:
    """Finish the current club film.

    - Marks the selected movie as watched.
    - Logs nominations (completed film + any still-nominated films) to NominationLog.
    - Resets other nominated movies to backlog.
    - Records member watches from Letterboxd RSS into FilmLog.
    """
    movie = get_movie_by_slug(slug)
    if movie.status != MovieStatus.SELECTED:
        raise HTTPException(status_code=400, detail=f"Movie must be selected to complete (current: {movie.status.value})")

    today = date.today().strftime("%m/%d/%Y")

    # Snapshot nomination into NominationLog before resetting
    if movie.nominated_by:
        nomination_log_repo.add_nomination(NominationLog(
            slug=slug,
            nominated_by=movie.nominated_by,
            voted_by=movie.voted_by,
            date_nominated=today,
        ))

    # Mark as watched
    movies_repo.update_movie_fields(
        slug,
        status=MovieStatus.WATCHED.value,
        watched_date=today,
    )

    # Log and reset other nominated movies back to backlog
    nominated = movies_repo.get_movies_by_status(MovieStatus.NOMINATED)
    for nominated_movie in nominated:
        if nominated_movie.nominated_by:
            nomination_log_repo.add_nomination(NominationLog(
                slug=nominated_movie.slug,
                nominated_by=nominated_movie.nominated_by,
                voted_by=nominated_movie.voted_by,
                date_nominated=today,
            ))
        movies_repo.update_movie_fields(nominated_movie.slug, status=MovieStatus.BACKLOG.value, nominated_by="", voted_by="")

    record_club_watches_after_complete(slug, completed_on=date.today())

    return get_movie_by_slug(slug)


def delete_movie(slug: str):
    """Delete a movie. Only backlog movies can be deleted."""
    movie = get_movie_by_slug(slug)
    if movie.status != MovieStatus.BACKLOG:
        raise HTTPException(status_code=400, detail=f"Only backlog movies can be deleted (current: {movie.status.value})")
    movies_repo.delete_movie(slug)
