from flask import Flask, render_template, redirect, url_for, request, jsonify
from collections import defaultdict
import statistics
import requests
from bs4 import BeautifulSoup
import time
import re
import os
import json
#import psycopg2
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

def resolve_letterboxd_url(short_url):
    response = requests.get(short_url, allow_redirects=True)
    return response.url  # final resolved URL like https://letterboxd.com/film/heat-1995/

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

# -------------- Config ------------------
CONFIG_PATH = "config.json"
CACHE_FILE = "/tmp/stats_cache.json"
CACHE_TTL = 60 * 60 * 12  # 12 hours

# -------------- Load Config --------------
def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

CONFIG = load_config()
USERNAMES = CONFIG['usernames']
MOVIES = CONFIG['movies']

# -------------- Caching ------------------
def is_cache_valid():
    return os.path.exists(CACHE_FILE) and (time.time() - os.path.getmtime(CACHE_FILE) < CACHE_TTL)

def load_cache():
    with open(CACHE_FILE, 'r') as f:
        return json.load(f)

def save_cache(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

# -------------- Utility ------------------
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

def expand_short_url(url):
    try:
        return requests.head(url, allow_redirects=True).url
    except:
        return url

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

# -------------- Stats Aggregation ------------------
def build_stats(logs_by_user_movie):
    stats = defaultdict(lambda: {'watched': 0, 'ratings': [], 'reviews': 0, 'words': []})
    movie_ratings = defaultdict(list)
    first_watch = defaultdict(list)
    longest = {'user': None, 'words': 0, 'title': None, 'url': None}
    shortest = {'user': None, 'words': float('inf'), 'title': None, 'url': None}

    for (username, title), logs in logs_by_user_movie.items():
        if not logs:
            continue

        stats[username]['watched'] += 1
        for log in logs:
            if log['rating'] is not None:
                stats[username]['ratings'].append(log['rating'])
                movie_ratings[title].append(log['rating'])

            if log['has_review']:
                stats[username]['reviews'] += 1
                stats[username]['words'].append(log['word_count'])

                if log['word_count'] > longest['words']:
                    longest = {'user': username, 'words': log['word_count'], 'title': log['title'], 'url': log['url']}

                if 0 < log['word_count'] < shortest['words']:
                    shortest = {'user': username, 'words': log['word_count'], 'title': log['title'], 'url': log['url']}

            first_watch[title].append((log['date'], username))

    summary = []
    for username in sorted(stats, key=lambda u: stats[u]['watched'], reverse=True):
        user = stats[username]
        summary.append({
            'username': username,
            'watched': user['watched'],
            'avg_rating': round(sum(user['ratings']) / len(user['ratings']), 2) if user['ratings'] else 0,
            'reviews': user['reviews'],
            'avg_words': round(sum(user['words']) / len(user['words']), 1) if user['words'] else 0
        })

    divisive = max(
        movie_ratings.items(),
        key=lambda x: statistics.stdev([r for r in x[1] if r is not None]) if len(x[1]) > 1 else 0,
        default=("No movies", [])
    )
    divisive_std = round(statistics.stdev([r for r in divisive[1] if r is not None]), 2) if len(divisive[1]) > 1 else 0

    averages = {movie: sum(r for r in rs if r is not None) / len([r for r in rs if r is not None]) for movie, rs in movie_ratings.items()}
    most_liked = max(averages.items(), key=lambda x: x[1], default=("N/A", 0))
    least_liked = min(averages.items(), key=lambda x: x[1], default=("N/A", 0))

    return {
        "summary": summary,
        "most_divisive": divisive,
        "most_divisive_stddev": divisive_std,
        "most_liked": most_liked,
        "least_liked": least_liked,
        "longest_review": longest,
        "shortest_review": shortest,
        "first_watch": first_watch
    }

# -------------- Routes ------------------
@app.route('/')
def index():
    if is_cache_valid():
        print("✅ Using cached data")
        cache = load_cache()
        logs_by_user_movie = {}
        for key, logs in cache.items():
            if '||' in key:
                username, title = key.split('||')
                logs_by_user_movie[(username, title)] = logs
    else:
        print("♻️ Recomputing cache")
        logs_by_user_movie = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(get_all_user_logs, username, movie): (username, movie)
                for username in USERNAMES for movie in MOVIES
            }
            for future in as_completed(futures):
                username, movie = futures[future]
                try:
                    logs_by_user_movie[(username, movie)] = future.result()
                except Exception as e:
                    print(f"Failed to fetch logs for {username} - {movie}: {e}")

        save_cache({f"{u}||{m}": logs for (u, m), logs in logs_by_user_movie.items()})

    return render_template('index.html', **build_stats(logs_by_user_movie))

@app.route('/refresh/<username>', methods=['POST'])
def refresh_user(username):
    logs_by_user = {}
    for movie in MOVIES:
        logs_by_user[(username, movie)] = get_all_user_logs(username, movie)

    cache = load_cache() if os.path.exists(CACHE_FILE) else {}
    for (u, m), logs in logs_by_user.items():
        cache[f"{u}||{m}"] = logs
    save_cache(cache)

    return redirect(url_for('index'))

@app.route('/parse-movie', methods=['POST'])
def parse_movie():
    link = request.form.get('url')
    if not link:
        return jsonify({"error": "Missing URL"}), 400

    full_url = expand_short_url(link)
    match = re.search(r'/film/([^/]+)/', full_url)
    if not match:
        return jsonify({"error": "Invalid Letterboxd link"}), 400

    slug = match.group(1)
    resp = requests.get(full_url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    title_tag = soup.find('meta', property='og:title')
    title = title_tag['content'] if title_tag else slug.replace('-', ' ').title()

    return jsonify({"title": title, "slug": slug, "url": full_url})

@app.route('/watchlist')
def watchlist():
    return render_template('watchlist.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
