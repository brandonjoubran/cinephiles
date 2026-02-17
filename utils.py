from collections import defaultdict
import os
import queue
import re
import statistics
import requests
import time
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from urllib.parse import urlparse

# One worker thread for "one browser per user" flows (warm). Playwright runs only in this thread.
_playwright_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="playwright")


def _playwright_headless():
    """Use PLAYWRIGHT_HEADLESS=0 or false to run with a visible browser (watch locally)."""
    v = (os.environ.get("PLAYWRIGHT_HEADLESS") or "true").strip().lower()
    return v not in ("0", "false", "no", "off")


def _chromium_launch_args():
    """Args for Chromium. When headless=False we skip server-style flags so the window can show."""
    if _playwright_headless():
        return [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--single-process",
        ]
    return []  # visible browser: use defaults so it can attach to your display

# Single browser thread: all Playwright runs here (avoids "Sync API inside asyncio loop" and one Chrome for all requests).
_browser_request_queue = queue.Queue()
_browser_thread_started = threading.Lock()
_browser_thread = None

try:
    import cloudscraper
except ImportError:
    cloudscraper = None

DEFAULT_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def _is_challenge_page(response):
    if not response:
        return False

    text = (response.text or "").lower()
    server_header = (response.headers.get("server", "") or "").lower()
    status = response.status_code

    challenge_markers = [
        "just a moment",
        "attention required",
        "cf-browser-verification",
        "cf_chl",
        "cf-chl",
        "/cdn-cgi/challenge-platform",
        "enable javascript and cookies",
    ]

    has_marker = any(marker in text for marker in challenge_markers)
    cloudflare_header = "cloudflare" in server_header

    if status in (403, 429, 503) and (has_marker or cloudflare_header):
        return True
    return has_marker and cloudflare_header


# Run before any page loads to reduce Cloudflare/security-check triggers.
_PLAYWRIGHT_STEALTH_INIT_SCRIPT = """
(function() {
  Object.defineProperty(navigator, 'webdriver', { get: function() { return undefined; }, configurable: true });
  if (window.chrome === undefined) window.chrome = { runtime: {} };
})();
"""


def _apply_playwright_context_options(context, user_agent):
    """Make the browser look like a real user to reduce security checks."""
    context.add_init_script(_PLAYWRIGHT_STEALTH_INIT_SCRIPT)
    # Already set via new_context: user_agent, viewport. Add locale and timezone.
    try:
        context.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
    except Exception:
        pass


def _browser_thread_worker():
    """Runs in a dedicated thread (no asyncio). One browser, new page (tab) per request."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        while True:
            _, _, _, _, future = _browser_request_queue.get()
            if future is None:
                break
            future.set_result(None)
        return
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=_playwright_headless(),
        args=_chromium_launch_args(),
    )
    context = browser.new_context(
        user_agent=DEFAULT_BROWSER_HEADERS["User-Agent"],
        viewport={"width": 1280, "height": 720},
        locale="en-US",
        timezone_id="America/New_York",
    )
    _apply_playwright_context_options(context, DEFAULT_BROWSER_HEADERS["User-Agent"])
    print("[fetch] Shared Playwright browser started (single instance, new tab per request)")
    while True:
        item = _browser_request_queue.get()
        url, timeout, user_agent, extra_wait_ms, future = item
        if future is None:
            break
        try:
            page = context.new_page()
            try:
                page.goto(url, wait_until="load", timeout=timeout * 1000)
                page.wait_for_timeout(extra_wait_ms)
                if "/tag/" in url and "/films" in url:
                    try:
                        page.wait_for_selector("div[data-item-slug]", timeout=12000)
                    except Exception:
                        pass
                elif "/film/" in url:
                    try:
                        page.wait_for_selector("h1.headline-1", timeout=15000)
                    except Exception:
                        pass
                html = page.content()
                final_url = page.url
                future.set_result((final_url, html))
            finally:
                page.close()
        except Exception as e:
            print(f"[fetch] Playwright request failed: {e}")
            future.set_result(None)
    try:
        context.close()
        browser.close()
        pw.stop()
    except Exception:
        pass
    print("[fetch] Shared Playwright browser closed")


def _ensure_browser_thread():
    global _browser_thread
    with _browser_thread_started:
        if _browser_thread is not None and _browser_thread.is_alive():
            return
        _browser_thread = threading.Thread(target=_browser_thread_worker, daemon=True)
        _browser_thread.start()


def _playwright_fetch(url, timeout, user_agent, extra_wait_after_load_ms=6000):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[fetch] Playwright not installed, skipping browser request")
        return None
    _ensure_browser_thread()
    future = Future()
    _browser_request_queue.put((url, timeout, user_agent, extra_wait_after_load_ms, future))
    try:
        result = future.result(timeout=timeout + 30)
    except Exception as e:
        print(f"[fetch] Playwright request failed: {e}")
        return None
    if result is None:
        return None
    final_url, html = result
    print(f"[fetch] Playwright got page (200) for {final_url} [shared browser]")
    synthetic = requests.Response()
    synthetic.url = final_url
    synthetic._content = html.encode("utf-8")
    synthetic.encoding = "utf-8"
    synthetic.headers = {"server": "playwright"}
    synthetic.request = requests.Request("GET", final_url).prepare()
    text_lower = (html or "").lower()
    if any(m in text_lower for m in ("just a moment", "attention required", "cf-browser-verification")):
        synthetic.status_code = 403
    else:
        synthetic.status_code = 200
    return synthetic


def run_playwright_in_thread(fn, *args, **kwargs):
    """Run fn(*args, **kwargs) in a fresh dedicated thread (no asyncio, no executor reuse). Single browser for whole run."""
    result_holder = []
    def run():
        result_holder.append(fn(*args, **kwargs))
    t = threading.Thread(target=run, name="warm-browser")
    t.start()
    t.join()
    return result_holder[0] if result_holder else None


def shared_playwright_browser(user_agent=None, timeout=45, long_lived=False):
    """
    No-op context manager. Kept for API compatibility.
    For warm: use run_playwright_in_thread with a per-user browser instead.
    """
    class _Ctx:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    return _Ctx()


def _is_letterboxd_url(url):
    """True if this URL is for Letterboxd (we should try Playwright first to avoid 403).
    Includes letterboxd.com and short/mobile links like boxd.it.
    """
    host = (urlparse(url).netloc or "").lower().strip()
    if not host:
        return False
    return (
        host in ("letterboxd.com", "www.letterboxd.com")
        or host == "boxd.it"
        or host.endswith(".letterboxd.com")
        or host.endswith(".boxd.it")
    )


def fetch_page(url, headers=None, timeout=45, allow_redirects=True, method="get"):
    merged_headers = dict(DEFAULT_BROWSER_HEADERS)
    if headers:
        merged_headers.update(headers)

    request_method = method.lower()
    user_agent = merged_headers.get("User-Agent", DEFAULT_BROWSER_HEADERS["User-Agent"])

    # For Letterboxd GET requests, try Playwright first so we don't hit Cloudflare 403.
    if request_method == "get" and _is_letterboxd_url(url):
        print(f"[fetch] Letterboxd URL: trying Playwright first for {url}")
        pw_response = _playwright_fetch(url=url, timeout=timeout, user_agent=user_agent)
        if pw_response is not None and not _is_challenge_page(pw_response):
            return pw_response
        # Sometimes the security check needs more time; retry once with longer wait.
        if pw_response is not None and _is_challenge_page(pw_response):
            print(f"[fetch] Playwright got challenge page, retrying with longer wait for {url}")
            time.sleep(2)
            pw_response = _playwright_fetch(
                url=url, timeout=timeout, user_agent=user_agent, extra_wait_after_load_ms=12000
            )
            if pw_response is not None and not _is_challenge_page(pw_response):
                return pw_response
        print(f"[fetch] Playwright didn't succeed, falling back to requests for {url}")

    print(f"[fetch] HTTP request: {request_method.upper()} {url}")
    response = requests.request(
        request_method,
        url,
        headers=merged_headers,
        timeout=timeout,
        allow_redirects=allow_redirects,
    )
    print(f"[fetch] HTTP response: {response.status_code} for {url}")

    if not _is_challenge_page(response):
        return response

    print(f"[fetch] Got challenge/block (e.g. Cloudflare), trying cloudscraper for {url}")
    if cloudscraper is not None:
        for attempt in range(2):
            try:
                try:
                    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "mobile": False})
                except (KeyError, TypeError):
                    scraper = cloudscraper.create_scraper()
                cf_response = scraper.request(
                    request_method,
                    url,
                    headers=merged_headers,
                    timeout=timeout,
                    allow_redirects=allow_redirects,
                )
                if cf_response.status_code < 500 and not _is_challenge_page(cf_response):
                    return cf_response
                response = cf_response
                time.sleep(0.5 * (attempt + 1))
            except Exception as e:
                print(f"[fetch] Cloudscraper attempt {attempt + 1} failed: {e}")
                time.sleep(0.5 * (attempt + 1))

    if request_method == "get":
        print(f"[fetch] Trying Playwright as fallback for {url}")
        # Use shorter timeout on fallback so we don't burn another 45s if first attempt already timed out
        fallback_timeout = min(timeout, 25)
        pw_response = _playwright_fetch(url=url, timeout=fallback_timeout, user_agent=user_agent)
        if pw_response is not None and not _is_challenge_page(pw_response):
            return pw_response

    # Cloudflare blocked us and fallbacks didn't succeed
    import sys
    print(
        "Letterboxd is protected by Cloudflare; simple requests were blocked. "
        "Install a browser for Playwright so it can bypass the check: run 'playwright install chromium'",
        file=sys.stderr,
    )
    return response

def expand_short_url(url):
    try:
        return fetch_page(url, allow_redirects=True, method="head").url
    except:
        return url

def resolve_letterboxd_url(short_url):
    response = fetch_page(short_url, allow_redirects=True)
    return response.url  # final resolved URL like https://letterboxd.com/film/heat-1995/

def slugify(title):
    return title.lower().replace(' ', '-').replace(':', '').replace("'", "").replace(",", "").replace(".", "").replace("&", "and")

def extract_full_date(href):
    match = re.search(r'/diary/for/(\d{4})/(\d{2})/(\d{2})/', href)
    return f"{match[1]}-{match[2]}-{match[3]}" if match else "Unknown date"

def parse_rating(rating_str):
    if not rating_str:
        return None
    full_stars = rating_str.count('★')
    half_star = '½' in rating_str
    return full_stars + 0.5 if half_star else full_stars

def build_stats(logs_by_user, selected_records, rotw_counts):
    stats = defaultdict(lambda: {'watched': 0, 'ratings': [], 'reviews': 0, 'words': [], 'rotw_count': 0})
    movie_ratings = defaultdict(list)
    first_watch = defaultdict(list)
    longest = {'user': None, 'words': 0, 'title': None, 'url': None}
    shortest = {'user': None, 'words': float('inf'), 'title': None, 'url': None}

    # Process logs by user
    for username, logs in logs_by_user.items():
        for log in logs:
            title = log['title']
            stats[username]['watched'] += 1

            if log.get('rating') is not None:
                stats[username]['ratings'].append(log['rating'])
                movie_ratings[title].append(log['rating'])

            if log.get('has_review'):
                stats[username]['reviews'] += 1
                word_count = log.get('word_count', 0)
                stats[username]['words'].append(word_count)

                if word_count > longest['words']:
                    longest = {
                        'user': username,
                        'words': word_count,
                        'title': title,
                        'url': log['url']
                    }

                if 0 < word_count < shortest['words']:
                    shortest = {
                        'user': username,
                        'words': word_count,
                        'title': title,
                        'url': log['url']
                    }

            first_watch[title].append((log['date'], username))

    # Add ROTW counts from the cache
    for username, count in rotw_counts.items():
        stats[username]['rotw_count'] = count

    # Summary stats per user
    summary = []
    for username in sorted(stats, key=lambda u: stats[u]['watched'], reverse=True):
        user_stats = stats[username]
        summary.append({
            'username': username,
            'watched': user_stats['watched'],
            'avg_rating': round(sum(user_stats['ratings']) / len(user_stats['ratings']), 2) if user_stats['ratings'] else 0,
            'reviews': user_stats['reviews'],
            'avg_words': round(sum(user_stats['words']) / len(user_stats['words']), 1) if user_stats['words'] else 0,
            'rotw_count': user_stats['rotw_count']  # Add ROTW count to the summary
        })

    # Movie stats
    divisive = max(
        movie_ratings.items(),
        key=lambda x: statistics.stdev(x[1]) if len(x[1]) > 1 else 0,
        default=("No movies", [])
    )
    divisive_std = round(statistics.stdev(divisive[1]), 2) if len(divisive[1]) > 1 else 0

    averages = {}
    for movie, ratings in movie_ratings.items():
        valid = [r for r in ratings if r is not None]
        if valid:
            averages[movie] = sum(valid) / len(valid)

    most_liked = max(averages.items(), key=lambda x: x[1], default=("N/A", 0))
    least_liked = min(averages.items(), key=lambda x: x[1], default=("N/A", 0))

    for title in first_watch:
        first_watch[title] = sorted(first_watch[title])

    return {
        'summary': summary,
        'most_divisive': divisive,
        'most_divisive_stddev': divisive_std,
        'most_liked': most_liked,
        'least_liked': least_liked,
        'longest_review': longest,
        'shortest_review': shortest,
        'first_watch': first_watch
    }
