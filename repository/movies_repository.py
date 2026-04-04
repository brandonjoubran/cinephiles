"""
Repository for the Movies sheet.

Column order: TITLE | SLUG | URL | ADDED_BY | DATE_ADDED | POSTER |
              STATUS | NOMINATED_BY | VOTED_BY | WATCHED_DATE | ROTW
"""
from infrastructure.sheets_client import get_worksheet
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
            rotw=row.get("ROTW", ""),
        )
        for row in rows
    ]
    cache.set("movies", movies)
    return movies


def get_movies_by_status(status: MovieStatus) -> list[Movie]:
    return [m for m in get_all_movies() if m.status == status]


def get_movie_by_slug(slug: str) -> Movie | None:
    for movie in get_all_movies():
        if movie.slug == slug:
            return movie
    return None


def add_movie(movie: Movie):
    """Append a new row to the Movies sheet. Caller (service layer) is
    responsible for setting defaults and checking uniqueness."""
    cache.clear()
    get_worksheet("Movies").append_row([
        movie.title,
        movie.slug,
        movie.url,
        movie.added_by,
        movie.date_added,
        movie.poster,
        movie.status.value,
        movie.nominated_by,
        ", ".join(movie.voted_by),
        movie.watched_date,
        ", ".join(movie.rotw),
    ])


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
