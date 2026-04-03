"""
Single shared gspread connection.
All repositories get their worksheet via get_worksheet(tab_name).

Never import this directly in tests — inject a fake sheet instead.
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_CREDS_FILE, SPREADSHEET_NAME, tab

_spreadsheet = None

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def _get_spreadsheet():
    global _spreadsheet
    if _spreadsheet is None:
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        _spreadsheet = client.open(SPREADSHEET_NAME)
    return _spreadsheet


def get_worksheet(name: str):
    """Return a gspread Worksheet. In dev, automatically uses TEST- prefixed tabs."""
    return _get_spreadsheet().worksheet(tab(name))
