import json
import time
from bs4 import BeautifulSoup
import requests
from utils import slugify, extract_full_date, parse_rating, resolve_letterboxd_url
import lxml

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
        time.sleep(1)
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Request failed with status code (review count) {resp.status_code}")
            return 0
        # Parse the response content
        soup = BeautifulSoup(resp.text, 'html.parser')
        review_box = soup.select_one('div.review') or soup.select_one('div.truncate')
        if review_box:
            return len(review_box.get_text(separator=' ', strip=True).split())
    except:
        pass
    return 0

# -------------- Scraper ------------------
def get_all_user_logs(username, target_slugs, max_pages=1):
    logs = []
    # target_slugs = []
    # #target_slug = slugify(movie_title)
    # for movie_title in movie_titles:
    #     target_slug = slugify(movie_title)
    #     target_slugs.append(target_slug)

    # Start timer for the entire function

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    function_start = time.time()

    for page in range(1, max_pages + 1):
        # Start timer for each page request
        page_start = time.time()

        url = f'https://letterboxd.com/{username}/films/diary/page/{page}/'
        resp = requests.get(url, headers=headers)
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

        # Start timer for processing rows
        rows_start = time.time()

        for row in rows:
            poster = row.select_one('div[data-film-slug]')
            if not poster:
                continue

            slug = slugify(poster['data-film-slug'])
            if slug not in target_slugs:
                continue

            title_tag = row.select_one('h3.headline-3 a')
            title = title_tag.text.strip() if title_tag else "NA"
            link = f"https://letterboxd.com{title_tag['href']}" if title_tag else ''
            date_tag = row.select_one('td.td-day a')
            date = extract_full_date(date_tag['href']) if date_tag and date_tag.has_attr('href') else 'Unknown date'
            rating_tag = row.select_one('div.hide-for-owner span.rating')
            rating_text = rating_tag.text.strip() if rating_tag else ''
            rating = parse_rating(rating_text)
            has_review = row.select_one('a.icon-review') is not None

            # Start timer for counting review words
            review_start = time.time()
            word_count = count_review_words(link, headers) if has_review else 0
            review_end = time.time()
            if has_review:
                print(f"Counting review words took {review_end - review_start:.2f} seconds")

            logs.append({
                'title': title,
                'date': date,
                'rating': rating,
                'rating_str': rating_text,
                'url': link,
                'has_review': has_review,
                'word_count': word_count
            })

        # End timer for processing rows
        rows_end = time.time()
        print(f"Page {page}: Processing rows took {rows_end - rows_start:.2f} seconds")

        # Add a delay to avoid overwhelming the server
        time.sleep(1)

    # End timer for the entire function
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