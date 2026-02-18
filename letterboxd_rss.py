"""
Letterboxd RSS feed integration.
Fetches user activity from https://letterboxd.com/<username>/rss/
and maps to the same film-log shape used by the rest of the app.
Much faster than scraping tag/diary pages.
"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
from cache import load_stats_cache, save_stats_cache
from db import get_film_logs_sheet

RSS_URL = "https://letterboxd.com/{username}/rss/"

# FilmLog columns: USERNAME, SLUG, TITLE, RATING, HAS_REVIEW, WORD_COUNT, REVIEW_LINK, WATCHED_DATE
FILM_LOGS_HEADERS = ("USERNAME", "SLUG", "TITLE", "RATING", "HAS_REVIEW", "WORD_COUNT", "REVIEW_LINK", "WATCHED_DATE")


def _row_get(row, *keys):
    """Get value from row trying multiple key casings (gspread keys = exact first row text)."""
    for k in keys:
        v = row.get(k)
        if v is not None and v != "":
            return v
    return None


def load_film_logs_by_user():
    """
    Load FilmLog sheet and return { username: { slug: film_data } }.
    Keys are normalized to lowercase so lookup is case-insensitive (Users sheet may differ from FilmLog).
    """
    out = {}
    try:
        sheet = get_film_logs_sheet()
        all_values = sheet.get_all_values()
    except Exception as e:
        print(f"   ⚠️ FilmLog load failed: {e}")
        return out
    if not all_values or len(all_values) < 2:
        print("   ⚠️ FilmLog sheet is empty or has only a header row")
        return out
    headers = [str(h).strip() for h in all_values[0]]
    # Column indices: USERNAME=0, SLUG=1, TITLE=2, RATING=3, HAS_REVIEW=4, WORD_COUNT=5, REVIEW_LINK=6, UPDATED_AT/WATCHED_DATE=7
    def col(name):
        for i, h in enumerate(headers):
            if h and name.upper() in (h.upper(), h.upper().replace(" ", "_")):
                return i
        return None
    idx_user = col("USERNAME") if col("USERNAME") is not None else 0
    idx_slug = col("SLUG") if col("SLUG") is not None else 1
    idx_title = col("TITLE") if col("TITLE") is not None else 2
    idx_rating = col("RATING") if col("RATING") is not None else 3
    idx_review = col("HAS_REVIEW") if col("HAS_REVIEW") is not None else 4
    idx_wc = col("WORD_COUNT") if col("WORD_COUNT") is not None else 5
    idx_link = col("REVIEW_LINK") if col("REVIEW_LINK") is not None else 6
    idx_date = col("UPDATED_AT") if col("UPDATED_AT") is not None else (col("WATCHED_DATE") if col("WATCHED_DATE") is not None else 7)
    for r in all_values[1:]:
        if len(r) <= max(idx_user, idx_slug):
            continue
        username = (r[idx_user] or "").strip()
        slug = (r[idx_slug] or "").strip()
        if not username or not slug:
            continue
        try:
            wc = int(r[idx_wc]) if idx_wc is not None and len(r) > idx_wc and r[idx_wc] not in (None, "") else 0
        except (TypeError, ValueError):
            wc = 0
        try:
            rating = float(r[idx_rating]) if idx_rating is not None and len(r) > idx_rating and r[idx_rating] not in (None, "") else None
        except (TypeError, ValueError):
            rating = None
        title = (r[idx_title] if idx_title is not None and len(r) > idx_title else None) or slug.replace("-", " ").title()
        has_review = (r[idx_review] if idx_review is not None and len(r) > idx_review else "") == "TRUE"
        review_link = (r[idx_link] if idx_link is not None and len(r) > idx_link else "") or ""
        watched_date = (r[idx_date] if idx_date is not None and len(r) > idx_date else "") or ""
        film_data = {
            "slug": slug,
            "title": title,
            "rating": rating,
            "has_review": has_review,
            "word_count": wc,
            "review_link": review_link,
            "url": review_link,
            "watched_date": watched_date,
        }
        # Normalize to lowercase so index() can match Users sheet (case-insensitive)
        key = username.lower()
        out.setdefault(key, {})[slug] = film_data
    total = sum(len(films) for films in out.values())
    print(f"   📋 FilmLog: loaded {len(all_values)-1} rows → {len(out)} users, {total} film entries (headers: {headers})")
    return out
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
# Letterboxd RSS uses custom namespaces; ElementTree may use full URI or local name
NS = {"lb": "http://letterboxd.com/ns/", "dc": "http://purl.org/dc/elements/1.1/"}


def _text(el):
    return (el.text or "").strip() if el is not None else ""


def _slug_from_link(link):
    """Extract film slug from item link: .../film/one-hour-photo/ -> one-hour-photo"""
    if not link:
        return None
    m = re.search(r"/film/([^/]+)/?", link)
    return m.group(1) if m else None


def _find_child(item, *names):
    """Find first direct child with tag ending in one of names (handles namespaced tags)."""
    for child in item:
        tag = child.tag
        local = tag.split("}")[-1] if "}" in tag else tag
        if local in names:
            return child
    return None


def _word_count_from_description(description_html):
    """Strip HTML and return word count of review text."""
    if not description_html:
        return 0
    # Remove img tag and any other tags, keep text
    text = re.sub(r"<[^>]+>", " ", description_html)
    text = re.sub(r"\s+", " ", text).strip()
    return len(text.split()) if text else 0


def fetch_rss(username):
    """Fetch raw RSS XML for a user. Returns response text or None."""
    url = RSS_URL.format(username=username)
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        print(f"   RSS fetch failed for {username}: {e}")
        return None


def parse_rss_item(item):
    """
    Parse one <item> into a film log dict compatible with build_stats/cache.
    Returns dict with: slug, title, rating, has_review, word_count, review_link, (url), watched_date.
    """
    link_el = _find_child(item, "link")
    link = _text(link_el) if link_el is not None else ""
    slug = _slug_from_link(link)
    if not slug:
        return None

    film_title_el = _find_child(item, "filmTitle")
    film_year_el = _find_child(item, "filmYear")
    title = _text(film_title_el) or ""
    year = _text(film_year_el)
    if year:
        title = f"{title} ({year})" if title else year

    rating_el = _find_child(item, "memberRating")
    rating_raw = _text(rating_el)
    try:
        rating = float(rating_raw) if rating_raw else None
    except ValueError:
        rating = None

    desc_el = _find_child(item, "description")
    description_html = ""
    if desc_el is not None:
        description_html = desc_el.text or ""
        if not description_html and list(desc_el):
            description_html = " ".join((e.text or "") for e in desc_el.iter() if e.text)
    word_count = _word_count_from_description(description_html)
    has_review = word_count > 0

    watched_date_el = _find_child(item, "watchedDate")
    watched_date = _text(watched_date_el) or ""

    return {
        "slug": slug,
        "title": title or slug.replace("-", " ").title(),
        "rating": rating,
        "has_review": has_review,
        "word_count": word_count,
        "review_link": link,
        "url": link,
        "watched_date": watched_date,
    }


def _local_name(tag):
    return tag.split("}")[-1] if tag and "}" in tag else (tag or "")


def parse_rss_feed(xml_text):
    """
    Parse RSS XML and return list of film log dicts (one per item).
    """
    if not xml_text:
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"   RSS parse error: {e}")
        return []
    # RSS 2.0: channel > item (handle default namespace)
    channel = root.find("channel")
    if channel is None:
        for child in root:
            if _local_name(child.tag) == "channel":
                channel = child
                break
        if channel is None:
            channel = root
    items = list(channel.findall("item"))
    if not items:
        for child in channel:
            if _local_name(child.tag) == "item":
                items.append(child)
    logs = []
    for item in items:
        entry = parse_rss_item(item)
        if entry:
            logs.append(entry)
    return logs


def get_films_from_rss(username, target_slugs=None):
    """
    Fetch RSS for username and return dict slug -> film_data.
    If target_slugs is set, only include those slugs (our group's selected films).
    Otherwise include all films from the feed.
    """
    xml_text = fetch_rss(username)
    if not xml_text:
        return {}
    logs = parse_rss_feed(xml_text)
    films = {log["slug"]: log for log in logs}
    if target_slugs is not None:
        target_set = set(target_slugs)
        films = {s: data for s, data in films.items() if s in target_set}
    return films


def get_all_user_logs(username, target_slugs, cache=None, _max_pages=2):
    """
    Get user film logs using RSS, merged with existing cache.
    Returns the same shape as scraper_optimized.get_all_user_logs:
    { username: { "films": { slug: film_data }, "stats": ... } }
    so that callers can use result[username]['films'].
    """
    try:
        cache = load_stats_cache(username)
    except Exception:
        cache = {}
    if not isinstance(cache, dict):
        cache = {}
    if username not in cache or not isinstance(cache[username], dict):
        cache[username] = {"films": {}, "stats": {}}
    cache[username].setdefault("films", {})
    cache[username].setdefault("stats", {})

    existing_films = cache[username]["films"]
    rss_films = get_films_from_rss(username, target_slugs=target_slugs)
    if rss_films:
        print(f"   📡 RSS: {username} — {len(rss_films)} films in selection")

    # Merge: RSS overwrites/adds for slugs we got from feed; keep existing for others
    merged = dict(existing_films)
    for slug, data in rss_films.items():
        merged[slug] = data

    cache[username]["films"] = merged
    save_stats_cache(username, cache)
    return cache


def refresh_film_for_all_users(movie_slug, usernames):
    """
    On movie complete: fetch each user's RSS for this film, persist to cache and FilmLog table.
    No Letterboxd scraping — RSS only.
    """
    try:
        film_logs_sheet = get_film_logs_sheet()
    except Exception as e:
        print(f"   ⚠️ FilmLog sheet unavailable: {e} (persisting to cache only)")
        film_logs_sheet = None
    for username in usernames:
        films = get_films_from_rss(username, target_slugs=[movie_slug])
        if not films:
            continue
        data = films[movie_slug]
        # Merge into user cache
        try:
            cache = load_stats_cache(username)
        except Exception:
            cache = {}
        if not isinstance(cache, dict) or username not in cache:
            cache = {username: {"films": {}, "stats": {}}}
        cache[username].setdefault("films", {})[movie_slug] = data
        save_stats_cache(username, cache)
        if film_logs_sheet:
            row = [
                username,
                data.get("slug", movie_slug),
                data.get("title", ""),
                data.get("rating") if data.get("rating") is not None else "",
                "TRUE" if data.get("has_review") else "FALSE",
                data.get("word_count", 0),
                data.get("review_link") or data.get("url") or "",
                datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            ]
            film_logs_sheet.append_row(row)
        print(f"   📡 RSS: {username} — {movie_slug} (cache + FilmLog)")
    print(f"   ✅ Refreshed {movie_slug} from RSS for all users")


def user_watched_film(username, movie_slug, cache=None):
    """
    Quick check: has this user watched this film?
    Uses cache first, then RSS fetch (filter by that slug) if not in cache.
    """
    try:
        cache = load_stats_cache(username) if cache is None else cache
    except Exception:
        cache = {}
    films = (cache.get(username) or {}).get("films") or {}
    if movie_slug in films:
        return True
    films_from_rss = get_films_from_rss(username, target_slugs=[movie_slug])
    if films_from_rss:
        cache.setdefault(username, {}).setdefault("films", {})[movie_slug] = list(films_from_rss.values())[0]
        save_stats_cache(username, cache)
        return True
    return False
