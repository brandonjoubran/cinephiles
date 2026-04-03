import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "dev")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "OnlyCinephilesDB_Dev")
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE", "onlycinephiles-b6b986d3cb57.json")
TMDB_API_KEY = os.getenv("API_KEY", "")
TMDB_API_READ_TOKEN = os.getenv("API_READ_TOKEN", "")


def tab(name: str) -> str:
    """Return the real tab name. In dev, all tabs are prefixed with TEST-."""
    return f"TEST-{name}" if ENV == "dev" else name
