# Letterboxd Stats App (Flask)
from flask import Flask, render_template, redirect, url_for, request
from collections import defaultdict
import statistics
import requests
from bs4 import BeautifulSoup
import time
import re
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

# -------------------- Constants -------------------- #

# These are your fixed usernames and movies to track
USERNAMES = [
    'bjoubs', 'KingKrab', 'raymondeezy', 'meganyip1211',
    'GeoMoD', 'ArnoZeld', 'BrittWilliamss', 'emilylush11', 'sarasantos28'
]

MOVIES = [
    "The count of monte cristo 2024", 
    "E.T. the Extra-Terrestrial",
    "My Neighbor Totoro",
    "Everybody Wants Some",
    "Portrait of a lady on fire",
    "Dead Poets Society",
    "Schindler's list"
]

CACHE_FILE = "/tmp/stats_cache.json"
CACHE_TTL = 60 * 60  # 1 hour

# -------------------- Utility Functions -------------------- #

def is_cache_valid():
    return os.path.exists(CACHE_FILE) and (time.time() - os.path.getmtime(CACHE_FILE) < CACHE_TTL)

def load_cache():
    with open(CACHE_FILE, 'r') as f:
        return json.load(f)

def save_cache(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def slugify(title):
    return title.lower().replace(' ', '-').replace(':', '').replace("'", "").replace(",", "").replace(".", "").replace("&", "and")

def extract_full_date(href):
    match = re.search(r'/diary/for/(\d{4})/(\d{2})/(\d{2})/', href)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"
    return "Unknown date"

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
            text = review_box.get_text(separator=' ', strip=True)
            return len(text.split())
    except:
        pass
    return 0

# -------------------- Scraping Diary Logs -------------------- #

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
            poster_div = row.select_one('div[data-film-slug]')
            if not poster_div:
                continue

            film_slug = poster_div.get('data-film-slug', '')
            if slugify(film_slug) != target_slug:
                continue

            title_tag = row.select_one('h3.headline-3 a')
            title = title_tag.text.strip() if title_tag else target_slug
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

# -------------------- Stats Builder -------------------- #

def build_stats_from_logs(log_data):
    user_stats = {}
    movie_ratings = defaultdict(list)
    first_watch = defaultdict(list)
    longest_review = {'user': None, 'words': 0, 'title': None, 'url': None}
    shortest_review = {'user': None, 'words': float('inf'), 'title': None, 'url': None}

    # Init user stats
    for username, _ in log_data.keys():
        user_stats[username] = {'watched': 0, 'ratings': [], 'reviews': 0, 'words': []}

    for (username, movie_title), logs in log_data.items():
        if not logs:
            continue

        user_stats[username]['watched'] += 1

        for log in logs:
            rating = log['rating']
            movie_ratings[movie_title].append(rating)

            if rating is not None:
                user_stats[username]['ratings'].append(rating)

            if log['has_review']:
                wc = log['word_count']
                user_stats[username]['reviews'] += 1
                user_stats[username]['words'].append(wc)

                if wc > longest_review['words']:
                    longest_review = {
                        'user': username, 'words': wc, 'title': log['title'], 'url': log['url']
                    }
                if wc < shortest_review['words'] and wc > 0:
                    shortest_review = {
                        'user': username, 'words': wc, 'title': log['title'], 'url': log['url']
                    }

            first_watch[movie_title].append((log['date'], username))

    # Build summary
    summary = []
    for username in sorted(user_stats, key=lambda u: user_stats[u]['watched'], reverse=True):
        stats = user_stats[username]
        avg_rating = round(sum(stats['ratings']) / len(stats['ratings']), 2) if stats['ratings'] else 0
        avg_words = round(sum(stats['words']) / len(stats['words']), 1) if stats['words'] else 0
        summary.append({
            'username': username,
            'watched': stats['watched'],
            'avg_rating': avg_rating,
            'reviews': stats['reviews'],
            'avg_words': avg_words
        })

    # Most divisive movie
    most_divisive = ("No movies", [])
    most_divisive_stddev = 0
    if movie_ratings:
        most_divisive = max(
            movie_ratings.items(),
            key=lambda item: statistics.stdev([r for r in item[1] if r is not None]) if len(item[1]) > 1 else 0
        )
        most_divisive_stddev = round(
            statistics.stdev([r for r in most_divisive[1] if r is not None]), 2
        ) if len(most_divisive[1]) > 1 else 0

    # Most liked and least liked
    avg_ratings = {
        movie: sum(r for r in ratings if r is not None) / len([r for r in ratings if r is not None])
        for movie, ratings in movie_ratings.items()
    }
    most_liked = max(avg_ratings.items(), key=lambda x: x[1])
    least_liked = min(avg_ratings.items(), key=lambda x: x[1])

    return {
        'summary': summary,
        'most_divisive': most_divisive,
        'most_divisive_stddev': most_divisive_stddev,
        'most_liked': most_liked,
        'least_liked': least_liked,
        'longest_review': longest_review,
        'shortest_review': shortest_review,
        'first_watch': first_watch
    }

# -------------------- Routes -------------------- #

@app.route('/')
def index():
    if is_cache_valid():
        print("✅ Using cached data")
        raw_cache = load_cache()

        # Rebuild data structure from flat cache keys
        log_data = {}
        for cache_key, logs in raw_cache.items():
            if '||' in cache_key:
                username, movie_title = cache_key.split('||')
                log_data[(username, movie_title)] = logs

        return render_template('index.html', **build_stats_from_logs(log_data))

    print("♻️ Cache expired or missing. Recomputing...")
    user_movie_pairs = [(u, m) for u in USERNAMES for m in MOVIES]
    log_data = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(get_all_user_logs, u, m): (u, m) for u, m in user_movie_pairs
        }
        for future in as_completed(futures):
            u, m = futures[future]
            try:
                log_data[(u, m)] = future.result()
            except Exception as e:
                print(f"Error for {u} - {m}: {e}")

    # Save to flat cache format
    raw_cache = {}
    for (u, m), logs in log_data.items():
        raw_cache[f"{u}||{m}"] = logs
    save_cache(raw_cache)

    return render_template('index.html', **build_stats_from_logs(log_data))

@app.route('/refresh/<username>', methods=['POST'])
def refresh_user(username):
    user_logs = {}
    for movie in MOVIES:
        user_logs[(username, movie)] = get_all_user_logs(username, movie)

    cache_data = load_cache() if os.path.exists(CACHE_FILE) else {}
    for (u, m), logs in user_logs.items():
        cache_data[f"{u}||{m}"] = logs

    save_cache(cache_data)
    return redirect(url_for('index'))

# -------------------- Main -------------------- #

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)