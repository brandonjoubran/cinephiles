from infrastructure.sheets_client import get_worksheet
from models.film_log import FilmLog


def get_all_film_logs() -> list[FilmLog]:
    rows = get_worksheet("FilmLog").get_all_records()
    return [
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


def get_film_logs_for_user(username: str) -> list[FilmLog]:
    return [r for r in get_all_film_logs() if r.username == username]
