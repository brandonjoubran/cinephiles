"""
Integration tests — FilmLog sheet (read-only header check).
"""
import pytest

import repository.film_log_repository as film_log_repo
from tests.integration.sheet_helpers import FILM_LOG_HEADERS, assert_headers, open_tab

pytestmark = pytest.mark.integration


def test_film_log_tab_has_expected_headers(require_integration_env):
    assert_headers(open_tab("FilmLog"), FILM_LOG_HEADERS)


def test_film_log_every_row_parses(require_integration_env):
    film_log_repo.get_all_film_logs()
