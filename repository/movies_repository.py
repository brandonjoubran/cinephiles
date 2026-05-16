from datetime import date

"""
Repository for the Movies sheet.

Expected headers: TITLE, SLUG, URL, ADDED_BY, DATE_ADDED, POSTER,
                  STATUS, NOMINATED_BY, VOTED_BY, WATCHED_DATE (any order).
"""
from infrastructure.sheets_client import get_worksheet
from infrastructure.sheet_rows import append_row_by_headers
from infrastructure.cache import cache
from models.movie import Movie, MovieStatus


def get_all_movies() -> list[Movie]:
    cached = cache.get("movies")
    if cached is not None:
        return cached

    rows = get_worksheet("Movies").get_all_records()
    movies = [
        Movie(
            title=row["TITLE"],
            slug=row["SLUG"],
            url=row["URL"],
            added_by=row["ADDED_BY"],
            date_added=row["DATE_ADDED"],
            poster=row["POSTER"],
            status=row["STATUS"],
            nominated_by=row.get("NOMINATED_BY", ""),
            voted_by=row.get("VOTED_BY", ""),
            watched_date=row.get("WATCHED_DATE", ""),
        )
        for row in rows
    ]
    cache.set("movies", movies)
    return movies


def get_movies_by_status(status: MovieStatus) -> list[Movie]:
    return [m for m in get_all_movies() if m.status == status]


def get_latest_watched_date(exclude_slug: str | None = None) -> date | None:
    """Return the most recent ``watched_date`` among watched movies, or None.

    Use ``exclude_slug`` to ignore the film being completed right now.
    """
    from infrastructure.dates import parse_date

    watched_dates = []
    for movie in get_movies_by_status(MovieStatus.WATCHED):
        if exclude_slug and movie.slug == exclude_slug:
            continue
        parsed = parse_date(movie.watched_date)
        if parsed:
            watched_dates.append(parsed)
    return max(watched_dates) if watched_dates else None


def get_movie_by_slug(slug: str) -> Movie | None:
    for movie in get_all_movies():
        if movie.slug == slug:
            return movie
    return None


def add_movie(movie: Movie):
    """Append a new row to the Movies sheet. Caller (service layer) is
    responsible for setting defaults and checking uniqueness."""
    cache.clear()
    sheet = get_worksheet("Movies")
    append_row_by_headers(sheet, {
        "title": movie.title,
        "slug": movie.slug,
        "url": movie.url,
        "added_by": movie.added_by,
        "date_added": movie.date_added,
        "poster": movie.poster,
        "status": movie.status,
        "nominated_by": movie.nominated_by,
        "voted_by": movie.voted_by,
        "watched_date": movie.watched_date,
    })


def update_movie_fields(slug: str, **fields):
    """Find the row matching `slug` and update one or more columns.
    Keys are lowercase field names (e.g. status, voted_by, watched_date)
    that get uppercased to match sheet headers."""
    sheet = get_worksheet("Movies")
    rows = sheet.get_all_records()
    headers = sheet.row_values(1)

    for i, row in enumerate(rows):
        if row["SLUG"] == slug:
            # +2: enumerate is 0-based and row 1 is the header
            row_index = i + 2
            for field, value in fields.items():
                col_name = field.upper()
                if col_name in headers:
                    sheet.update_cell(row_index, headers.index(col_name) + 1, value)
            cache.clear()
            return


def delete_movie(slug: str):
    """Find the row matching `slug` and delete it."""
    sheet = get_worksheet("Movies")
    rows = sheet.get_all_records()

    for i, row in enumerate(rows):
        if row["SLUG"] == slug:
            sheet.delete_rows(i + 2)
            cache.clear()
            return
