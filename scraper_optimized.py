import json
import re
import threading
import time
from bs4 import BeautifulSoup
import requests
from utils import (
    slugify, extract_full_date, parse_rating, resolve_letterboxd_url, fetch_page, shared_playwright_browser,
    run_playwright_in_thread, DEFAULT_BROWSER_HEADERS,
    _playwright_headless, _chromium_launch_args, _apply_playwright_context_options,
)
from cache import *
from persistence import load_user_films, save_user_films, load_all_users_films
from film_log_sheet import sync_user_films_to_sheet

_warm_lock = threading.Lock()

def check_user_has_tag(username, tag_name="onlycinephiles"):
    """
    Check if a user has a specific tag on their Letterboxd profile.
    Returns True if tag exists and has movies, False otherwise.
    """
    url = f"https://letterboxd.com/{username}/tag/{tag_name}/films/"
    # Use default browser-like headers from utils; avoid old User-Agents (Cloudflare blocks them).

    try:
        time.sleep(0.3)
        resp = fetch_page(url)
        print(f"Checking tag for {username}: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Tag check failed for {username} at {url}")
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            film_divs = soup.select('div[data-item-slug]')
            return len(film_divs) > 0, soup
        return False, None
    except Exception as e:
        print(f"Error checking tag for {username}: {e}")
        return False, None

def get_film_containers_from_tag_page(soup):
    return soup.select('li.griditem')

def get_slug_from_film_container(film_container):
    slug_element = film_container.select('div.react-component')[0]
    slug = slug_element.attrs.get('data-item-slug')
    title = slug_element.attrs.get('data-item-name')
    return slug, title

def get_rating_element_from_film_container(film_container):
    rating_element = film_container.select_one('p.poster-viewingdata')
    return rating_element

def get_rating_from_film_container(film_rating_element):
    # print(film_rating_element)
    # print(film_rating_element.attrs.get('poster-viewingdata'))
    # print(film_rating_element.select('span.rating'))
    rating_class = film_rating_element.select('span.rating')[0].text.strip()
    rating = parse_rating(rating_class)
    return rating

def get_review_element(rating_element):
    review_element= rating_element.select('a.review-micro')[0]
    return review_element

def get_review_link(review_element):
    review_href = (review_element.get('href') or '').lstrip('/')
    print(f"   Found review: /{review_href}")
    review_link = f"https://letterboxd.com/{review_href}"
    return review_link


def get_slug_to_film_url_from_tag_page(username, tag_name="onlycinephiles"):
    """
    Fetch the user's tag page and return (slug_to_url, ok).
    slug_to_url: dict slug -> full film page URL.
    ok: True if we got a valid response (200), False on 403/timeout/exception.
    When ok is False we know the tag page failed; when ok is True but slug_to_url is {}
    we got 200 but parsed 0 films (could be empty tag or page not ready - don't zero out).
    """
    url = f"https://letterboxd.com/{username}/tag/{tag_name}/films/"
    slug_to_url = {}
    try:
        time.sleep(0.3)
        resp = fetch_page(url)
        if resp.status_code != 200:
            return {}, False
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"   [tag page] Failed to fetch {url}: {e}")
        return {}, False
    for film_container in soup.select("li.griditem"):
        try:
            slug_el = film_container.select_one("div[data-item-slug]")
            if not slug_el:
                continue
            slug = slug_el.attrs.get("data-item-slug")
            if not slug:
                continue
            # Prefer the review link (points to the correct viewing, e.g. /username/film/slug/1/ for rewatch)
            rating_el = film_container.select_one("p.poster-viewingdata")
            review_anchor = rating_el.select_one("a.review-micro") if rating_el else None
            if review_anchor and review_anchor.get("href"):
                href = (review_anchor.get("href") or "").lstrip("/")
                film_url = f"https://letterboxd.com/{href}" if href and not href.startswith("http") else href
                slug_to_url[slug] = film_url.rstrip("/") + "/"
            else:
                # No review; use any link in the container to this film (poster link may be .../slug/1/)
                film_anchor = film_container.select_one(f'a[href*="/film/{slug}"]')
                if film_anchor and film_anchor.get("href"):
                    href = (film_anchor.get("href") or "").lstrip("/")
                    film_url = f"https://letterboxd.com/{href}" if href and not href.startswith("http") else href
                    slug_to_url[slug] = film_url.rstrip("/") + "/"
                else:
                    slug_to_url[slug] = f"https://letterboxd.com/{username}/film/{slug}/"
        except (IndexError, KeyError, TypeError):
            continue
    return slug_to_url, True

def get_review_paragraphs(review_element, slug, headers, review_link):
    print(f"   Review link: {review_link}")
    review_html = fetch_page(review_link, headers=headers)
    review_soup = BeautifulSoup(review_html.text, "html.parser")
    review_element = review_soup.select_one('div.js-review-body')
    review_paragraphs = review_element.select('p')
    return review_paragraphs

def get_word_count(review_paragraphs):
    word_count = 0
    for p in review_paragraphs:
        word_count += len(p.get_text(strip=True).split())
        # print(f"   Review paragraph: {p.get_text(strip=True)}")
    print(f"   Total word count: {word_count}")
    return word_count

def trim(logs, target_slugs, cache, username):
    user_cache = cache[username] if username in cache else {}
    user_film_cache = user_cache.get("films", {})
    user_film_cache_keys = set(user_film_cache.keys())
    new_slugs = []
    for target_slug in target_slugs:
        if target_slug in user_film_cache_keys:
            print(f"   Found cached data for {target_slug}")
            logs.append(user_film_cache[target_slug])
        else:
            new_slugs.append(target_slug)
    print(f"   New slugs to fetch: {new_slugs}")
    return logs, new_slugs

def is_slug_in_cache(username, slug, cache):
    return cache.get(username, {}).get("films", {}).get(slug)

def scrape_from_tag_page(soup, username, target_slugs, tag_name="onlycinephiles", cache=None):
    """
    Scrape movie data from a user's tag page.
    This is MUCH faster than scraping the diary.
    
    Process:
    1. Load tag page (e.g., /bjoubs/tag/onlycinephiles/films/)
    2. Extract all film slugs and ratings from poster grid
    3. For each film that has a review, fetch individual film page to get:
       - Watch date
       - Review word count
    """
    cache = load_stats_cache(username)
    print(f"🏷️ Scraping {username} from tag page...")
    start_time = time.time()
    
    logs = []
    target_slugs = set(target_slugs)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # # The tag page shows all tagged films
    # url = f"https://letterboxd.com/{username}/tag/{tag_name}/films/"
    
    # # try:
    # time.sleep(0.3)
    # resp = requests.get(url, headers=headers)
    
    # if resp.status_code != 200:
    #     print(f"❌ Failed to fetch tag page (status {resp.status_code})")
    #     return []
    
    # soup = BeautifulSoup(resp.text, "html.parser")

    logs, target_slugs = trim(logs, target_slugs, cache, username)
    print(f"   Target slugs after trimming: {target_slugs}")
    if target_slugs == []:
        print(f"   All target slugs found in cache")
        return logs

    # Find all containers on the tag page
    film_containers = get_film_containers_from_tag_page(soup)
    print(f"   Found {len(film_containers)} films with tag '{tag_name}'")
    new_data = {}
    for film_container in film_containers:
        # Extract the slug from data-item-slug attribute
        slug, title = get_slug_from_film_container(film_container)
        print(f"slug: {slug} title: {title}")

        # Only process movies we care about
        print(f"   Checking slug: {slug} not in {target_slugs}: {slug not in target_slugs}")
        if slug not in target_slugs:
            continue
        
        print(f"   Processing: {slug}")
        film_rating_element = get_rating_element_from_film_container(film_container)
        film_rating = get_rating_from_film_container(film_rating_element)
        print(f"   Found rating: {film_rating}")
        review_element = get_review_element(film_rating_element)
        word_count = 0
        if review_element:
            review_link = get_review_link(review_element)
            review_paragraphs = get_review_paragraphs(review_element, slug, headers, review_link)
            word_count = get_word_count(review_paragraphs)
            
            logs.append({
                'title': title,
                'slug': slug,
                'rating': film_rating,
                'has_review': True if review_element else False,
                'word_count': word_count,
                'review_link': review_link
            })

            cache.setdefault(username, {}).setdefault("films", {})[slug] = logs[-1]
            new_data[slug] = logs[-1]

    elapsed = time.time() - start_time
    print(f"✅ Tag scraping completed in {elapsed:.2f}s - found {len(logs)} movies")
    save_stats_cache(username, cache)
    # update_film_cache(username, new_data)
    return cache
        
    # except Exception as e:
    #     print(f"❌ Error scraping tag page: {e}")
    #     return []


def scrape_from_diary(username, target_slugs, cache=None, max_pages=2):
    """
    Fallback method: Scrape from user's diary.
    This is slower but works for users who don't use tags.
    """
    print(f"📖 Scraping {username} from diary (slower method)...")
    start_time = time.time()
    
    logs = []
    target_slugs = set(target_slugs)
    cache = load_stats_cache(username)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    logs, target_slugs = trim(logs, target_slugs, cache, username)
    
    if target_slugs == set():
        print(f"   All target slugs found in cache")
        return logs
    found_slugs = set()

    for page in range(1, max_pages + 1):
        url = f'https://letterboxd.com/{username}/films/diary/page/{page}/'
        
        try:
            resp = fetch_page(url, headers=headers)
        except requests.exceptions.RequestException as e:
            print(f"   Page {page}: Request failed - {e}")
            break

        if resp.status_code == 429:
            print(f"   ⚠️ Rate limited on page {page}")
            time.sleep(5)
            continue

        if resp.status_code != 200:
            print(f"   Page {page}: Failed (status {resp.status_code})")
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        rows = soup.select('tr.diary-entry-row')
        
        if not rows:
            print(f"   Page {page}: No more entries")
            break

        for row in rows:
            poster = row.select_one('div[data-item-slug]')
            if not poster:
                continue

            slug = slugify(poster['data-item-slug'])
            
            if slug not in target_slugs:
                continue

            found_slugs.add(slug)

            full_title_element = row.select_one("div.react-component.figure")
            title = full_title_element.attrs.get('data-item-full-display-name', '')
            # Extract title and link
            h2_tag = row.select_one('h2.name.-primary.prettify')
            title_tag = h2_tag.find('a') if h2_tag else None
            # title = title_tag.text.strip() if title_tag else "NA"
            link = f"https://letterboxd.com{title_tag['href']}" if title_tag else ''

            # Extract date
            date_tag = row.select_one('td.td-day a')
            date = extract_full_date(date_tag['href']) if date_tag and date_tag.has_attr('href') else 'Unknown date'
            
            # Extract rating
            rating_tag = row.select_one('div.hide-for-owner span.rating')
            rating_text = rating_tag.text.strip() if rating_tag else ''
            rating = parse_rating(rating_text)
            
            # Check for review
            has_review = row.select_one('a.icon-review') is not None

            # Count review words
            # cache_key = f"{username}_{slug}"
            # if has_review and cache_key in cache:
            #     word_count = cache[cache_key]
            if has_review:
                time.sleep(0.5)
                word_count = count_review_words(link, headers)
                # cache[cache_key] = word_count
            else:
                word_count = 0

            logs.append({
                'slug': slug,
                'title': title,
                'date': date,
                'rating': rating,
                'rating_str': rating_text,
                'url': link,
                'has_review': has_review,
                'word_count': word_count
            })
            cache.setdefault(username, {}).setdefault("films", {})[slug] = logs[-1]

        # Early exit if we found everything
        if found_slugs == target_slugs:
            print(f"   ✅ Found all target movies, exiting early")
            break

        time.sleep(0.5)

    elapsed = time.time() - start_time
    print(f"✅ Diary scraping completed in {elapsed:.2f}s - found {len(logs)} movies")
    save_stats_cache(username, cache)
    return cache


def get_all_user_logs(username, target_slugs, cache=None, max_pages=2):
    """
    MAIN FUNCTION: Intelligently scrape user's movie logs.
    
    Strategy:
    1. Check if user has 'onlycinephiles' tag
    2. If yes: Scrape from tag page (FAST)
    3. If no: Fall back to diary scraping (SLOW)
    
    This gives us the best of both worlds!
    """
    print(f"\n{'='*60}")
    print(f"🎬 Fetching logs for {username}")
    print(f"{'='*60}")

    cache = cache or {}

    # One Playwright browser for this user's scrape to avoid 30+ launches and worker timeout.
    with shared_playwright_browser():
        # Check if user uses the tag
        has_tag, soup = check_user_has_tag(username, "onlycinephiles")
        if has_tag:
            result = scrape_from_tag_page(soup, username, target_slugs, "onlycinephiles", cache)
        else:
            print(f"⚠️ User doesn't use 'onlycinephiles' tag, falling back to diary")
            result = scrape_from_diary(username, target_slugs, cache, max_pages)

    # Callers expect get_all_user_logs(username, ...)[username]['films'] – always return that shape.
    # When scraping fails (e.g. 403) or returns empty, result may be {} or a list; normalize it.
    if isinstance(result, list):
        films = {log["slug"]: log for log in result} if result else {}
        result = {username: {"films": films}}
    elif not isinstance(result, dict) or username not in result:
        result = {username: {"films": {}}}
    else:
        result[username].setdefault("films", {})

    # Persist so future loads can use film-page-only refresh.
    save_user_films(username, result)
    sync_user_films_to_sheet(username, result[username]["films"])
    print(f"{'='*60}\n")
    return result


def count_review_words(url, headers):
    """Count words in a review from a film page."""
    try:
        time.sleep(0.5)
        resp = fetch_page(url, headers=headers)
        
        if resp.status_code != 200:
            return 0
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        review_box = soup.select_one('div.js-review-body')
        
        if review_box:
            paragraphs = review_box.find_all('p')
            review_text = " ".join(p.get_text(separator=' ', strip=True) for p in paragraphs)
            return len(review_text.split())
            
    except Exception as e:
        print(f"   Error counting review words: {e}")
    
    return 0


def parse_film_page(html, url, slug):
    """
    Parse a user's film page (letterboxd.com/username/film/slug/).
    Returns a film dict for our cache: title, slug, rating, has_review, word_count, review_link, url.
    Returns None if the page doesn't look like a valid viewing (e.g. still a challenge page).
    """
    low = (html or "").lower()
    if "just a moment" in low or "attention required" in low or "cf-browser-verification" in low:
        return None
    soup = BeautifulSoup(html, "html.parser")
    review_link = url.rstrip("/")
    review_box = soup.select_one("div.js-review-body")
    has_review = review_box is not None
    word_count = 0
    if review_box:
        paragraphs = review_box.find_all("p")
        review_text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
        word_count = len(review_text.split())
    rating = None
    rating_el = soup.select_one("span.rating") or soup.select_one("[class*='rating']")
    if rating_el:
        rating = parse_rating(rating_el.get_text(strip=True))
    # Prefer h1 (film name only); og:title is the full page title e.g. "A ★★★★★ review of City of God (2002) (5.0⭐)"
    title_el = soup.select_one("h1.headline-1") or soup.select_one("meta[property='og:title']")
    if title_el:
        if title_el.name == "meta":
            raw = title_el.get("content", "").strip()
            # Strip "A ... review of " and " by ..." / " • " so stats show film name only
            for prefix in ("A ", "An "):
                if raw.lower().startswith(prefix.lower()) and " review of " in raw:
                    raw = raw.split(" review of ", 1)[-1]
            if " by " in raw:
                raw = raw.split(" by ")[0].strip()
            if " • " in raw:
                raw = raw.split(" • ")[0].strip()
            title = raw.strip() or slug.replace("-", " ").title()
        else:
            title = title_el.get_text(strip=True)
    else:
        title = slug.replace("-", " ").title()
    if not title:
        title = slug.replace("-", " ").title()
    return {
        "slug": slug,
        "title": title,
        "rating": rating,
        "has_review": has_review,
        "word_count": word_count,
        "review_link": review_link,
        "url": review_link,
    }


def fetch_film_page_result(username, slug, film_url=None):
    """
    Fetch one film page. Uses film_url if provided (e.g. from tag page for rewatches: .../film/slug/1/);
    otherwise letterboxd.com/<username>/film/<slug>/.
    Returns None if 404 (not watched) or error; else returns film dict from parse_film_page.
    """
    url = film_url or f"https://letterboxd.com/{username}/film/{slug}/"
    try:
        time.sleep(0.3)
        resp = fetch_page(url)
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            return None
        return parse_film_page(resp.text, resp.url, slug)
    except Exception as e:
        print(f"   Film page fetch failed for {username}/{slug}: {e}")
        return None


def _refresh_one_user_in_one_browser(username, target_slugs, existing_films, tag_name="onlycinephiles"):
    """
    Run in run_playwright_in_thread: ONE browser, ONE tab reused for tag + all film pages.
    Returns (films_dict, tag_ok). tag_ok=False means tag page failed (zero user).
    """
    from playwright.sync_api import sync_playwright
    user_agent = DEFAULT_BROWSER_HEADERS["User-Agent"]
    films = dict(existing_films)
    target_slugs = set(target_slugs)
    to_fetch = [s for s in target_slugs if s not in films]
    if not to_fetch:
        return (films, True)
    tag_url = f"https://letterboxd.com/{username}/tag/{tag_name}/films/"
    context = None
    browser = None
    pw = None
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(
            headless=_playwright_headless(),
            args=_chromium_launch_args(),
        )
        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            timezone_id="America/New_York",
        )
        _apply_playwright_context_options(context, user_agent)
        page = context.new_page()
        print("[refresh] One browser, one tab (reused for all URLs)")
        # Longer timeout for first load (Cloudflare / slow network); don't zero user on timeout
        page.goto(tag_url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(6000)
        try:
            page.wait_for_selector("div[data-item-slug]", timeout=15000)
        except Exception:
            pass
        html = page.content()
        slug_to_url = _parse_tag_page_html(html, username, tag_name)
        # Only zero when we got a definite challenge/block page; timeout/error = keep existing data
        if (not html or "just a moment" in (html or "").lower() or
                "attention required" in (html or "").lower() or "cf-browser-verification" in (html or "").lower()):
            return ({}, False)
        if not slug_to_url:
            return (films, True)
        to_fetch = [s for s in to_fetch if s in slug_to_url]
        for slug in to_fetch:
            film_url = slug_to_url[slug]
            page.goto(film_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)
            try:
                page.wait_for_selector("h1.headline-1", timeout=15000)
            except Exception:
                pass
            html = page.content()
            result = parse_film_page(html, film_url, slug)
            if result:
                films[slug] = result
                print(f"   Cached: {slug} (rating={result.get('rating')}, {result.get('word_count', 0)} words)")
        page.close()
        return (films, True)
    except Exception as e:
        print(f"   [refresh] Error (keeping existing data): {e}")
        # Timeout or other error: don't zero the user, keep existing films
        return (films, True)
    finally:
        try:
            if context:
                context.close()
            if browser:
                browser.close()
            if pw:
                pw.stop()
        except Exception:
            pass
        print("[refresh] Browser closed")


def get_all_user_logs_from_film_pages(username, target_slugs, use_persistence=True):
    """
    Tag page is required. Uses one browser, one tab (same as warm) when use_one_browser=True.
    If the tag page isn't available, zero out this user's stats.
    """
    if use_persistence:
        data = load_user_films(username)
    else:
        data = {username: {"films": {}, "stats": {}}}
    films = data[username]["films"]
    existing_films = dict(films)
    with _warm_lock:
        films_dict, tag_ok = run_playwright_in_thread(
            _refresh_one_user_in_one_browser, username, target_slugs, existing_films
        )
    if not tag_ok:
        print(f"   [tag page] Unavailable for {username}; zeroing stats")
        data[username]["films"] = {}
        data[username]["stats"] = {}
        if use_persistence:
            save_user_films(username, data)
            sync_user_films_to_sheet(username, {})
        save_stats_cache(username, data)
        return {username: {"films": {}, "stats": {}}}
    data[username]["films"] = films_dict
    if use_persistence:
        save_user_films(username, data)
        sync_user_films_to_sheet(username, films_dict)
    save_stats_cache(username, data)
    return {username: {"films": films_dict}}


def _parse_tag_page_html(html, username, tag_name="onlycinephiles"):
    """Parse tag page HTML (from Playwright) into slug -> film URL dict. Same logic as get_slug_to_film_url_from_tag_page."""
    slug_to_url = {}
    if not html or "just a moment" in (html or "").lower() or "attention required" in (html or "").lower():
        return slug_to_url
    soup = BeautifulSoup(html, "html.parser")
    for film_container in soup.select("li.griditem"):
        try:
            slug_el = film_container.select_one("div[data-item-slug]")
            if not slug_el:
                continue
            slug = slug_el.attrs.get("data-item-slug")
            if not slug:
                continue
            rating_el = film_container.select_one("p.poster-viewingdata")
            review_anchor = rating_el.select_one("a.review-micro") if rating_el else None
            if review_anchor and review_anchor.get("href"):
                href = (review_anchor.get("href") or "").lstrip("/")
                film_url = f"https://letterboxd.com/{href}" if href and not href.startswith("http") else href
                slug_to_url[slug] = film_url.rstrip("/") + "/"
            else:
                film_anchor = film_container.select_one(f'a[href*="/film/{slug}"]')
                if film_anchor and film_anchor.get("href"):
                    href = (film_anchor.get("href") or "").lstrip("/")
                    film_url = f"https://letterboxd.com/{href}" if href and not href.startswith("http") else href
                    slug_to_url[slug] = film_url.rstrip("/") + "/"
                else:
                    slug_to_url[slug] = f"https://letterboxd.com/{username}/film/{slug}/"
        except (IndexError, KeyError, TypeError):
            continue
    return slug_to_url


def _warm_all_users_in_one_browser(usernames, new_slug, tag_name="onlycinephiles"):
    """
    One browser, one tab (reused). Single launch for entire run.
    For each user: goto tag page → parse links → goto film page if needed → parse. Same tab for all.
    Returns list of (username, slug_to_url, tag_ok, film_result).
    """
    from playwright.sync_api import sync_playwright
    user_agent = DEFAULT_BROWSER_HEADERS["User-Agent"]
    results = []
    context = None
    browser = None
    pw = None
    n = len(usernames)
    print(f"[warm] Starting single browser for {n} users (one tab, reuse for all URLs)")
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(
            headless=_playwright_headless(),
            args=_chromium_launch_args(),
        )
        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            timezone_id="America/New_York",
        )
        _apply_playwright_context_options(context, user_agent)
        page = context.new_page()
        print("[warm] Browser launched once — reusing same tab for all navigations")
        for idx, username in enumerate(usernames):
            try:
                tag_url = f"https://letterboxd.com/{username}/tag/{tag_name}/films/"
                # domcontentloaded = don't wait for all images (Letterboxd has many posters); then wait for grid
                page.goto(tag_url, wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(4000)
                try:
                    page.wait_for_selector("div[data-item-slug]", timeout=35000)  # grid is JS-rendered
                except Exception:
                    pass
                html = page.content()
                slug_to_url = _parse_tag_page_html(html, username, tag_name)
                if (not html or "just a moment" in (html or "").lower() or
                        "attention required" in (html or "").lower() or
                        "cf-browser-verification" in (html or "").lower()):
                    results.append((username, {}, False, None))
                    continue
                if not slug_to_url:
                    results.append((username, slug_to_url, True, None))
                    continue
                if new_slug not in slug_to_url:
                    results.append((username, slug_to_url, True, None))
                    continue
                film_url = slug_to_url[new_slug]
                page.goto(film_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(4000)
                try:
                    page.wait_for_selector("h1.headline-1", timeout=20000)
                except Exception:
                    pass
                html = page.content()
                result = parse_film_page(html, film_url, new_slug)
                results.append((username, slug_to_url, True, result))
            except Exception as e:
                print(f"   [warm] Error for {username} (keeping existing data): {e}")
                # Timeout/error: don't zero this user
                results.append((username, {}, True, None))
        page.close()
    finally:
        try:
            if context:
                context.close()
            if browser:
                browser.close()
            if pw:
                pw.stop()
        except Exception:
            pass
        print("[warm] Browser closed")
    return results


def warm_film_data_for_new_slug(usernames, new_slug):
    """
    After a meeting is marked complete, warm cache/persistence for the new slug.
    One browser, one tab reused: tag page → parse links → film page → parse, per user. Minimal and fast.
    """
    if not usernames or not new_slug:
        return
    users_to_warm = [
        u for u in usernames
        if not load_user_films(u).get(u, {}).get("films", {}).get(new_slug)
    ]
    if not users_to_warm:
        return
    print(f"[warm] Updating cache for new slug {new_slug} ({len(users_to_warm)} users) — one browser, one tab reused")
    with _warm_lock:
        results = run_playwright_in_thread(_warm_all_users_in_one_browser, users_to_warm, new_slug)
    if not results:
        return
    for username, slug_to_url, tag_ok, film_result in results:
        if not tag_ok:
            print(f"   [tag page] Unavailable for {username}; zeroing stats")
            data = {username: {"films": {}, "stats": {}}}
            save_user_films(username, data)
            sync_user_films_to_sheet(username, {})
            save_stats_cache(username, data)
            continue
        if not slug_to_url or new_slug not in slug_to_url:
            continue
        if film_result is None:
            continue
        data = load_user_films(username)
        data[username].setdefault("films", {})[new_slug] = film_result
        save_user_films(username, data)
        sync_user_films_to_sheet(username, data[username]["films"])
        save_stats_cache(username, data)
        print(f"   {username}: {new_slug} (rating={film_result.get('rating')}, {film_result.get('word_count', 0)} words)")


def user_watched_last_film(username, movie_slug):
    """
    Quick check: Did user watch a specific movie?
    Uses tag page for fast lookup.
    """
    url = f"https://letterboxd.com/{username}/tag/onlycinephiles/films/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        time.sleep(0.3)
        resp = fetch_page(url, headers=headers)
        
        if resp.status_code != 200:
            return False
        
        soup = BeautifulSoup(resp.text, "html.parser")
        film_divs = soup.select('div[data-item-slug]')
        
        for div in film_divs:
            if div['data-item-slug'] == movie_slug:
                return True
        
        return False
        
    except Exception as e:
        print(f"Error checking if {username} watched {movie_slug}: {e}")
        return 
    
def user_watched_last_film_optimized(username, movie_slug):
    """
    Quick check: Did user watch a specific movie?
    Uses tag page for fast lookup.
    """
    url = f"https://letterboxd.com/{username}/tag/onlycinephiles/films/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    cache = load_stats_cache(username)
    print(f"🏷️ Scraping {username} from tag page...")
    start_time = time.time()
    cache = cache or {}

    if is_slug_in_cache(username, movie_slug, cache):
        print(f"   Found {movie_slug} in cache")
        return True

    try:
        logs = get_all_user_logs(username, [movie_slug])
        if logs and movie_slug in logs[username]['films']:
            print(f"   Found {movie_slug} in logs")
            return True
        return False
        # time.sleep(0.3)
        # resp = requests.get(url, headers=headers)
        
        # if resp.status_code != 200:
        #     return False
        
        # soup = BeautifulSoup(resp.text, "html.parser")
        # film_divs = soup.select('div[data-item-slug]')
        
        # for div in film_divs:
        #     if div['data-item-slug'] == movie_slug:
        #         return True
        
        # return False
        
    except Exception as e:
        print(f"Error checking if {username} watched {movie_slug}: {e}")
        return False


# Legacy functions (kept for backwards compatibility)
def did_user_watch_movie(username, target_slug, max_pages=1):
    """Legacy function - consider using user_watched_last_film() instead"""
    return user_watched_last_film(username, target_slug)


def get_user_number_of_movies_watched(username):
    """Get the number of movies watched by a user with proper checks and logging."""
    letterboxd_url = f"https://letterboxd.com/{username}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    print(f"Fetching profile page for {username}: {letterboxd_url}")

    try:
        resp = fetch_page(letterboxd_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching profile for {username}: {e}")
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')

    user_stats_element = soup.select_one('div.profile-stats.js-profile-stats')
    if not user_stats_element:
        print(f"Profile stats element not found for {username}")
        return None

    # Primary selector used previously
    user_stats_individual_elements = user_stats_element.select('h4.profile-statistic.statistic')
    target_element = None

    if len(user_stats_individual_elements) >= 2:
        target_element = user_stats_individual_elements[1]
        is_this_year = target_element.select_one('span.definition').get_text(strip=True) == "This year"
        if not is_this_year:
            print(f"Watched count for {username} is not from this year")
            return 0
        print(f"Found target stats element from h4.profile-statistic for {username}")
    else:
        # Fallbacks: look for the films link value or any span.value in the stats block
        target_element = user_stats_element.select_one('a[href$="/films/"] span.value') \
                         or user_stats_element.select_one('span.value')
        if target_element:
            print(f"Found target stats element using fallback selectors for {username}")

    if not target_element:
        print(f"Could not locate the watched count element for {username}")
        return None

    # Extract number and sanitize
    value_text = target_element.get_text(strip=True)
    print(f"Raw watched-count text for {username}: {value_text}")

    # Remove non-digits (commas, spaces, etc.)
    digits = re.sub(r'[^\d]', '', value_text)
    if not digits:
        print(f"No digits found in watched count for {username} (raw: {value_text})")
        print(f"Unable to parse watched count for {username}: '{value_text}'")
        return None

    try:
        count = int(digits)
    except ValueError as e:
        print(f"Error parsing watched count for {username}: {e}")
        return None

    print(f"User {username} has watched {count} movies")
    return count

# selected_slugs = [
#     "the-count-of-monte-cristo-2024",
#     "et-the-extra-terrestrial",
#     "my-neighbor-totoro",
#     "portrait-of-a-lady-on-fire",
#     "everybody-wants-some",
#     "dead-poets-society",
#     "schindlers-list",
#     "children-of-men",
#     "the-shawshank-redemption",
#     "eyes-wide-shut",
#     "the-hunt-2012",
#     "brazil",
#     "blue-valentine",
#     "moonrise-kingdom",
#     "the-fantastic-4-first-steps",
#     "amelie",
#     "the-florida-project",
#     "rain-man",
#     "moneyball",
#     "the-thing",
#     "the-rocky-horror-picture-show",
#     "titanic-1997",
#     "inglourious-basterds",
#     "die-hard",
#     "the-nightmare-before-christmas",
# ]

# selected_slugs = ['before-sunrise']
# the-count-of-monte-cristo-2024
# et-the-extra-terrestrial
# my-neighbor-totoro
# portrait-of-a-lady-on-fire
# for username in usernames:
#     start_time = time.time()
#     logs = get_all_user_logs(username, selected_slugs)
#     end_time = time.time()
#     print(f"Found {len(logs)} movies for {username} in {end_time - start_time} seconds")
#     for log in logs:
#         print(f"  - {log['slug']} ({log['title']}): {log['rating']}⭐, {log['word_count']} words")

# user_watched_last_film = user_watched_last_film_optimized("bjoubs", "the-nightmare-before-christmas")
# print(user_watched_last_film)

# user_watched_last_film = user_watched_last_film_optimized("bjoubs", "moneyball")
# print(user_watched_last_film)

# user_watched_last_film = user_watched_last_film_optimized("meganyip1211", "moneyball")
# print(user_watched_last_film)
