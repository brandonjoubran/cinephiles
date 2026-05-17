"""Shared HTTP helpers for Letterboxd, TMDB, and other outbound requests."""
import requests

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}
DEFAULT_TIMEOUT = 15


def get(url: str, **kwargs) -> requests.Response:
    """GET with shared browser-like headers and a default timeout."""
    kwargs.setdefault("headers", DEFAULT_HEADERS)
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    return requests.get(url, **kwargs)


def resolve_url(url: str) -> str:
    """Follow redirects (e.g. boxd.it) and return the final URL."""
    response = get(url, allow_redirects=True)
    response.raise_for_status()
    return response.url
