#!/usr/bin/env python3
"""Copy the live club tabs into TEST-* or PROD-* tabs.

Live tabs (Users, Watchlist, …) stay untouched. Destination tabs are replaced,
not appended.

    ENV=dev .venv/bin/python scripts/migrate_sheets.py
    ENV=dev .venv/bin/python scripts/migrate_sheets.py --write
    ENV=dev .venv/bin/python scripts/migrate_sheets.py --target prod --write

The app reads whichever set matches ENV: dev uses TEST-*, prod uses PROD-*.

Mapping:
    Users        -> Users          same columns
    FilmLog      -> FilmLog        same columns
    Watchlist    -> Movies         IS_* flags become one STATUS
    Nominations  -> NominationLog  slug, nominator, voters, date
    Selected     -> Selected       ROTW is dropped (it lives on Meetings)
    Meetings     -> Meetings       ROTW copied from Selected by movie slug
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
from infrastructure.cache import cache
from infrastructure.sheets_client import _get_spreadsheet

MOVIE_HEADERS = [
    "TITLE", "SLUG", "URL", "ADDED_BY", "DATE_ADDED", "POSTER",
    "STATUS", "NOMINATED_BY", "VOTED_BY", "WATCHED_DATE",
]
USER_HEADERS = ["USERNAME", "DATE_JOINED"]
FILM_LOG_HEADERS = [
    "USERNAME", "SLUG", "TITLE", "RATING", "HAS_REVIEW",
    "WORD_COUNT", "REVIEW_LINK", "UPDATED_AT",
]
NOMINATION_HEADERS = ["SLUG", "NOMINATED_BY", "VOTED_BY", "DATE_NOMINATED"]
SELECTED_HEADERS = [
    "TITLE", "SLUG", "URL", "ADDED_BY", "DATE_ADDED", "POSTER",
    "NOMINATED_BY", "VOTED_BY", "WATCHED_DATE",
]
MEETING_HEADERS = [
    "DATE", "MOVIE_NAME", "MOVIE_SLUG", "START_TIME", "END_TIME", "PARTICIPANTS", "ROTW",
]


def _cell(row: dict, key: str) -> str:
    value = row.get(key, "")
    return "" if value is None else str(value).strip()


def _is_true(row: dict, key: str) -> bool:
    return _cell(row, key).upper() == "TRUE"


def movie_status(row: dict) -> str:
    """Old watchlist used three flags. The new Movies tab uses one status."""
    if _is_true(row, "IS_SELECTED"):
        return "selected"
    if _is_true(row, "IS_NOMINATED"):
        return "nominated"
    if _is_true(row, "IS_WATCHED"):
        return "watched"
    return "backlog"


def build_tables(sheets: dict[str, list[dict]]) -> tuple[dict[str, tuple[list[str], list[list[str]]]], list[str]]:
    """Return TEST tab name -> (headers, rows), plus notes about ROTW with no meeting."""
    watched_dates = {_cell(row, "SLUG"): _cell(row, "WATCHED_DATE") for row in sheets["Selected"]}
    rotw_by_slug = {
        _cell(row, "SLUG"): _cell(row, "ROTW")
        for row in sheets["Selected"]
        if _cell(row, "ROTW")
    }

    movies = []
    for row in sheets["Watchlist"]:
        slug = _cell(row, "SLUG")
        movies.append([
            _cell(row, "TITLE"),
            slug,
            _cell(row, "URL"),
            _cell(row, "ADDED_BY"),
            _cell(row, "DATE_ADDED"),
            _cell(row, "POSTER"),
            movie_status(row),
            _cell(row, "NOMINATED_BY"),
            _cell(row, "VOTED_BY"),
            watched_dates.get(slug, ""),
        ])

    users = [[_cell(row, "USERNAME"), _cell(row, "DATE_JOINED")] for row in sheets["Users"]]
    film_logs = [
        [_cell(row, header) for header in FILM_LOG_HEADERS]
        for row in sheets["FilmLog"]
    ]
    nominations = [
        [
            _cell(row, "SLUG"),
            _cell(row, "NOMINATED_BY"),
            _cell(row, "VOTED_BY"),
            _cell(row, "DATE_ADDED"),
        ]
        for row in sheets["Nominations"]
    ]
    selected = [
        [_cell(row, header) for header in SELECTED_HEADERS]
        for row in sheets["Selected"]
    ]

    meeting_slugs = {_cell(row, "MOVIE_SLUG") for row in sheets["Meetings"]}
    meetings = []
    for row in sheets["Meetings"]:
        slug = _cell(row, "MOVIE_SLUG")
        meetings.append([
            _cell(row, "DATE"),
            _cell(row, "MOVIE_NAME"),
            slug,
            _cell(row, "START_TIME"),
            _cell(row, "END_TIME"),
            _cell(row, "PARTICIPANTS"),
            rotw_by_slug.get(slug, ""),
        ])

    notes = [
        f"{slug} has ROTW on Selected and no Meetings row"
        for slug in rotw_by_slug
        if slug not in meeting_slugs
    ]

    tables = {
        "Users": (USER_HEADERS, users),
        "FilmLog": (FILM_LOG_HEADERS, film_logs),
        "Movies": (MOVIE_HEADERS, movies),
        "NominationLog": (NOMINATION_HEADERS, nominations),
        "Selected": (SELECTED_HEADERS, selected),
        "Meetings": (MEETING_HEADERS, meetings),
    }
    return tables, notes


def _replace_tab(spreadsheet, title: str, headers: list[str], rows: list[list[str]]) -> None:
    try:
        worksheet = spreadsheet.worksheet(title)
    except Exception:
        worksheet = spreadsheet.add_worksheet(title=title, rows=max(len(rows) + 10, 100), cols=len(headers))
    worksheet.clear()
    worksheet.update("A1", [headers, *rows], value_input_option="RAW")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("test", "prod"), default="test", help="Which prefixed tabs to fill. Default: test.")
    parser.add_argument("--write", action="store_true", help="Replace the destination tabs. Omit to preview only.")
    args = parser.parse_args()
    prefix = "TEST" if args.target == "test" else "PROD"

    spreadsheet = _get_spreadsheet()
    source_names = ["Users", "Watchlist", "FilmLog", "Nominations", "Selected", "Meetings"]
    sheets = {name: spreadsheet.worksheet(name).get_all_records() for name in source_names}
    tables, notes = build_tables(sheets)

    print(f"Preview for {prefix}-* tabs. Live tabs are not changed.")
    for name, (headers, rows) in tables.items():
        print(f"  {prefix}-{name}: {len(rows)} rows  ({', '.join(headers)})")
    if notes:
        print("ROTW left off Meetings (no matching meeting):")
        for note in notes:
            print(f"  {note}")

    if not args.write:
        print(f"\nDry run. Re-run with --target {args.target} --write to replace those tabs.")
        return

    for name, (headers, rows) in tables.items():
        title = f"{prefix}-{name}"
        print(f"Writing {title}...")
        _replace_tab(spreadsheet, title, headers, rows)
    if (prefix == "TEST" and config.ENV == "dev") or (prefix == "PROD" and config.ENV == "prod"):
        cache.clear()
        print("Disk cache cleared.")
    print(f"Done. {prefix}-* tabs replaced.")


if __name__ == "__main__":
    main()
