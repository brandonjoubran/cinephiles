"""
Integration tests — Users sheet (TEST-Users in dev).
"""
import pytest

import repository.users_repository as users_repo
from tests.integration.sheet_helpers import USERS_HEADERS, assert_headers, open_tab

pytestmark = pytest.mark.integration


def test_users_tab_is_reachable(require_integration_env):
    sheet = open_tab("Users")
    assert sheet.title.startswith("TEST-") or sheet.title == "Users"


def test_users_tab_has_expected_headers(require_integration_env):
    assert_headers(open_tab("Users"), USERS_HEADERS)


def test_users_every_row_parses(require_integration_env):
    users_repo.get_users()
