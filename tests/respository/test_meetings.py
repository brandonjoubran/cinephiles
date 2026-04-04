from unittest.mock import MagicMock, call, patch
from models.meeting import Meeting
from repository.meetings_repository import get_all_meetings, add_meeting, update_meeting, delete_meeting

FAKE_ROWS = [
    {
        "DATE": "01/15/2025",
        "MOVIE_NAME": "The Substance",
        "MOVIE_SLUG": "the-substance",
        "START_TIME": "19:00",
        "END_TIME": "21:30",
        "PARTICIPANTS": "bjoubs, KingKrab, GeoMoD",
    },
    {
        "DATE": "01/22/2025",
        "MOVIE_NAME": "Anora",
        "MOVIE_SLUG": "anora",
        "START_TIME": "20:00",
        "END_TIME": "22:00",
        "PARTICIPANTS": "bjoubs, KingKrab",
    },
]


def fake_worksheet(records):
    sheet = MagicMock()
    sheet.get_all_records.return_value = records
    return sheet


def test_get_all_meetings_returns_models():
    with patch("repository.meetings_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_all_meetings()
    assert len(result) == 2
    assert all(isinstance(m, Meeting) for m in result)


def test_get_all_meetings_maps_fields():
    with patch("repository.meetings_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_all_meetings()
    assert result[0].movie_slug == "the-substance"
    assert result[0].participants == ["bjoubs", "KingKrab", "GeoMoD"]
    assert result[0].start_time == "19:00"


def test_get_all_meetings_empty_sheet():
    with patch("repository.meetings_repository.get_worksheet", return_value=fake_worksheet([])):
        assert get_all_meetings() == []


def test_add_meeting_appends_row():
    sheet = fake_worksheet([])
    meeting = Meeting(
        date="03/01/2025",
        movie_name="Heat",
        movie_slug="heat-1995",
        start_time="19:00",
        end_time="22:00",
        participants=["bjoubs", "KingKrab"],
    )
    with patch("repository.meetings_repository.get_worksheet", return_value=sheet):
        add_meeting(meeting)
    sheet.append_row.assert_called_once_with([
        "03/01/2025",
        "Heat",
        "heat-1995",
        "19:00",
        "22:00",
        "bjoubs, KingKrab",
    ])


# ── update_meeting ────────────────────────────────────────────────────────────

def test_update_meeting_updates_correct_row():
    sheet = MagicMock()
    sheet.get_all_records.return_value = FAKE_ROWS
    sheet.row_values.return_value = [
        "DATE", "MOVIE_NAME", "MOVIE_SLUG", "START_TIME", "END_TIME", "PARTICIPANTS",
    ]
    with patch("repository.meetings_repository.get_worksheet", return_value=sheet):
        update_meeting("the-substance", start_time="18:30", end_time="21:00")
    calls = sheet.update_cell.call_args_list
    assert call(2, 4, "18:30") in calls
    assert call(2, 5, "21:00") in calls


def test_update_meeting_no_match_does_nothing():
    sheet = MagicMock()
    sheet.get_all_records.return_value = FAKE_ROWS
    sheet.row_values.return_value = [
        "DATE", "MOVIE_NAME", "MOVIE_SLUG", "START_TIME", "END_TIME", "PARTICIPANTS",
    ]
    with patch("repository.meetings_repository.get_worksheet", return_value=sheet):
        update_meeting("nonexistent", start_time="18:30")
    sheet.update_cell.assert_not_called()


# ── delete_meeting ────────────────────────────────────────────────────────────

def test_delete_meeting_deletes_correct_row():
    sheet = MagicMock()
    sheet.get_all_records.return_value = FAKE_ROWS
    with patch("repository.meetings_repository.get_worksheet", return_value=sheet):
        delete_meeting("anora")
    sheet.delete_rows.assert_called_once_with(3)


def test_delete_meeting_no_match_does_nothing():
    sheet = MagicMock()
    sheet.get_all_records.return_value = FAKE_ROWS
    with patch("repository.meetings_repository.get_worksheet", return_value=sheet):
        delete_meeting("nonexistent")
    sheet.delete_rows.assert_not_called()
