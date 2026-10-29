from unittest.mock import patch

from models.movie import Movie, MovieStatus
from models.selected_film import SelectedFilm
from service.watchlist_page_service import get_watchlist_movies


def _movie(slug: str, status: MovieStatus) -> Movie:
    return Movie(
        title=slug,
        slug=slug,
        url=f"https://letterboxd.com/film/{slug}/",
        added_by="bjoubs",
        date_added="01/01/2025",
        poster="",
        status=status,
        nominated_by="",
        voted_by=[],
        watched_date="",
    )


def test_watchlist_order_selected_then_nominated_then_backlog():
    movies = [
        _movie("backlog-a", MovieStatus.BACKLOG),
        _movie("nom-b", MovieStatus.NOMINATED),
        _movie("pick", MovieStatus.SELECTED),
    ]
    with patch("service.watchlist_page_service.movies_repo.get_all_movies", return_value=movies), patch(
        "service.watchlist_page_service.selected_repo.get_all_selected", return_value=[]
    ), patch("service.watchlist_page_service.film_log_repo.get_all_film_logs", return_value=[]):
        slugs = [row["SLUG"] for row in get_watchlist_movies()]
    assert slugs == ["pick", "nom-b", "backlog-a"]


def test_completed_films_come_from_selected_sheet():
    movies = [_movie("done", MovieStatus.WATCHED)]
    selected = [
        SelectedFilm(
            title="Done",
            slug="done",
            url="https://letterboxd.com/film/done/",
            added_by="bjoubs",
            date_added="01/01/2025",
            poster="",
            nominated_by="",
            voted_by=[],
            watched_date="02/01/2025",
        )
    ]
    with patch("service.watchlist_page_service.movies_repo.get_all_movies", return_value=movies), patch(
        "service.watchlist_page_service.selected_repo.get_all_selected", return_value=selected
    ), patch("service.watchlist_page_service.film_log_repo.get_all_film_logs", return_value=[]):
        rows = get_watchlist_movies()
    assert len(rows) == 1
    assert rows[0]["IS_WATCHED"] is True
    assert rows[0]["WATCHED_DATE"] == "02/01/2025"
