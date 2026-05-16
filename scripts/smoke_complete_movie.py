#!/usr/bin/env python3
"""
Ad-hoc smoke test: add fake movies, run nominate → select → complete, check stats.

Uses the real API (TestClient) and TEST-* sheets when ENV=dev.
Letterboxd RSS is patched (no real HTTP) so the target user appears to have watched the film.

Run from repo root:
    ENV=dev .venv/bin/python scripts/smoke_complete_movie.py

Optional env:
    SMOKE_USER=bjoubs       # user who should gain +1 movies_watched
    SMOKE_PAUSE=2.5         # seconds between heavy sheet steps (avoid 429)
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
import repository.film_log_repository as film_log_repo
import repository.movies_repository as movies_repo
import service.stats_service as stats_service
from fastapi.testclient import TestClient
from infrastructure.cache import cache
from infrastructure.letterboxd_rss import LetterboxdFilm
from infrastructure.sheet_rows import _col_letter, serialize_field_value
from main import app
from models.movie import MovieStatus
from tests.integration.sheet_helpers import _with_retry, open_tab

import gspread

# ── Config ────────────────────────────────────────────────────────────────────

E2E_PREFIX = "e2e-smoke-"
FAKE_SLUGS = [f"{E2E_PREFIX}1", f"{E2E_PREFIX}2", f"{E2E_PREFIX}3"]
FAKE_SLUG_SET = set(FAKE_SLUGS)
SELECTED_SLUG = FAKE_SLUGS[0]
TARGET_USER = os.environ.get("SMOKE_USER", "bjoubs")
NOMINATOR = TARGET_USER
PAUSE_SEC = float(os.environ.get("SMOKE_PAUSE", "2.5"))

# One read per tab for cleanup / batch updates
SHEET_COLUMNS = [
    ("Movies", "SLUG"),
    ("FilmLog", "SLUG"),
    ("NominationLog", "SLUG"),
    ("Meetings", "MOVIE_SLUG"),
]


@dataclass
class MovieSnapshot:
    slug: str
    status: str
    nominated_by: str
    voted_by: str
    watched_date: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def pause(multiplier: float = 1.0) -> None:
    """Wait between sheet bursts so we stay under Google Sheets quotas."""
    time.sleep(PAUSE_SEC * multiplier)


def sheets_retry(action, attempts: int = 6, base_delay: float = 5.0):
    """Retry on 429 (read or write quota). Waits longer each attempt."""
    for attempt in range(attempts):
        try:
            return action()
        except gspread.exceptions.APIError as exc:
            if attempt == attempts - 1 or exc.response.status_code != 429:
                raise
            wait = base_delay * (attempt + 1)
            print(f"     (rate limited, waiting {wait:.0f}s...)")
            time.sleep(wait)


def ok(message: str) -> None:
    print(f"  OK  {message}")


def fail(message: str) -> None:
    print(f"  FAIL  {message}")
    raise AssertionError(message)


def clear_cache() -> None:
    cache.clear()


def stats_for(username: str) -> dict:
    """One stats pass (reads FilmLog, Users, Movies, Meetings)."""
    clear_cache()
    pause()
    for row in stats_service.get_all_user_stats():
        if row.username.lower() == username.lower():
            return row.model_dump()
    fail(f"User {username!r} not found on Users sheet")


def snapshot_all_movies() -> list[MovieSnapshot]:
    clear_cache()
    pause()
    return [
        MovieSnapshot(
            slug=m.slug,
            status=m.status.value,
            nominated_by=m.nominated_by or "",
            voted_by=", ".join(m.voted_by),
            watched_date=m.watched_date or "",
        )
        for m in movies_repo.get_all_movies()
        if m.slug not in FAKE_SLUG_SET
    ]


def _apply_movie_field_updates(updates_by_slug: dict[str, dict[str, object]]) -> None:
    """Change many rows with one read and one write (avoids per-cell write quota)."""
    if not updates_by_slug:
        return

    sheet = open_tab("Movies")

    def _run():
        values = sheet.get_all_values()
        if not values:
            return

        headers = values[0]
        col_for_header = {str(h).strip().upper(): index for index, h in enumerate(headers) if str(h).strip()}
        slug_col = col_for_header.get("SLUG")
        if slug_col is None:
            return

        for row in values[1:]:
            while len(row) < len(headers):
                row.append("")
            slug = row[slug_col].strip()
            field_updates = updates_by_slug.get(slug)
            if not field_updates:
                continue
            for field, value in field_updates.items():
                col = col_for_header.get(field.upper())
                if col is not None:
                    row[col] = serialize_field_value(value)

        end_col = _col_letter(len(headers))
        sheet.update(f"A1:{end_col}{len(values)}", values)
        clear_cache()

    sheets_retry(_run)


def restore_movies(snapshots: list[MovieSnapshot], only_slugs: set[str]) -> None:
    """Put back rows that prepare changed. Skips movies we never touched."""
    updates = {
        snap.slug: {
            "status": snap.status,
            "nominated_by": snap.nominated_by,
            "voted_by": snap.voted_by,
            "watched_date": snap.watched_date,
        }
        for snap in snapshots
        if snap.slug in only_slugs
    }
    _apply_movie_field_updates(updates)


def prepare_movies_sheet() -> set[str]:
    """Clear nominations/selections. Keep watched club films for stats/streak."""
    clear_cache()
    pause()
    movies = movies_repo.get_all_movies()
    updates: dict[str, dict[str, object]] = {}

    for movie in movies:
        if movie.slug in FAKE_SLUG_SET:
            updates[movie.slug] = {
                "status": MovieStatus.BACKLOG.value,
                "nominated_by": "",
                "voted_by": "",
                "watched_date": "",
            }
        elif movie.status in (MovieStatus.NOMINATED, MovieStatus.SELECTED):
            updates[movie.slug] = {
                "status": MovieStatus.BACKLOG.value,
                "nominated_by": "",
                "voted_by": "",
            }

    _apply_movie_field_updates(updates)
    ok("Sheet ready: no active nominations; watched history kept")
    return set(updates.keys())


def cleanup_e2e_rows() -> None:
    """Delete all e2e rows — one read per tab, not one per slug."""
    for tab_name, column in SHEET_COLUMNS:
        sheet = open_tab(tab_name)

        def _delete(sheet=sheet, column=column):
            rows = sheet.get_all_records()
            for row_index in reversed(range(len(rows))):
                if rows[row_index].get(column) in FAKE_SLUG_SET:
                    sheet.delete_rows(row_index + 2)
            clear_cache()

        _with_retry(_delete)
        pause()

    ok("Removed e2e rows from Movies, FilmLog, NominationLog, Meetings")


def fake_rss_for_user(username: str, slugs: list[str] | None = None) -> dict[str, LetterboxdFilm]:
    """Pretend TARGET_USER watched the e2e film today (no Letterboxd HTTP)."""
    if slugs is None or username.lower() != TARGET_USER.lower():
        return {}

    today = date.today().isoformat()
    films = {}
    for slug in slugs:
        if slug in FAKE_SLUG_SET:
            films[slug] = LetterboxdFilm(
                slug=slug,
                title=f"E2E Test {slug}",
                rating=4.0,
                has_review=True,
                word_count=42,
                review_link=f"https://letterboxd.com/{username}/film/{slug}/",
                watched_date=today,
            )
    return films


def assert_status(movie: dict, expected: str, label: str) -> None:
    if movie.get("status") != expected:
        fail(f"{label}: expected status {expected!r}, got {movie.get('status')!r}")


# ── Main flow ─────────────────────────────────────────────────────────────────

def run() -> None:
    if config.ENV != "dev":
        fail("Refusing to run: set ENV=dev so only TEST-* tabs are touched")

    creds = Path(config.GOOGLE_CREDS_FILE)
    if not creds.is_file():
        fail(f"Google credentials not found: {creds}")

    print(f"\nSmoke test (ENV={config.ENV}, user={TARGET_USER}, pause={PAUSE_SEC}s)\n")

    movie_snapshots: list[MovieSnapshot] = []
    modified_slugs: set[str] = set()
    test_passed = False
    client = TestClient(app)

    try:
        print("1. Cleanup leftover e2e data")
        cleanup_e2e_rows()

        print("2. Snapshot real movies (restore after test)")
        movie_snapshots = snapshot_all_movies()

        print("3. Prepare Movies sheet")
        modified_slugs = prepare_movies_sheet()
        pause()

        print("4. Stats BEFORE complete")
        stats_before = stats_for(TARGET_USER)
        print(f"     {TARGET_USER}: movies_watched={stats_before['movies_watched']}, streak={stats_before['streak']}")

        print("5. Add 3 fake movies via API")
        for slug in FAKE_SLUGS:
            response = client.post(
                "/movies",
                json={
                    "title": f"E2E Test {slug}",
                    "slug": slug,
                    "url": f"https://letterboxd.com/film/{slug}/",
                    "added_by": NOMINATOR,
                    "poster": "https://example.com/poster.jpg",
                },
            )
            if response.status_code not in (200, 409):
                fail(f"POST /movies {slug}: {response.status_code} {response.text}")
            if response.status_code == 200:
                assert_status(response.json(), "backlog", slug)
            else:
                clear_cache()
                existing = movies_repo.get_movie_by_slug(slug)
                if not existing or existing.status != MovieStatus.BACKLOG:
                    fail(f"{slug} should be backlog when reusing existing row")
            pause()
        ok("Three movies on backlog")

        print("6. Nominate all 3 fake movies")
        nominated = {}
        for slug in FAKE_SLUGS:
            response = client.post(f"/movies/{slug}/nominate", json={"username": NOMINATOR})
            response.raise_for_status()
            nominated[slug] = response.json()
            assert_status(nominated[slug], "nominated", slug)
            pause()
        ok("All three nominated")

        print(f"7. Select {SELECTED_SLUG}")
        response = client.post(f"/movies/{SELECTED_SLUG}/select")
        response.raise_for_status()
        assert_status(response.json(), "selected", SELECTED_SLUG)
        for slug in FAKE_SLUGS[1:]:
            assert_status(nominated[slug], "nominated", slug)
        ok("One selected, others still nominated")
        pause()

        print(f"8. Complete {SELECTED_SLUG} (fake Letterboxd RSS, no HTTP)")
        with patch("service.letterboxd_service.fetch_user_films", side_effect=fake_rss_for_user):
            response = client.post(f"/movies/{SELECTED_SLUG}/complete")
        response.raise_for_status()
        completed = response.json()
        if completed["status"] != "watched" or not completed.get("watched_date"):
            fail("Completed movie should be watched with a date")
        ok("Complete returned watched")
        pause()

        print("9. Assert movie statuses (one sheet read)")
        clear_cache()
        pause()
        by_slug = {m.slug: m for m in movies_repo.get_all_movies()}

        if by_slug[SELECTED_SLUG].status != MovieStatus.WATCHED:
            fail(f"{SELECTED_SLUG} should be watched")
        for slug in FAKE_SLUGS[1:]:
            other = by_slug.get(slug)
            if not other or other.status != MovieStatus.BACKLOG:
                fail(f"{slug} should be back on backlog")
            if other.nominated_by:
                fail(f"{slug} should have nomination fields cleared")
        ok("Watched + other nominees reset to backlog")

        print("10. Assert FilmLog row for target user")
        clear_cache()
        pause()
        slugs_logged = {log.slug for log in film_log_repo.get_film_logs_for_user(TARGET_USER)}
        if SELECTED_SLUG not in slugs_logged:
            fail(f"FilmLog missing {SELECTED_SLUG} for {TARGET_USER}")
        ok(f"FilmLog contains {SELECTED_SLUG} for {TARGET_USER}")

        print("11. Stats AFTER complete")
        stats_after = stats_for(TARGET_USER)
        print(
            f"     {TARGET_USER}: movies_watched={stats_after['movies_watched']} "
            f"(club FilmLog rows), streak={stats_after['streak']}"
        )

        expected_watched = stats_before["movies_watched"] + 1
        if stats_after["movies_watched"] != expected_watched:
            fail(f"movies_watched expected {expected_watched}, got {stats_after['movies_watched']}")
        ok(f"movies_watched +1 ({stats_before['movies_watched']} → {stats_after['movies_watched']})")

        if stats_after["streak"] < stats_before["streak"]:
            fail(f"streak should not decrease ({stats_before['streak']} → {stats_after['streak']})")
        if stats_after["streak"] == stats_before["streak"] + 1:
            ok(f"streak +1 ({stats_before['streak']} → {stats_after['streak']})")
        else:
            print(
                f"     note: streak {stats_before['streak']} → {stats_after['streak']} "
                "(+1 only if prior club films are all in FilmLog)"
            )

        print("\nAll assertions passed.\n")
        test_passed = True

    finally:
        print("12. Cleanup")
        cleanup_e2e_rows()
        if movie_snapshots and modified_slugs:
            print(f"    Restoring {len(modified_slugs)} movie row(s) changed during prepare")
            pause(multiplier=2)
            try:
                restore_movies(movie_snapshots, modified_slugs)
                ok("Restored movie snapshots")
            except Exception as exc:
                if test_passed:
                    print(f"  WARN  Restore hit Sheets quota: {exc}")
                    print("        E2e data was removed; re-run later or fix rows manually on TEST-Movies.")
                else:
                    raise
        print("Done.\n")


if __name__ == "__main__":
    try:
        run()
    except AssertionError:
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}\n")
        sys.exit(1)
