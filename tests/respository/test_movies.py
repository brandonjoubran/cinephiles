from unittest.mock import MagicMock, patch, call
from models.movie import Movie, MovieStatus
from repository.movies_repository import (
    get_all_movies,
    get_movies_by_status,
    get_movie_by_slug,
    add_movie,
    update_movie_fields,
    delete_movie,
)

FAKE_ROWS = [
    {
        "TITLE": "The Substance",
        "SLUG": "the-substance",
        "URL": "https://letterboxd.com/film/the-substance/",
        "ADDED_BY": "bjoubs",
        "DATE_ADDED": "01/15/2025",
        "POSTER": "https://image.tmdb.org/poster1.jpg",
        "STATUS": "watched",
        "NOMINATED_BY": "KingKrab",
        "VOTED_BY": "bjoubs, GeoMoD",
        "WATCHED_DATE": "02/01/2025",
    },
    {
        "TITLE": "Anora",
        "SLUG": "anora",
        "URL": "https://letterboxd.com/film/anora/",
        "ADDED_BY": "KingKrab",
        "DATE_ADDED": "01/20/2025",
        "POSTER": "https://image.tmdb.org/poster2.jpg",
        "STATUS": "nominated",
        "NOMINATED_BY": "bjoubs",
        "VOTED_BY": "",
        "WATCHED_DATE": "",
    },
    {
        "TITLE": "Dune: Part Two",
        "SLUG": "dune-part-two",
        "URL": "https://letterboxd.com/film/dune-part-two/",
        "ADDED_BY": "GeoMoD",
        "DATE_ADDED": "01/25/2025",
        "POSTER": "https://image.tmdb.org/poster3.jpg",
        "STATUS": "backlog",
        "NOMINATED_BY": "",
        "VOTED_BY": "",
        "WATCHED_DATE": "",
    },
]


def fake_worksheet(records):
    sheet = MagicMock()
    sheet.get_all_records.return_value = records
    return sheet


# ── get_all_movies ────────────────────────────────────────────────────────────

def test_get_all_movies_returns_models():
    with patch("repository.movies_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_all_movies()
    assert len(result) == 3
    assert all(isinstance(m, Movie) for m in result)


def test_get_all_movies_maps_fields():
    with patch("repository.movies_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_all_movies()
    assert result[0].title == "The Substance"
    assert result[0].slug == "the-substance"
    assert result[0].status == MovieStatus.WATCHED
    assert result[0].voted_by == ["bjoubs", "GeoMoD"]


def test_get_all_movies_empty_sheet():
    with patch("repository.movies_repository.get_worksheet", return_value=fake_worksheet([])):
        assert get_all_movies() == []


# ── get_movies_by_status ──────────────────────────────────────────────────────

def test_get_movies_by_status_watched():
    with patch("repository.movies_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_movies_by_status(MovieStatus.WATCHED)
    assert len(result) == 1
    assert result[0].slug == "the-substance"


def test_get_movies_by_status_nominated():
    with patch("repository.movies_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_movies_by_status(MovieStatus.NOMINATED)
    assert len(result) == 1
    assert result[0].slug == "anora"


def test_get_movies_by_status_backlog():
    with patch("repository.movies_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_movies_by_status(MovieStatus.BACKLOG)
    assert len(result) == 1
    assert result[0].slug == "dune-part-two"


def test_get_movies_by_status_selected_returns_empty():
    with patch("repository.movies_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_movies_by_status(MovieStatus.SELECTED)
    assert result == []


# ── get_movie_by_slug ─────────────────────────────────────────────────────────

def test_get_movie_by_slug_found():
    with patch("repository.movies_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_movie_by_slug("anora")
    assert result is not None
    assert result.title == "Anora"


def test_get_movie_by_slug_not_found():
    with patch("repository.movies_repository.get_worksheet", return_value=fake_worksheet(FAKE_ROWS)):
        result = get_movie_by_slug("nonexistent")
    assert result is None


# ── add_movie ─────────────────────────────────────────────────────────────────

def test_add_movie_appends_row():
    sheet = MagicMock()
    sheet.row_values.return_value = [
        "TITLE", "SLUG", "URL", "ADDED_BY", "DATE_ADDED", "POSTER",
        "STATUS", "NOMINATED_BY", "VOTED_BY", "WATCHED_DATE",
    ]
    movie = Movie(
        title="Heat",
        slug="heat-1995",
        url="https://letterboxd.com/film/heat-1995/",
        added_by="bjoubs",
        date_added="03/01/2025",
        poster="https://image.tmdb.org/heat.jpg",
        status="backlog",
        nominated_by="",
        voted_by="",
        watched_date="",
    )
    with patch("repository.movies_repository.get_worksheet", return_value=sheet):
        add_movie(movie)
    sheet.append_row.assert_called_once_with([
        "Heat",
        "heat-1995",
        "https://letterboxd.com/film/heat-1995/",
        "bjoubs",
        "03/01/2025",
        "https://image.tmdb.org/heat.jpg",
        "backlog",
        "",
        "",
        "",
    ])


def test_add_movie_appends_row_respects_header_order_on_sheet():
    sheet = MagicMock()
    sheet.row_values.return_value = [
        "SLUG", "TITLE", "STATUS", "URL", "ADDED_BY", "DATE_ADDED", "POSTER",
        "NOMINATED_BY", "VOTED_BY", "WATCHED_DATE",
    ]
    movie = Movie(
        title="Heat",
        slug="heat-1995",
        url="https://letterboxd.com/film/heat-1995/",
        added_by="bjoubs",
        date_added="03/01/2025",
        poster="https://image.tmdb.org/heat.jpg",
        status="backlog",
        nominated_by="",
        voted_by=[],
        watched_date="",
    )
    with patch("repository.movies_repository.get_worksheet", return_value=sheet):
        add_movie(movie)
    sheet.append_row.assert_called_once_with([
        "heat-1995",
        "Heat",
        "backlog",
        "https://letterboxd.com/film/heat-1995/",
        "bjoubs",
        "03/01/2025",
        "https://image.tmdb.org/heat.jpg",
        "",
        "",
        "",
    ])


# ── update_movie_fields ──────────────────────────────────────────────────────

def test_update_movie_fields_single_field():
    sheet = MagicMock()
    sheet.get_all_records.return_value = FAKE_ROWS
    sheet.row_values.return_value = [
        "TITLE", "SLUG", "URL", "ADDED_BY", "DATE_ADDED", "POSTER",
        "STATUS", "NOMINATED_BY", "VOTED_BY", "WATCHED_DATE",
    ]
    with patch("repository.movies_repository.get_worksheet", return_value=sheet):
        update_movie_fields("anora", status="selected")
    sheet.update_cell.assert_called_once_with(3, 7, "selected")


def test_update_movie_fields_multiple_fields():
    sheet = MagicMock()
    sheet.get_all_records.return_value = FAKE_ROWS
    sheet.row_values.return_value = [
        "TITLE", "SLUG", "URL", "ADDED_BY", "DATE_ADDED", "POSTER",
        "STATUS", "NOMINATED_BY", "VOTED_BY", "WATCHED_DATE",
    ]
    with patch("repository.movies_repository.get_worksheet", return_value=sheet):
        update_movie_fields("anora", status="watched", watched_date="03/01/2025")
    calls = sheet.update_cell.call_args_list
    assert call(3, 7, "watched") in calls
    assert call(3, 10, "03/01/2025") in calls


def test_update_movie_fields_voted_by():
    sheet = MagicMock()
    sheet.get_all_records.return_value = FAKE_ROWS
    sheet.row_values.return_value = [
        "TITLE", "SLUG", "URL", "ADDED_BY", "DATE_ADDED", "POSTER",
        "STATUS", "NOMINATED_BY", "VOTED_BY", "WATCHED_DATE",
    ]
    with patch("repository.movies_repository.get_worksheet", return_value=sheet):
        update_movie_fields("anora", voted_by="bjoubs, KingKrab")
    sheet.update_cell.assert_called_once_with(3, 9, "bjoubs, KingKrab")


# ── delete_movie ─────────────────────────────────────────────────────────────

def test_delete_movie_removes_row():
    sheet = MagicMock()
    sheet.get_all_records.return_value = FAKE_ROWS
    with patch("repository.movies_repository.get_worksheet", return_value=sheet):
        delete_movie("anora")
    sheet.delete_rows.assert_called_once_with(3)


def test_delete_movie_no_match():
    sheet = MagicMock()
    sheet.get_all_records.return_value = FAKE_ROWS
    with patch("repository.movies_repository.get_worksheet", return_value=sheet):
        delete_movie("nonexistent")
    sheet.delete_rows.assert_not_called()
