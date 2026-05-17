"""
Repository for the Selected sheet (club films after complete).

Expected headers: TITLE, SLUG, URL, ADDED_BY, DATE_ADDED, POSTER,
                  NOMINATED_BY, VOTED_BY, WATCHED_DATE (any order).

Rows are appended when a selected movie is completed.
"""
from datetime import date

from infrastructure.dates import parse_date
from infrastructure.sheets_client import get_worksheet
from infrastructure.sheet_rows import append_row_by_headers
from infrastructure.cache import cache
from models.movie import Movie
from models.selected_film import SelectedFilm


def _row_to_model(row: dict) -> SelectedFilm:
    return SelectedFilm(
        title=row["TITLE"],
        slug=row["SLUG"],
        url=row["URL"],
        added_by=row["ADDED_BY"],
        date_added=row["DATE_ADDED"],
        poster=row.get("POSTER", ""),
        nominated_by=row.get("NOMINATED_BY", ""),
        voted_by=row.get("VOTED_BY", ""),
        watched_date=row.get("WATCHED_DATE", ""),
    )


def get_all_selected() -> list[SelectedFilm]:
    cached = cache.get("selected")
    if cached is not None:
        return cached

    rows = get_worksheet("Selected").get_all_records()
    films = [_row_to_model(row) for row in rows]
    cache.set("selected", films)
    return films


def get_selected_slugs() -> list[str]:
    """Club watch history, oldest to newest (for streaks)."""
    films = list(get_all_selected())
    films.sort(key=lambda film: parse_date(film.watched_date) or date.min)
    return [film.slug for film in films]


def add_selected(movie: Movie, watched_date: str) -> None:
    """Append a completed club film to the Selected sheet."""
    cache.clear()
    sheet = get_worksheet("Selected")
    append_row_by_headers(sheet, {
        "title": movie.title,
        "slug": movie.slug,
        "url": movie.url,
        "added_by": movie.added_by,
        "date_added": movie.date_added,
        "poster": movie.poster,
        "nominated_by": movie.nominated_by,
        "voted_by": movie.voted_by,
        "watched_date": watched_date,
    })
