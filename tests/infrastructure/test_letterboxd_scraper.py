from unittest.mock import MagicMock, patch

import pytest

from infrastructure.letterboxd_scraper import parse_letterboxd_film_url
from models.parsed_letterboxd_movie import ParsedLetterboxdMovie

SAMPLE_HTML = """
<html>
<head>
<meta property="og:title" content="Heat (1995)" />
</head>
<body data-tmdb-id="949">
<script type="application/ld+json">{"name":"Heat","image":"https://letterboxd.com/poster-fallback.jpg"}</script>
</body>
</html>
"""


def test_parse_letterboxd_film_url_from_long_link():
    page_response = MagicMock()
    page_response.text = SAMPLE_HTML
    page_response.raise_for_status = MagicMock()

    with (
        patch("infrastructure.letterboxd_scraper.http.resolve_url", return_value="https://letterboxd.com/film/heat-1995/"),
        patch("infrastructure.letterboxd_scraper.http.get", return_value=page_response),
        patch("infrastructure.letterboxd_scraper.get_poster_url", return_value="https://image.tmdb.org/t/p/w500/poster.jpg"),
    ):
        result = parse_letterboxd_film_url("https://letterboxd.com/film/heat-1995/")

    assert result == ParsedLetterboxdMovie(
        title="Heat",
        slug="heat-1995",
        url="https://letterboxd.com/film/heat-1995/",
        poster="https://image.tmdb.org/t/p/w500/poster.jpg",
    )


def test_parse_letterboxd_film_url_rejects_non_film_link():
    with patch("infrastructure.letterboxd_scraper.http.resolve_url", return_value="https://letterboxd.com/bjoubs/"):
        with pytest.raises(ValueError, match="Invalid Letterboxd film link"):
            parse_letterboxd_film_url("https://letterboxd.com/bjoubs/")
