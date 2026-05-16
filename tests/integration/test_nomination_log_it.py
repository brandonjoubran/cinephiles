"""
Integration tests — NominationLog sheet.
"""
import pytest
from pydantic import ValidationError

import repository.nomination_log_repository as nomination_log_repo
from infrastructure.cache import cache
from models.nomination_log import NominationLog
from tests.integration.sheet_helpers import NOMINATION_LOG_HEADERS, assert_headers, open_tab

pytestmark = pytest.mark.integration


def test_nomination_log_tab_has_expected_headers(require_integration_env):
    assert_headers(open_tab("NominationLog"), NOMINATION_LOG_HEADERS)


def test_nomination_log_every_row_parses(require_integration_env):
    """Every row on the sheet must match the NominationLog model — catches column drift or bad data."""
    rows = open_tab("NominationLog").get_all_records()
    errors = []
    for i, row in enumerate(rows, start=2):
        try:
            NominationLog(
                slug=row["SLUG"],
                nominated_by=row["NOMINATED_BY"],
                voted_by=row.get("VOTED_BY", ""),
                date_nominated=row["DATE_NOMINATED"],
            )
        except ValidationError as exc:
            errors.append(f"row {i}: {row!r} -> {exc}")
    assert not errors, "Invalid NominationLog rows:\n" + "\n".join(errors)


def test_add_nomination_round_trip(integration_movie_slug):
    slug = integration_movie_slug

    nomination_log_repo.add_nomination(NominationLog(
        slug=slug,
        nominated_by="it-user",
        voted_by=["it-voter"],
        date_nominated="01/15/2025",
    ))
    cache.clear()

    logs = nomination_log_repo.get_all_nominations()
    match = [n for n in logs if n.slug == slug and n.nominated_by == "it-user"]
    assert len(match) == 1
    assert match[0].voted_by == ["it-voter"]
    assert match[0].date_nominated == "01/15/2025"
