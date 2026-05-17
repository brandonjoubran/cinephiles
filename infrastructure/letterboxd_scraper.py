"""
Scrape a Letterboxd film page into fields we store on the Movies sheet.

Flow (same idea as aaa-old add-movie):
  1. Resolve short links (boxd.it) → canonical URL
  2. Read slug from /film/{slug}/ in the URL
  3. Download HTML and parse with BeautifulSoup
  4. Title  ← usually <meta property="og:title"> (strip year)
  5. Poster ← usually <body data-tmdb-id="…"> + TMDB API, else JSON-LD image

If something breaks after a Letterboxd deploy, check in this order:
  - _fetch_soup          → network / blocked / login wall HTML
  - _slug_from_url       → URL shape changed (not /film/slug/)
  - _title_from_soup     → og:title or fallbacks missing
  - _poster_from_soup    → data-tmdb-id removed or TMDB key missing

Example:
  parse_letterboxd_film_url("https://letterboxd.com/film/hoppers/")
  → ParsedLetterboxdMovie(title="Hoppers", slug="hoppers", url="https://…", poster="https://image.tmdb.org/…")
"""
import json
import re

from bs4 import BeautifulSoup

from infrastructure import http
from infrastructure.tmdb import get_poster_url
from models.parsed_letterboxd_movie import ParsedLetterboxdMovie

# Canonical film URLs always contain /film/{slug}/ — used after redirect resolution.
# Example: "https://letterboxd.com/film/heat-1995/" → slug "heat-1995"
FILM_PATH_PATTERN = re.compile(r"/film/([^/]+)/?")


def parse_letterboxd_film_url(link: str) -> ParsedLetterboxdMovie:
    """
    Entry point: any Letterboxd film link in, parsed movie out.

    Accepts long URLs, boxd.it short links, or URLs with query params.
    Example:
        link = "https://boxd.it/abc123"
        → resolves to "https://letterboxd.com/film/sinners-2025/"
        → ParsedLetterboxdMovie(...)
    """
    full_url = http.resolve_url(link.strip())
    slug = _slug_from_url(full_url)
    soup = _fetch_soup(full_url)

    title = _title_from_soup(soup, slug)
    poster = _poster_from_soup(soup)

    return ParsedLetterboxdMovie(
        title=title,
        slug=slug,
        url=full_url,
        poster=poster,
    )


def _slug_from_url(full_url: str) -> str:
    """
    Pull the film slug from the resolved URL path (not from page HTML).

    Letterboxd film pages live at /film/{slug}/. If the user passes a profile
    or list URL, we fail here with a clear error.

    Examples:
        "https://letterboxd.com/film/hoppers/"     → "hoppers"
        "https://letterboxd.com/film/heat-1995/"   → "heat-1995"
        "https://letterboxd.com/bjoubs/"           → ValueError (no /film/ segment)
    """
    match = FILM_PATH_PATTERN.search(full_url)
    if not match:
        raise ValueError(
            f"Invalid Letterboxd film link — expected /film/{{slug}}/ in URL, got: {full_url}"
        )
    return match.group(1)


def _fetch_soup(url: str) -> BeautifulSoup:
    """
    Download the film page and return a BeautifulSoup tree.

    Uses infrastructure.http (shared User-Agent + timeout). If this step fails,
    the problem is network-level, not a moved CSS selector.

    Example:
        url = "https://letterboxd.com/film/hoppers/"
        → soup with <body data-tmdb-id="…">, <meta property="og:title" …>, etc.
    """
    response = http.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def _title_from_soup(soup: BeautifulSoup, slug: str) -> str:
    """
    Extract a display title for the Movies sheet.

    Primary source (stable for years): Open Graph meta tag.
      <meta property="og:title" content="Hoppers (2026)" />
    We strip the trailing "(YYYY)" so the sheet shows "Hoppers".

    Fallbacks if og:title is missing (Letterboxd redesign):
      1. <h1 class="headline-1 …"> on film pages
      2. JSON-LD "name" field (see _json_ld_blocks)

    Last resort: derive from slug ("heat-1995" → "Heat 1995").

    Examples:
        og:title "Heat (1995)"  → "Heat"
        og:title missing, h1 "Sinners" → "Sinners"
        everything missing, slug "dune-part-two" → "Dune Part Two"
    """
    title = _title_from_og_tag(soup)
    if title:
        return _strip_year_from_title(title)

    title = _title_from_headline(soup)
    if title:
        return _strip_year_from_title(title)

    title = _title_from_json_ld(soup)
    if title:
        return _strip_year_from_title(title)

    return slug.replace("-", " ").title()


def _title_from_og_tag(soup: BeautifulSoup) -> str | None:
    """Read <meta property="og:title" content="…">. Returns None if tag missing."""
    tag = soup.find("meta", property="og:title")
    if not tag:
        return None
    content = tag.get("content", "").strip()
    return content or None


def _title_from_headline(soup: BeautifulSoup) -> str | None:
    """
    Fallback: visible page heading on film pages.

    Example HTML:
        <h1 class="headline-1 primaryname">Hoppers</h1>
    """
    heading = soup.find("h1", class_=lambda value: value and "headline-1" in value)
    if not heading:
        heading = soup.find("h1")
    if not heading:
        return None
    text = heading.get_text(strip=True)
    return text or None


def _title_from_json_ld(soup: BeautifulSoup) -> str | None:
    """
    Fallback: structured data block often includes the film name.

    Example:
        {"@type": "Movie", "name": "Hoppers", …}
    """
    for block in _json_ld_blocks(soup):
        if not isinstance(block, dict):
            continue
        name = block.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return None


def _strip_year_from_title(title: str) -> str:
    """
    Remove a trailing release year from the title string.

    Examples:
        "Heat (1995)"   → "Heat"
        "Hoppers (2026)" → "Hoppers"
        "Heat"          → "Heat"  (unchanged)
    """
    return re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()


def _poster_from_soup(soup: BeautifulSoup) -> str:
    """
    Find a poster image URL for the POSTER column.

    Priority (matches old Flask app):
      1. <body data-tmdb-id="949"> → TMDB API → w500 image URL (best quality)
      2. JSON-LD "image" field (Letterboxd-hosted or TMDB URL string)
      3. "" if nothing found (movie still adds; poster column empty)

    If posters suddenly disappear, check:
      - body still has data-tmdb-id (inspect page source)
      - TMDB API_KEY in .env
      - JSON-LD still has "image"

    Example:
        body data-tmdb-id="949" + valid API key
        → "https://image.tmdb.org/t/p/w500/abc123.jpg"
    """
    tmdb_id = _tmdb_id_from_body(soup)
    if tmdb_id:
        poster = get_poster_url(tmdb_id)
        if poster:
            return poster

    poster = _poster_from_json_ld(soup)
    if poster:
        return poster

    return ""


def _tmdb_id_from_body(soup: BeautifulSoup) -> str | None:
    """
    Read TMDB movie id from the <body> tag.

    Letterboxd embeds this for their own TMDB integration:
        <body class="film" data-tmdb-id="949">

    Example: data-tmdb-id="949" → "949"
    """
    body = soup.find("body")
    if not body:
        return None
    tmdb_id = body.get("data-tmdb-id")
    if not tmdb_id:
        return None
    return str(tmdb_id).strip() or None


def _poster_from_json_ld(soup: BeautifulSoup) -> str:
    """
    Read poster/image URL from application/ld+json scripts.

    May be a string URL or a list; we take the first string that looks like a URL.

    Example:
        {"@type": "Movie", "image": "https://…"}
    """
    for block in _json_ld_blocks(soup):
        if not isinstance(block, dict):
            continue
        image = block.get("image")
        if isinstance(image, str) and image.startswith("http"):
            return image
        if isinstance(image, list):
            for item in image:
                if isinstance(item, str) and item.startswith("http"):
                    return item
    return ""


def _json_ld_blocks(soup: BeautifulSoup) -> list[dict]:
    """
    Yield all JSON-LD objects from <script type="application/ld+json"> tags.

    Letterboxd may ship one object or an @graph array; normalizing here keeps
    title/poster fallbacks in one place.

    Example shapes:
        {"@type": "Movie", "name": "Hoppers", "image": "https://…"}
        {"@graph": [{"@type": "Movie", …}, …]}
    """
    blocks: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict) and isinstance(data.get("@graph"), list):
            blocks.extend(item for item in data["@graph"] if isinstance(item, dict))
        elif isinstance(data, dict):
            blocks.append(data)
        elif isinstance(data, list):
            blocks.extend(item for item in data if isinstance(item, dict))

    return blocks
