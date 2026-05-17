"""Fetch movie poster URLs from TMDB."""
import requests

from config import TMDB_API_KEY
from infrastructure import http

TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{movie_id}"


def get_poster_url(tmdb_id: str) -> str:
    """Return a w500 poster URL for a TMDB movie id, or ``""`` if unavailable."""
    if not TMDB_API_KEY or not tmdb_id:
        return ""

    url = TMDB_MOVIE_URL.format(movie_id=tmdb_id)
    try:
        response = http.get(url, params={"api_key": TMDB_API_KEY})
        response.raise_for_status()
        poster_path = response.json().get("poster_path")
    except (requests.RequestException, ValueError, KeyError):
        return ""

    if not poster_path:
        return ""

    return f"https://image.tmdb.org/t/p/w500{poster_path}"
