from infrastructure.sheets_client import get_worksheet
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
        )
        for row in rows
    ]
    cache.set("meetings", meetings)
    return meetings


def add_meeting(meeting: Meeting):
    cache.clear()
    get_worksheet("Meetings").append_row([
        meeting.date,
        meeting.movie_name,
        meeting.movie_slug,
        meeting.start_time,
        meeting.end_time,
        ", ".join(meeting.participants),
    ])


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
                    sheet.update_cell(row_index, headers.index(col_name) + 1, value)
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
