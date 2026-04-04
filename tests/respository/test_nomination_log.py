from unittest.mock import MagicMock, patch
from models.nomination_log import NominationLog
from repository.nomination_log_repository import get_all_nominations, add_nomination

FAKE_ROWS = [
    {"SLUG": "the-substance", "NOMINATED_BY": "KingKrab", "VOTED_BY": "bjoubs, GeoMoD", "DATE_NOMINATED": "01/10/2025"},
    {"SLUG": "anora", "NOMINATED_BY": "bjoubs", "VOTED_BY": "", "DATE_NOMINATED": "01/12/2025"},
    {"SLUG": "the-substance", "NOMINATED_BY": "GeoMoD", "VOTED_BY": "bjoubs, KingKrab", "DATE_NOMINATED": "02/01/2025"},
]


def fake_worksheet(records):
    sheet = MagicMock()
    sheet.get_all_records.return_value = records
    return sheet


def test_get_all_nominations_returns_models():
    with patch("repository.nomination_log_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_all_nominations()
    assert len(result) == 3
    assert all(isinstance(n, NominationLog) for n in result)


def test_get_all_nominations_maps_fields():
    with patch("repository.nomination_log_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_all_nominations()
    assert result[0].slug == "the-substance"
    assert result[0].nominated_by == "KingKrab"
    assert result[0].voted_by == ["bjoubs", "GeoMoD"]
    assert result[0].date_nominated == "01/10/2025"


def test_get_all_nominations_empty_sheet():
    with patch("repository.nomination_log_repository.get_worksheet", return_value=fake_worksheet([])):
        assert get_all_nominations() == []


def test_add_nomination_appends_row():
    sheet = fake_worksheet([])
    nomination = NominationLog(slug="heat-1995", nominated_by="bjoubs", voted_by=["KingKrab", "GeoMoD"], date_nominated="03/01/2025")
    with patch("repository.nomination_log_repository.get_worksheet", return_value=sheet):
        add_nomination(nomination)
    sheet.append_row.assert_called_once_with(["heat-1995", "bjoubs", "KingKrab, GeoMoD", "03/01/2025"])
