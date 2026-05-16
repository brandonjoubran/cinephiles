from datetime import date
from unittest.mock import patch

from infrastructure.letterboxd_rss import LetterboxdFilm
from service.letterboxd_service import record_club_watches_after_complete


def test_record_club_watches_skips_out_of_window():
    film = LetterboxdFilm(
        slug="the-substance",
        title="The Substance",
        rating=4.0,
        has_review=False,
        word_count=0,
        review_link="https://letterboxd.com/bjoubs/film/the-substance/",
        watched_date="2025-01-01",
    )

    with (
        patch("service.letterboxd_service.movies_repo.get_latest_watched_date", return_value=date(2025, 2, 1)),
        patch("service.letterboxd_service.users_repo.get_usernames", return_value=["bjoubs"]),
        patch("service.letterboxd_service.fetch_user_films", return_value={"the-substance": film}),
        patch("service.letterboxd_service.film_log_repo.save_film_log") as mock_save,
    ):
        saved = record_club_watches_after_complete("the-substance", completed_on=date(2025, 3, 10))

    assert saved == 0
    mock_save.assert_not_called()


def test_record_club_watches_saves_in_window():
    film = LetterboxdFilm(
        slug="the-substance",
        title="The Substance",
        rating=4.0,
        has_review=True,
        word_count=50,
        review_link="https://letterboxd.com/bjoubs/film/the-substance/",
        watched_date="2025-03-05",
    )

    with (
        patch("service.letterboxd_service.movies_repo.get_latest_watched_date", return_value=date(2025, 2, 1)),
        patch("service.letterboxd_service.users_repo.get_usernames", return_value=["bjoubs"]),
        patch("service.letterboxd_service.fetch_user_films", return_value={"the-substance": film}),
        patch("service.letterboxd_service.film_log_repo.save_film_log") as mock_save,
    ):
        saved = record_club_watches_after_complete("the-substance", completed_on=date(2025, 3, 10))

    assert saved == 1
    mock_save.assert_called_once()
    assert mock_save.call_args[0][0].slug == "the-substance"
