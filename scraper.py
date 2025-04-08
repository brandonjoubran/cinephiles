import json
import time
from bs4 import BeautifulSoup
import requests
from utils import slugify, extract_full_date, parse_rating, resolve_letterboxd_url


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

def count_review_words(url):
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        review_box = soup.select_one('div.review') or soup.select_one('div.truncate')
        if review_box:
            return len(review_box.get_text(separator=' ', strip=True).split())
    except:
        pass
    return 0

# -------------- Scraper ------------------
def get_all_user_logs(username, movie_title, max_pages=2):
    logs = []
    target_slug = slugify(movie_title)

    for page in range(1, max_pages + 1):
        url = f'https://letterboxd.com/{username}/films/diary/page/{page}/'
        resp = requests.get(url)
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        rows = soup.select('tr.diary-entry-row')
        if not rows:
            break

        for row in rows:
            poster = row.select_one('div[data-film-slug]')
            if not poster:
                continue

            slug = slugify(poster['data-film-slug'])
            if slug != target_slug:
                continue

            title_tag = row.select_one('h3.headline-3 a')
            title = title_tag.text.strip() if title_tag else movie_title
            link = f"https://letterboxd.com{title_tag['href']}" if title_tag else ''
            date_tag = row.select_one('td.td-day a')
            date = extract_full_date(date_tag['href']) if date_tag and date_tag.has_attr('href') else 'Unknown date'
            rating_tag = row.select_one('div.hide-for-owner span.rating')
            rating_text = rating_tag.text.strip() if rating_tag else ''
            rating = parse_rating(rating_text)
            has_review = row.select_one('a.icon-review') is not None
            word_count = count_review_words(link) if has_review else 0

            logs.append({
                'title': title,
                'date': date,
                'rating': rating,
                'rating_str': rating_text,
                'url': link,
                'has_review': has_review,
                'word_count': word_count
            })
        time.sleep(0.2)
    return logs