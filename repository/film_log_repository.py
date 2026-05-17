"""
FilmLog sheet: one row per club member per film they watched during a cycle.

Expected headers: USERNAME, SLUG, TITLE, RATING, HAS_REVIEW, WORD_COUNT,
                  REVIEW_LINK, UPDATED_AT (any order).
"""
from infrastructure.sheets_client import get_worksheet
from infrastructure.cache import cache
from infrastructure.sheet_rows import append_row_by_headers, update_row_by_headers
from models.film_log import FilmLog


def get_all_film_logs() -> list[FilmLog]:
    """Return every FilmLog row (cached until the sheet changes)."""
    cached = cache.get("film_logs")
    if cached is not None:
        return cached

    rows = get_worksheet("FilmLog").get_all_records()
    logs = [_row_to_model(row) for row in rows]
    cache.set("film_logs", logs)
    return logs


def get_film_logs_for_user(username: str) -> list[FilmLog]:
    """Return FilmLog rows for a single club member."""
    return [log for log in get_all_film_logs() if log.username == username]


def get_usernames_for_slug(slug: str) -> list[str]:
    """Return usernames that have a FilmLog row for this film."""
    slug = slug.strip().lower()
    seen = set()
    usernames = []
    for log in get_all_film_logs():
        if log.slug.strip().lower() != slug:
            continue
        key = log.username.strip().lower()
        if key and key not in seen:
            seen.add(key)
            usernames.append(log.username.strip())
    return usernames


def save_film_log(film_log: FilmLog) -> None:
    """Insert or update the row for this username + slug pair."""
    sheet = get_worksheet("FilmLog")
    rows = sheet.get_all_records()
    row_fields = _model_to_row(film_log)

    for index, row in enumerate(rows):
        if row.get("USERNAME") == film_log.username and row.get("SLUG") == film_log.slug:
            update_row_by_headers(sheet, index + 2, row_fields)
            cache.clear()
            return

    append_row_by_headers(sheet, row_fields)
    cache.clear()


def _row_to_model(row: dict) -> FilmLog:
    return FilmLog(
        username=row["USERNAME"],
        slug=row["SLUG"],
        title=row["TITLE"],
        rating=row["RATING"],
        has_review=row["HAS_REVIEW"],
        word_count=row["WORD_COUNT"],
        review_link=row["REVIEW_LINK"],
        updated_at=row["UPDATED_AT"],
    )


def _model_to_row(film_log: FilmLog) -> dict[str, object]:
    """Convert a FilmLog to lowercase keys used by sheet_rows helpers."""
    return {
        "username": film_log.username,
        "slug": film_log.slug,
        "title": film_log.title,
        "rating": film_log.rating if film_log.rating else "",
        "has_review": "TRUE" if film_log.has_review else "FALSE",
        "word_count": film_log.word_count,
        "review_link": film_log.review_link,
        "updated_at": film_log.updated_at,
    }
