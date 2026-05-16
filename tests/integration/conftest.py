"""Shared fixtures for integration tests against the TEST-* spreadsheet tabs.

Run (serially — avoids Sheets API rate limits):
    pytest tests/integration -m integration -v

Requires ENV=dev, credentials file, and TEST-* tabs with expected headers.
Add ROTW to TEST-Meetings before running meeting tests.
"""
import time
from pathlib import Path

import pytest

import config
from tests.integration.sheet_helpers import IT_MOVIE_SLUG, cleanup_integration_movie


@pytest.fixture(scope="session")
def require_integration_env():
    if config.ENV != "dev":
        pytest.skip("Integration tests require ENV=dev (TEST-* tab prefix)")
    creds = Path(config.GOOGLE_CREDS_FILE)
    if not creds.is_file():
        pytest.skip(f"Google credentials not found: {creds}")


@pytest.fixture(scope="session", autouse=True)
def _integration_session_bookends(require_integration_env):
    """One cleanup at start/end of the integration run (not every test)."""
    cleanup_integration_movie(IT_MOVIE_SLUG)
    yield
    cleanup_integration_movie(IT_MOVIE_SLUG)


@pytest.fixture(autouse=True)
def _pace_api_calls(require_integration_env):
    """Space out integration tests to stay under Sheets read quotas."""
    yield
    time.sleep(2.5)


@pytest.fixture
def integration_movie_slug(require_integration_env):
    """Reserved slug for tests that write rows; session bookends handle cleanup."""
    yield IT_MOVIE_SLUG
