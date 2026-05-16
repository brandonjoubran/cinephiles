"""Helpers for Google Sheets integration tests (TEST-* tabs in dev)."""
import time

import gspread
from infrastructure.sheets_client import get_worksheet
from infrastructure.cache import cache

IT_MOVIE_SLUG = "it-integration-movie"

MEETINGS_HEADERS = [
    "DATE",
    "MOVIE_NAME",
    "MOVIE_SLUG",
    "START_TIME",
    "END_TIME",
    "PARTICIPANTS",
    "ROTW",
]

MOVIES_HEADERS = [
    "TITLE",
    "SLUG",
    "URL",
    "ADDED_BY",
    "DATE_ADDED",
    "POSTER",
    "STATUS",
    "NOMINATED_BY",
    "VOTED_BY",
    "WATCHED_DATE",
]

USERS_HEADERS = ["USERNAME", "DATE_JOINED"]

NOMINATION_LOG_HEADERS = ["SLUG", "NOMINATED_BY", "VOTED_BY", "DATE_NOMINATED"]

FILM_LOG_HEADERS = [
    "USERNAME",
    "SLUG",
    "TITLE",
    "RATING",
    "HAS_REVIEW",
    "WORD_COUNT",
    "REVIEW_LINK",
    "UPDATED_AT",
]


def open_tab(logical_name: str):
    """Open a worksheet using the same tab() rules as repositories."""
    return get_worksheet(logical_name)


def assert_headers(sheet, expected: list[str], forbidden: list[str] | None = None):
    """Required columns must exist; forbidden columns must not (order does not matter)."""
    header = sheet.row_values(1)
    while header and not str(header[-1]).strip():
        header = header[:-1]

    forbidden = forbidden or []
    unexpected = [col for col in forbidden if col in header]
    missing = [col for col in expected if col not in header]

    problems = []
    if unexpected:
        problems.append(f"forbidden column(s) present: {unexpected}")
    if missing:
        problems.append(f"missing column(s) {missing}")

    assert not problems, (
        f"{sheet.title}: " + "; ".join(problems) + f". Header row is: {header}"
    )


def _with_retry(action, attempts: int = 4, base_delay: float = 2.0):
    for attempt in range(attempts):
        try:
            return action()
        except gspread.exceptions.APIError as exc:
            if attempt == attempts - 1 or exc.response.status_code != 429:
                raise
            time.sleep(base_delay * (attempt + 1))


def delete_rows_where(sheet, column: str, value: str):
    """Delete every data row where `column` equals `value` (bottom-up)."""
    def _run():
        rows = sheet.get_all_records()
        row_indices = [
            i + 2
            for i, row in enumerate(rows)
            if row.get(column) == value
        ]
        for row_index in reversed(row_indices):
            sheet.delete_rows(row_index)
        if row_indices:
            cache.clear()

    _with_retry(_run)


def cleanup_integration_movie(slug: str = IT_MOVIE_SLUG):
    delete_rows_where(open_tab("Meetings"), "MOVIE_SLUG", slug)
    delete_rows_where(open_tab("NominationLog"), "SLUG", slug)
    delete_rows_where(open_tab("Movies"), "SLUG", slug)
