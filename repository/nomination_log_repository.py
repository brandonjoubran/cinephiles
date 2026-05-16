from infrastructure.sheets_client import get_worksheet
from infrastructure.sheet_rows import append_row_by_headers
from infrastructure.cache import cache
from models.nomination_log import NominationLog


def get_all_nominations() -> list[NominationLog]:
    cached = cache.get("nomination_logs")
    if cached is not None:
        return cached

    rows = get_worksheet("NominationLog").get_all_records()
    logs = [
        NominationLog(
            slug=row["SLUG"],
            nominated_by=row["NOMINATED_BY"],
            voted_by=row.get("VOTED_BY", ""),
            date_nominated=row["DATE_NOMINATED"],
        )
        for row in rows
    ]
    cache.set("nomination_logs", logs)
    return logs


def add_nomination(nomination: NominationLog):
    cache.clear()
    sheet = get_worksheet("NominationLog")
    append_row_by_headers(sheet, {
        "slug": nomination.slug,
        "nominated_by": nomination.nominated_by,
        "voted_by": nomination.voted_by,
        "date_nominated": nomination.date_nominated,
    })
