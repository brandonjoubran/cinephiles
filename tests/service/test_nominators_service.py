from unittest.mock import patch

import pytest
from fastapi import HTTPException

from service.nominators_service import generate_nominators


def test_generate_nominators_picks_three_who_watched_latest():
    with (
        patch("service.nominators_service.selected_repo.get_latest_completed_slug", return_value="dune-part-two"),
        patch("service.nominators_service.film_log_repo.get_usernames_for_slug", return_value=["bjoubs", "kingkrab", "geomod", "alice"]),
        patch("service.nominators_service.users_repo.get_usernames", return_value=["bjoubs", "kingkrab", "geomod", "bob"]),
        patch("service.nominators_service.random.sample", side_effect=lambda pool, k: pool[:k]),
    ):
        slug, nominators = generate_nominators()

    assert slug == "dune-part-two"
    assert nominators == ["bjoubs", "kingkrab", "geomod"]


def test_generate_nominators_fewer_than_three_when_not_enough_eligible():
    with (
        patch("service.nominators_service.selected_repo.get_latest_completed_slug", return_value="anora"),
        patch("service.nominators_service.film_log_repo.get_usernames_for_slug", return_value=["bjoubs"]),
        patch("service.nominators_service.users_repo.get_usernames", return_value=["bjoubs", "kingkrab"]),
        patch("service.nominators_service.random.sample", side_effect=lambda pool, k: pool[:k]),
    ):
        slug, nominators = generate_nominators()

    assert slug == "anora"
    assert nominators == ["bjoubs"]


def test_generate_nominators_empty_when_no_one_watched():
    with (
        patch("service.nominators_service.selected_repo.get_latest_completed_slug", return_value="anora"),
        patch("service.nominators_service.film_log_repo.get_usernames_for_slug", return_value=[]),
        patch("service.nominators_service.users_repo.get_usernames", return_value=["bjoubs"]),
    ):
        slug, nominators = generate_nominators()

    assert slug == "anora"
    assert nominators == []


def test_generate_nominators_rejects_when_no_selected_films():
    with patch("service.nominators_service.selected_repo.get_latest_completed_slug", return_value=None):
        with pytest.raises(HTTPException) as exc:
            generate_nominators()
    assert exc.value.status_code == 400
