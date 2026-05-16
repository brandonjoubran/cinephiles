"""
Record club member watches in FilmLog after a movie is completed.

For each member we read their Letterboxd RSS and save a FilmLog row when they
watched the film during this cycle (after the last completion, before this one).
"""
from datetime import date

import repository.film_log_repository as film_log_repo
import repository.movies_repository as movies_repo
import repository.users_repository as users_repo
from infrastructure.dates import is_in_cycle
from infrastructure.letterboxd_rss import LetterboxdFilm, fetch_user_films
from models.film_log import FilmLog


def record_club_watches_after_complete(movie_slug: str, completed_on: date | None = None) -> int:
    """Pull Letterboxd RSS for each member and save watches that count for this cycle."""
    cycle_end = completed_on or date.today()
    cycle_start = movies_repo.get_latest_watched_date(exclude_slug=movie_slug)
    saved = 0

    for username in users_repo.get_usernames():
        if _save_member_watch_if_in_cycle(username, movie_slug, cycle_start, cycle_end):
            saved += 1

    return saved


def _save_member_watch_if_in_cycle(
    username: str,
    movie_slug: str,
    cycle_start: date | None,
    cycle_end: date,
) -> bool:
    """Save FilmLog when this member watched the film during the current cycle."""
    films = fetch_user_films(username, slugs=[movie_slug])
    film = films.get(movie_slug)
    if film is None:
        return False

    if not is_in_cycle(film.watched_date, cycle_start, cycle_end):
        return False

    film_log_repo.save_film_log(_to_film_log(username, film, cycle_end))
    return True


def _to_film_log(username: str, film: LetterboxdFilm, synced_on: date) -> FilmLog:
    """Build a FilmLog row from a Letterboxd RSS entry."""
    return FilmLog(
        username=username,
        slug=film.slug,
        title=film.title,
        rating=film.rating if film.rating is not None else 0.0,
        has_review=film.has_review,
        word_count=film.word_count,
        review_link=film.review_link,
        updated_at=synced_on.isoformat(),
    )
