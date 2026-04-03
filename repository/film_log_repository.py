from infrastructure.sheets_client import get_worksheet
from infrastructure.cache import cache
from models.film_log import FilmLog


def get_all_film_logs() -> list[FilmLog]:
    cached = cache.get("film_logs")
    if cached is not None:
        return cached

    rows = get_worksheet("FilmLog").get_all_records()
    logs = [
        FilmLog(
            username=row["USERNAME"],
            slug=row["SLUG"],
            title=row["TITLE"],
            rating=row["RATING"],
            has_review=row["HAS_REVIEW"],
            word_count=row["WORD_COUNT"],
            review_link=row["REVIEW_LINK"],
            updated_at=row["UPDATED_AT"],
        )
        for row in rows
    ]
    cache.set("film_logs", logs)
    return logs


def get_film_logs_for_user(username: str) -> list[FilmLog]:
    return [r for r in get_all_film_logs() if r.username == username]
