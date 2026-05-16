from unittest.mock import MagicMock

from infrastructure.sheet_rows import append_row_by_headers


def test_append_row_by_headers_maps_by_column_name():
    sheet = MagicMock()
    sheet.row_values.return_value = [
        "SLUG",
        "NOMINATED_BY",
        "DATE_NOMINATED",
        "VOTED_BY",
    ]
    append_row_by_headers(sheet, {
        "slug": "anora",
        "nominated_by": "bjoubs",
        "voted_by": ["KingKrab"],
        "date_nominated": "01/15/2025",
    })
    sheet.append_row.assert_called_once_with([
        "anora",
        "bjoubs",
        "01/15/2025",
        "KingKrab",
    ])
