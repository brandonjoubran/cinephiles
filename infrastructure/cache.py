"""Save sheet tab data to a JSON file so we read Google Sheets less often.

Repositories call cache.get("movies") before opening a sheet. On a miss they
fetch from Sheets and call cache.set("movies", rows). Any sheet write calls
cache.clear() so the next read is fresh.

File: .cache/{ENV}__{SPREADSHEET_NAME}.json  (see config.cache_file_path)
Shape: {"movies": [{...}, ...], "users": [{...}, ...], ...}

Clear manually: GET /cache/clear, delete the file, or cache.clear() in a script.
"""

import json
from pathlib import Path

from config import cache_file_path


def objects_to_json(value):
    """Pydantic model lists → plain dict lists. Everything else stored as-is."""
    if not isinstance(value, list):
        return value
    if not value:
        return []
    first_item = value[0]
    if hasattr(first_item, "model_dump"):
        return [item.model_dump(mode="json") for item in value]
    return value


def json_to_objects(cache_key: str, value):
    """Plain dict lists from JSON → Pydantic models for known sheet tabs."""
    if not isinstance(value, list):
        return value

    if cache_key == "movies":
        from models.movie import Movie
        return [Movie.model_validate(row) for row in value]

    if cache_key == "users":
        from models.user import User
        return [User.model_validate(row) for row in value]

    if cache_key == "film_logs":
        from models.film_log import FilmLog
        return [FilmLog.model_validate(row) for row in value]

    if cache_key == "meetings":
        from models.meeting import Meeting
        return [Meeting.model_validate(row) for row in value]

    if cache_key == "nomination_logs":
        from models.nomination_log import NominationLog
        return [NominationLog.model_validate(row) for row in value]

    if cache_key == "selected":
        from models.selected_film import SelectedFilm
        return [SelectedFilm.model_validate(row) for row in value]

    return value


class Cache:
    """One JSON file holding every cached tab."""

    def __init__(self, path: str | Path | None = None):
        self.file_path = Path(path) if path is not None else Path(cache_file_path())
        self.store: dict = {}
        self.disk_loaded = False

    def load_from_disk_if_needed(self) -> None:
        if self.disk_loaded:
            return

        self.disk_loaded = True

        if not self.file_path.exists():
            self.store = {}
            return

        try:
            file_text = self.file_path.read_text(encoding="utf-8")
            self.store = json.loads(file_text)
        except (json.JSONDecodeError, OSError):
            self.store = {}

    def save_to_disk(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        file_text = json.dumps(self.store, indent=2)
        self.file_path.write_text(file_text, encoding="utf-8")

    def get(self, key: str):
        self.load_from_disk_if_needed()

        if key not in self.store:
            return None

        raw_value = self.store[key]
        return json_to_objects(key, raw_value)

    def set(self, key: str, value) -> None:
        self.load_from_disk_if_needed()

        json_value = objects_to_json(value)
        self.store[key] = json_value
        self.save_to_disk()

    def clear(self) -> None:
        self.store = {}
        self.disk_loaded = False

        if self.file_path.exists():
            self.file_path.unlink(missing_ok=True)


cache = Cache()
