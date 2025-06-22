import json
import time
from bs4 import BeautifulSoup
import requests
from utils import slugify, extract_full_date, parse_rating, resolve_letterboxd_url
import lxml

def user_watched_last_film(username, movie_slug):
    """
    Returns True if the given movie_slug is found in the user's onlycinephiles tag list, else False.
    Includes detailed logging and timing.
    """
    print(f"🔍 Checking if '{username}' watched '{movie_slug}' via onlycinephiles tag...")
    start_time = time.time()
    time.sleep(0.3)
    url = f"https://letterboxd.com/{username}/tag/onlycinephiles/films/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        req_start = time.time()
        resp = requests.get(url, headers=headers)
        req_end = time.time()
        print(f"    ⏱️ Request to {url} took {req_end - req_start:.2f} seconds")
        if resp.status_code != 200:
            print(f"    ❌ Failed to fetch {url} (status {resp.status_code})")
            return False
        parse_start = time.time()
        soup = BeautifulSoup(resp.text, "html.parser")
        film_divs = soup.select('div[data-film-slug]')
        parse_end = time.time()
        print(f"    ⏱️ Parsing HTML took {parse_end - parse_start:.2f} seconds")
        for div in film_divs:
            found_slug = div['data-film-slug']
            print(f"        - Found slug: {found_slug}")
            if found_slug == movie_slug:
                print(f"    ✅ {username} HAS watched {movie_slug} (found in tag list)")
                total_time = time.time() - start_time
                print(f"    ⏳ Total time for user_watched_last_film: {total_time:.2f} seconds")
                return True
        print(f"    ❌ {username} has NOT watched {movie_slug} (not found in tag list)")
        total_time = time.time() - start_time
        print(f"    ⏳ Total time for user_watched_last_film: {total_time:.2f} seconds")
        return False
    except Exception as e:
        print(f"    ❌ Error fetching or parsing {url}: {e}")
        return False

def parse_letterboxd_movie(link):
    # Step 1: Expand short URL if needed
    if 'boxd.it' in link:
        link = resolve_letterboxd_url(link)

    # Step 2: Fetch and parse the movie page
    resp = requests.get(link)
    soup = BeautifulSoup(resp.text, 'html.parser')

    json_ld = soup.find("script", type="application/ld+json")
    if not json_ld:
        raise Exception("Structured movie data not found.")

    data = json.loads(json_ld.string)

    title = data.get("name")
    year = data.get("datePublished")[:4] if data.get("datePublished") else None
    poster_url = data.get("image")
    slug = link.strip('/').split('/')[-1]  # e.g., "heat-1995"

    return {
        "title": title,
        "year": int(year) if year else None,
        "poster_url": poster_url,
        "slug": slug,
        "url": link
    }

def count_review_words(url, headers):
    try:
        time.sleep(0.5)
        request_start = time.time()
        resp = requests.get(url, headers=headers)
        request_end = time.time()
        print(f"    Request to {url} took {request_end - request_start:.2f} seconds")
        if resp.status_code != 200:
            print(f"Request failed with status code (review count) {resp.status_code}")
            return 0
        # Parse the response content
        request_start = time.time()
        soup = BeautifulSoup(resp.text, 'html.parser')
        review_box = soup.select_one('div.review') or soup.select_one('div.truncate')
        if review_box:
            request_end = time.time()
            print(f"    Parsing review took {request_end - request_start:.2f} seconds")
            return len(review_box.get_text(separator=' ', strip=True).split())
    except:
        pass
    return 0

# -------------- Scraper ------------------
def get_all_user_logs(username, target_slugs, review_word_counts_cache=None, max_pages=1):
    logs = []
    target_slugs = set(target_slugs)  # ✅ Optimization: use a set for O(1) lookups
    review_word_counts_cache = review_word_counts_cache or {}  # 🔧 Ensure default dict

    function_start = time.time()
    found_slugs = set()  # ✅ Optimization: track found slugs to exit early

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for page in range(1, max_pages + 1):
        page_start = time.time()
        url = f'https://letterboxd.com/{username}/films/diary/page/{page}/'
        try:
            resp = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as e:
            print(f"Page {page}: Request failed due to exception: {e}")
            break

        if resp.status_code == 429:
            print(f"⚠️ Rate limited on page {page} for user {username}. Status code: 429")
            time.sleep(5)  # ✅ Backoff on 429
            continue

        if resp.status_code != 200:
            print(f"Page {page}: Request failed with status code {resp.status_code}")
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        rows = soup.select('tr.diary-entry-row')
        if not rows:
            print(f"Page {page}: No diary entry rows found.")
            break

        page_end = time.time()
        print(f"Page {page}: Request and parsing took {page_end - page_start:.2f} seconds")

        rows_start = time.time()

        for row in rows:
            poster = row.select_one('div[data-film-slug]')
            if not poster:
                continue

            slug = slugify(poster['data-film-slug'])
            if slug not in target_slugs:
                continue

            found_slugs.add(slug)

            title_tag = row.select_one('h3.headline-3 a')
            title = title_tag.text.strip() if title_tag else "NA"
            link = f"https://letterboxd.com{title_tag['href']}" if title_tag else ''
            date_tag = row.select_one('td.td-day a')
            date = extract_full_date(date_tag['href']) if date_tag and date_tag.has_attr('href') else 'Unknown date'
            rating_tag = row.select_one('div.hide-for-owner span.rating')
            rating_text = rating_tag.text.strip() if rating_tag else ''
            rating = parse_rating(rating_text)
            has_review = row.select_one('a.icon-review') is not None

            # 🔧 Use or update review word count cache
            cache_key = f"{username}_{slug}"
            if has_review and cache_key in review_word_counts_cache:
                word_count = review_word_counts_cache[cache_key]
            elif has_review:
                review_start = time.time()
                word_count = count_review_words(link, headers)
                review_end = time.time()
                print(f"🔧 Counted {word_count} words (took {review_end - review_start:.2f}s)")
                review_word_counts_cache[cache_key] = word_count
            else:
                word_count = 0

            logs.append({
                'title': title,
                'date': date,
                'rating': rating,
                'rating_str': rating_text,
                'url': link,
                'has_review': has_review,
                'word_count': word_count
            })

        rows_end = time.time()
        print(f"Page {page}: Processing rows took {rows_end - rows_start:.2f} seconds")

        if found_slugs == target_slugs:
            print(f"✅ All target slugs found for {username}. Early exit.")
            break

        time.sleep(0.5)

    function_end = time.time()
    print(f"get_all_user_logs({username}) took {function_end - function_start:.2f} seconds")
    return logs

def did_user_watch_movie(username, target_slug, max_pages=1):
    logs = []
    function_start = time.time()

    for page in range(1, max_pages + 1):
        # Start timer for each page request
        page_start = time.time()

        url = f'https://letterboxd.com/{username}/films/diary/page/{page}/'
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Page {page}: Request failed with status code {resp.status_code}")
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        rows = soup.select('tr.diary-entry-row')
        if not rows:
            print(f"Page {page}: No diary entry rows found.")
            break

        # End timer for page request and parsing
        page_end = time.time()
        print(f"Page {page}: Request and parsing took {page_end - page_start:.2f} seconds")

        for row in rows:
            poster = row.select_one('div[data-film-slug]')
            if not poster:
                continue

            slug = slugify(poster['data-film-slug'])
            print(slug, target_slug)
            if slug != target_slug:
                continue
            return True
            
        # Add a delay to avoid overwhelming the server
        time.sleep(1)

    # End timer for the entire function
    function_end = time.time()
    print(f"get_all_user_logs({username}) took {function_end - function_start:.2f} seconds")

    return False

def get_user_diary(username, max_pages=1):
    logs = []

    for page in range(1, max_pages + 1):
        url = f'https://letterboxd.com/{username}/films/diary/page/{page}/'
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Page {page}: Request failed with status code {resp.status_code}")
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        rows = soup.select('tr.diary-entry-row')
        if not rows:
            print(f"Page {page}: No diary entry rows found.")
            break

        for row in rows:
            poster = row.select_one('div[data-film-slug]')
            if not poster:
                continue

            slug = slugify(poster['data-film-slug'])
            title_tag = row.select_one('h3.headline-3 a')
            title = title_tag.text.strip() if title_tag else 'Unknown Title'
            link = f"https://letterboxd.com{title_tag['href']}" if title_tag else ''
            date_tag = row.select_one('td.td-day a')
            date = extract_full_date(date_tag['href']) if date_tag and date_tag.has_attr('href') else 'Unknown date'
            rating_tag = row.select_one('div.hide-for-owner span.rating')
            rating_text = rating_tag.text.strip() if rating_tag else ''
            rating = parse_rating(rating_text)
            has_review = row.select_one('a.icon-review') is not None

            logs.append({
                'slug': slug,
                'title': title,
                'date': date,
                'rating': rating,
                'rating_str': rating_text,
                'url': link,
                'has_review': has_review
            })

        # Add a delay to avoid overwhelming the server
        time.sleep(1)

    return logs