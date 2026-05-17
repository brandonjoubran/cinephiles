import pytest
from pydantic import ValidationError

from models.parsed_letterboxd_movie import ParsedLetterboxdMovie


def test_valid_parsed_movie():
    movie = ParsedLetterboxdMovie(
        title="Heat",
        slug="heat-1995",
        url="https://letterboxd.com/film/heat-1995/",
        poster="https://image.tmdb.org/poster.jpg",
    )
    assert movie.slug == "heat-1995"


def test_empty_slug_raises():
    with pytest.raises(ValidationError):
        ParsedLetterboxdMovie(title="Heat", slug="", url="https://letterboxd.com/film/heat/", poster="")
