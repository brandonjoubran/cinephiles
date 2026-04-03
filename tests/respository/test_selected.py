from unittest.mock import MagicMock, patch
from repository.selected_repository import get_selected_slugs, get_rotw_winners

FAKE_ROWS = [
    {"SLUG": "the-substance", "TITLE": "The Substance", "ROTW": "bjoubs"},
    {"SLUG": "dune-part-two", "TITLE": "Dune: Part Two", "ROTW": "bjoubs, kingkrab"},
    {"SLUG": "anora", "TITLE": "Anora", "ROTW": ""},
]


def fake_worksheet(records):
    sheet = MagicMock()
    sheet.get_all_records.return_value = records
    return sheet


# ── get_selected_slugs ────────────────────────────────────────────────────────

def test_get_selected_slugs_returns_list_of_strings():
    with patch("repository.selected_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_selected_slugs()
    assert result == ["the-substance", "dune-part-two", "anora"]


def test_get_selected_slugs_skips_empty():
    rows = [{"SLUG": "the-substance", "ROTW": ""}, {"SLUG": "", "ROTW": ""}, {"SLUG": "anora", "ROTW": ""}]
    with patch("repository.selected_repository.get_worksheet", return_value=fake_worksheet(rows)):
        result = get_selected_slugs()
    assert result == ["the-substance", "anora"]


def test_get_selected_slugs_empty_sheet():
    with patch("repository.selected_repository.get_worksheet", return_value=fake_worksheet([])):
        assert get_selected_slugs() == []


# ── get_rotw_winners ──────────────────────────────────────────────────────────

def test_get_rotw_winners_returns_flat_list():
    with patch("repository.selected_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_rotw_winners()
    assert result == ["bjoubs", "bjoubs", "kingkrab"]


def test_get_rotw_winners_skips_empty():
    rows = [{"SLUG": "a", "ROTW": ""}, {"SLUG": "b", "ROTW": "bjoubs"}]
    with patch("repository.selected_repository.get_worksheet", return_value=fake_worksheet(rows)):
        result = get_rotw_winners()
    assert result == ["bjoubs"]


def test_get_rotw_winners_strips_whitespace():
    rows = [{"SLUG": "a", "ROTW": " bjoubs , kingkrab "}]
    with patch("repository.selected_repository.get_worksheet", return_value=fake_worksheet(rows)):
        result = get_rotw_winners()
    assert result == ["bjoubs", "kingkrab"]


def test_get_rotw_winners_empty_sheet():
    with patch("repository.selected_repository.get_worksheet", return_value=fake_worksheet([])):
        assert get_rotw_winners() == []
