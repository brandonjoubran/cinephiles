"""
Integration test — hits the real Google Sheet.
Requires credentials and network access.

Run with:
    pytest tests/respository/test_user_it.py -v -m integration
"""
import pytest
from infrastructure.sheets_client import get_worksheet


@pytest.mark.integration
def test_test_users_tab_is_reachable():
    sheet = get_worksheet("TEST-Users")
    assert sheet.title == "TEST-Users"


@pytest.mark.integration
def test_test_users_tab_has_header_row():
    sheet = get_worksheet("TEST-Users")
    rows = sheet.get_all_values()
    assert len(rows) >= 1, "TEST-Users tab should have at least a header row"


@pytest.mark.integration
def test_test_users_tab_has_expected_columns():
    sheet = get_worksheet("TEST-Users")
    print(sheet.get_all_values())
    header = sheet.get_all_values()[0]
    assert "USERNAME" in header
    assert "DATE_JOINED" in header
