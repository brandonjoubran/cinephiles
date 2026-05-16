"""
Repository for the Meetings sheet.

Expected headers: DATE, MOVIE_NAME, MOVIE_SLUG, START_TIME, END_TIME,
                  PARTICIPANTS, ROTW (any order).
"""
from infrastructure.sheets_client import get_worksheet
from infrastructure.sheet_rows import append_row_by_headers, serialize_field_value
from infrastructure.cache import cache
from models.meeting import Meeting


def get_all_meetings() -> list[Meeting]:
    cached = cache.get("meetings")
    if cached is not None:
        return cached

    rows = get_worksheet("Meetings").get_all_records()
    meetings = [
        Meeting(
            date=row["DATE"],
            movie_name=row["MOVIE_NAME"],
            movie_slug=row["MOVIE_SLUG"],
            start_time=row["START_TIME"],
            end_time=row["END_TIME"],
            participants=row.get("PARTICIPANTS", ""),
            rotw=row.get("ROTW", ""),
        )
        for row in rows
    ]
    cache.set("meetings", meetings)
    return meetings


def get_rotw_winners() -> list[str]:
    """All ROTW recipients across meetings (one entry per win, for stats)."""
    winners = []
    for meeting in get_all_meetings():
        for name in meeting.rotw:
            winners.append(name)
    return winners


def add_meeting(meeting: Meeting):
    cache.clear()
    sheet = get_worksheet("Meetings")
    append_row_by_headers(sheet, {
        "date": meeting.date,
        "movie_name": meeting.movie_name,
        "movie_slug": meeting.movie_slug,
        "start_time": meeting.start_time,
        "end_time": meeting.end_time,
        "participants": meeting.participants,
        "rotw": meeting.rotw,
    })


def update_meeting(movie_slug: str, **fields):
    """Find the meeting matching `movie_slug` and update one or more columns."""
    sheet = get_worksheet("Meetings")
    rows = sheet.get_all_records()
    headers = sheet.row_values(1)

    for i, row in enumerate(rows):
        if row["MOVIE_SLUG"] == movie_slug:
            row_index = i + 2
            for field, value in fields.items():
                col_name = field.upper()
                if col_name in headers:
                    sheet.update_cell(
                        row_index,
                        headers.index(col_name) + 1,
                        serialize_field_value(value),
                    )
            cache.clear()
            return


def delete_meeting(movie_slug: str):
    """Find the meeting matching `movie_slug` and delete its row."""
    sheet = get_worksheet("Meetings")
    rows = sheet.get_all_records()

    for i, row in enumerate(rows):
        if row["MOVIE_SLUG"] == movie_slug:
            sheet.delete_rows(i + 2)
            cache.clear()
            return
