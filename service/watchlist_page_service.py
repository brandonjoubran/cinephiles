"""Build the combined watchlist card list for the watchlist template (old Flask shape)."""
from __future__ import annotations

from datetime import datetime

import repository.film_log_repository as film_log_repo
import repository.movies_repository as movies_repo
import repository.selected_repository as selected_repo
from infrastructure.dates import parse_date
from models.movie import Movie, MovieStatus
from models.selected_film import SelectedFilm


def _movie_to_row(movie: Movie) -> dict:
    return {
        "TITLE": movie.title,
        "SLUG": movie.slug,
        "URL": movie.url,
        "ADDED_BY": movie.added_by,
        "DATE_ADDED": movie.date_added,
        "POSTER": movie.poster,
        "IS_WATCHED": movie.status == MovieStatus.WATCHED,
        "IS_NOMINATED": movie.status == MovieStatus.NOMINATED,
        "IS_SELECTED": movie.status == MovieStatus.SELECTED,
        "NOMINATED_BY": movie.nominated_by,
        "VOTED_BY": list(movie.voted_by),
        "WATCHED_DATE": movie.watched_date or None,
        "AVG_RATING": None,
    }


def _selected_to_row(film: SelectedFilm, avg_rating: float | None) -> dict:
    return {
        "TITLE": film.title,
        "SLUG": film.slug,
        "URL": film.url,
        "ADDED_BY": film.added_by,
        "DATE_ADDED": film.date_added,
        "POSTER": film.poster,
        "IS_WATCHED": True,
        "IS_NOMINATED": False,
        "IS_SELECTED": False,
        "NOMINATED_BY": film.nominated_by,
        "VOTED_BY": list(film.voted_by),
        "WATCHED_DATE": film.watched_date,
        "AVG_RATING": avg_rating,
        "WATCH_DATE": parse_date(film.watched_date),
    }


def _avg_ratings_by_slug() -> dict[str, float]:
    by_slug: dict[str, list[float]] = {}
    for log in film_log_repo.get_all_film_logs():
        if log.rating and log.rating > 0:
            by_slug.setdefault(log.slug, []).append(log.rating)
    return {
        slug: round(sum(ratings) / len(ratings), 2)
        for slug, ratings in by_slug.items()
        if ratings
    }


def get_watchlist_movies() -> list[dict]:
    """Same ordering as aaa-old/letterboxd.py watchlist(): selected → nominated → backlog → watched history."""
    all_movies = movies_repo.get_all_movies()
    selected_films = selected_repo.get_all_selected()
    selected_slugs = {film.slug for film in selected_films}
    avg_ratings = _avg_ratings_by_slug()

    active = [m for m in all_movies if m.slug not in selected_slugs]

    selected_movie = next((m for m in active if m.status == MovieStatus.SELECTED), None)
    nominated = sorted(
        [m for m in active if m.status == MovieStatus.NOMINATED],
        key=lambda m: m.date_added,
    )
    backlog = sorted(
        [m for m in active if m.status == MovieStatus.BACKLOG],
        key=lambda m: m.date_added,
    )
    watched_on_watchlist = sorted(
        [m for m in active if m.status == MovieStatus.WATCHED],
        key=lambda m: m.date_added,
    )

    watched_rows = sorted(
        [
            _selected_to_row(film, avg_ratings.get(film.slug))
            for film in selected_films
            if film.watched_date
        ],
        key=lambda row: row["WATCH_DATE"] or datetime.min,
    )

    combined: list[dict] = []
    if selected_movie:
        combined.append(_movie_to_row(selected_movie))
    combined.extend(_movie_to_row(m) for m in nominated)
    combined.extend(_movie_to_row(m) for m in backlog)
    combined.extend(_movie_to_row(m) for m in watched_on_watchlist)
    combined.extend(watched_rows)
    return combined
