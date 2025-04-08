from flask import Flask, render_template, redirect, url_for, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import load_config
from cache import is_cache_valid, load_cache, save_cache, CACHE_FILE
from scraper import get_all_user_logs
from utils import expand_short_url, build_stats

app = Flask(__name__)

# -------------- Config ------------------
CONFIG = load_config()
USERNAMES = CONFIG['usernames']
MOVIES = CONFIG['movies']

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
