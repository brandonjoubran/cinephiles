from unittest.mock import patch

import pytest
from fastapi import HTTPException

from models.parsed_letterboxd_movie import ParsedLetterboxdMovie
from service.movies_service import add_movie_from_letterboxd_link


def test_add_movie_from_letterboxd_link_delegates_to_add_movie():
    parsed = ParsedLetterboxdMovie(
        title="Heat",
        slug="heat-1995",
        url="https://letterboxd.com/film/heat-1995/",
        poster="https://image.tmdb.org/poster.jpg",
    )
    with (
        patch("service.movies_service.parse_letterboxd_film_url", return_value=parsed),
        patch("service.movies_service.add_movie") as mock_add,
    ):
        add_movie_from_letterboxd_link("https://boxd.it/abc", "bjoubs")

    mock_add.assert_called_once_with(
        "Heat",
        "heat-1995",
        "https://letterboxd.com/film/heat-1995/",
        "bjoubs",
        "https://image.tmdb.org/poster.jpg",
    )


def test_add_movie_from_letterboxd_link_invalid_url_returns_400():
    with patch("service.movies_service.parse_letterboxd_film_url", side_effect=ValueError("bad link")):
        with pytest.raises(HTTPException) as exc:
            add_movie_from_letterboxd_link("not-a-url", "bjoubs")
    assert exc.value.status_code == 400
