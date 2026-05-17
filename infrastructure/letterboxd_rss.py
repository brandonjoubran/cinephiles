"""
Read club members' recent watches from Letterboxd RSS feeds.

Each feed lives at https://letterboxd.com/<username>/rss/
"""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests

from infrastructure import http

RSS_URL = "https://letterboxd.com/{username}/rss/"


@dataclass
class LetterboxdFilm:
    """One film entry parsed from a user's RSS feed."""

    slug: str
    title: str
    rating: float | None
    has_review: bool
    word_count: int
    review_link: str
    watched_date: str


def fetch_user_films(username: str, slugs: list[str] | None = None) -> dict[str, LetterboxdFilm]:
    """Download a user's RSS feed and return films keyed by slug.

    Pass ``slugs`` to only keep films the club cares about (faster, less noise).
    Returns an empty dict when the feed cannot be fetched or parsed.
    """
    xml_text = _download_feed(username)
    if not xml_text:
        return {}

    films = {film.slug: film for film in _parse_feed(xml_text)}
    if slugs is None:
        return films
    wanted = set(slugs)
    return {slug: film for slug, film in films.items() if slug in wanted}


def _download_feed(username: str) -> str | None:
    """GET the raw RSS XML for one Letterboxd user."""
    url = RSS_URL.format(username=username)
    try:
        response = http.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def _parse_feed(xml_text: str) -> list[LetterboxdFilm]:
    """Parse RSS XML into a list of films (newest items first, as in the feed)."""
    if not xml_text:
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    channel = _find_channel(root)
    items = _find_items(channel)
    films = []
    for item in items:
        film = _parse_item(item)
        if film:
            films.append(film)
    return films


def _parse_item(item) -> LetterboxdFilm | None:
    """Parse a single RSS <item> into a LetterboxdFilm."""
    link = _element_text(_find_child(item, "link"))
    slug = _slug_from_url(link)
    if not slug:
        return None

    title = _element_text(_find_child(item, "filmTitle"))
    year = _element_text(_find_child(item, "filmYear"))
    if year:
        title = f"{title} ({year})" if title else year

    rating = _parse_rating(_element_text(_find_child(item, "memberRating")))
    description = _description_html(_find_child(item, "description"))
    word_count = _word_count(description)

    return LetterboxdFilm(
        slug=slug,
        title=title or slug.replace("-", " ").title(),
        rating=rating,
        has_review=word_count > 0,
        word_count=word_count,
        review_link=link,
        watched_date=_element_text(_find_child(item, "watchedDate")),
    )


def _find_channel(root):
    channel = root.find("channel")
    if channel is not None:
        return channel
    for child in root:
        if _tag_name(child.tag) == "channel":
            return child
    return root


def _find_items(channel) -> list:
    items = list(channel.findall("item"))
    if items:
        return items
    return [child for child in channel if _tag_name(child.tag) == "item"]


def _find_child(parent, *local_names: str):
    """Find a direct child by tag name, ignoring XML namespaces."""
    for child in parent:
        if _tag_name(child.tag) in local_names:
            return child
    return None


def _tag_name(tag: str) -> str:
    return tag.split("}")[-1] if tag and "}" in tag else (tag or "")


def _element_text(element) -> str:
    return (element.text or "").strip() if element is not None else ""


def _slug_from_url(url: str) -> str | None:
    """Extract the film slug from a Letterboxd film URL."""
    if not url:
        return None
    match = re.search(r"/film/([^/]+)/?", url)
    return match.group(1) if match else None


def _parse_rating(raw: str) -> float | None:
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _description_html(element) -> str:
    if element is None:
        return ""
    text = element.text or ""
    if not text and list(element):
        text = " ".join(part.text or "" for part in element.iter() if part.text)
    return text


def _word_count(html: str) -> int:
    """Count words in review text after stripping HTML tags."""
    if not html:
        return 0
    plain = re.sub(r"<[^>]+>", " ", html)
    plain = re.sub(r"\s+", " ", plain).strip()
    return len(plain.split()) if plain else 0
