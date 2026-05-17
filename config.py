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


# Folder for on-disk sheet cache (see infrastructure/cache.py). Override in .env if needed.
CACHE_DIR = os.getenv("CACHE_DIR", ".cache")


def cache_file_path() -> str:
    """Path to the JSON cache file for the current env and spreadsheet.

    Example: ``.cache/dev__OnlyCinephilesDB_Dev.json``

    Uses ``ENV`` and ``SPREADSHEET_NAME`` so dev TEST tabs and prod tabs never
    share the same cache file.
    """
    safe_name = SPREADSHEET_NAME.replace("/", "_").replace(" ", "_")
    return os.path.join(CACHE_DIR, f"{ENV}__{safe_name}.json")
