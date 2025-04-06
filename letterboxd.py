from flask import Flask, render_template
from collections import defaultdict
import statistics
import requests
from bs4 import BeautifulSoup
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json

app = Flask(__name__)

# Include all your existing functions here (slugify, extract_full_date, parse_rating, count_review_words, get_all_user_logs)

CACHE_FILE = "/tmp/stats_cache.json"
CACHE_TTL = 60 * 60  # 1 hour

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
    except Exception as e:
        pass
    return 0

def get_all_user_logs(username, movie_title, max_pages=2):
    logs = []
    target_slug = slugify(movie_title)

    for page in range(1, max_pages + 1):
        url = f'https://letterboxd.com/{username}/films/diary/page/{page}/'
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Failed to fetch page {page} for {username}")
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

            # 🗓️ Extract watch date
            date_tag = row.select_one('td.td-day a')
            date = extract_full_date(date_tag['href']) if date_tag and date_tag.has_attr('href') else 'Unknown date'

            # ⭐ Extract rating
            rating_tag = row.select_one('div.hide-for-owner span.rating')
            rating_text = rating_tag.text.strip() if rating_tag else ''
            rating = parse_rating(rating_text)

            # 📝 Check if there's a review
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

@app.route('/')
def index():
    if is_cache_valid():
        print("✅ Using cached data")
        return render_template('index.html', **load_cache())
    
    print("♻️ Cache expired or missing. Recomputing...")
    usernames = [
                'bjoubs',
                 'KingKrab',
                 'raymondeezy',
                 'meganyip1211',
                 'GeoMoD',
                 'ArnoZeld',
                 "BrittWilliamss",
                 "emilylush11",
                 "sarasantos28"
                 ]
    
    movie_titles = [
        "The count of monte cristo 2024", 
        "E.T. the Extra-Terrestrial",
        "My Neighbor Totoro",
        "Everybody Wants Some",
        "Portrait of a lady on fire",
        "Dead Poets Society",
        "Schindler's list"
    ]

    # Stats
    user_stats = defaultdict(lambda: {
        'watched': 0,
        'ratings': [],
        'reviews': 0,
        'words': [],
    })

    movie_ratings = defaultdict(list)
    first_watch = defaultdict(list)
    longest_review = {'user': None, 'words': 0, 'title': None, 'url': None}
    shortest_review = {'user': None, 'words': float('inf'), 'title': None, 'url': None}

    user_movie_pairs = [(username, title) for title in movie_titles for username in usernames]

    logs_by_user_movie = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user_movie = {
            executor.submit(get_all_user_logs, username, title): (username, title)
            for username, title in user_movie_pairs
        }

        for future in as_completed(future_to_user_movie):
            username, title = future_to_user_movie[future]
            try:
                logs = future.result()
                logs_by_user_movie[(username, title)] = logs
            except Exception as e:
                print(f"Error with {username} - {title}: {e}")

            if logs:
                user_stats[username]['watched'] += 1
                for log in logs:
                    movie_ratings[title].append(log['rating'])

                    if log['rating'] is not None:
                        user_stats[username]['ratings'].append(log['rating'])

                    if log['has_review']:
                        user_stats[username]['reviews'] += 1
                        user_stats[username]['words'].append(log['word_count'])

                        # Track longest and shortest reviews
                        if log['word_count'] > longest_review['words']:
                            longest_review.update({'user': username, 'words': log['word_count'], 'title': log['title'], 'url': log['url']})
                        if log['word_count'] < shortest_review['words'] and log['word_count'] > 0:
                            shortest_review.update({'user': username, 'words': log['word_count'], 'title': log['title'], 'url': log['url']})

                    # First to log a movie
                    first_watch[title].append((log['date'], username))

    # Summary
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
    #most_divisive = max(movie_ratings.items(), key=lambda x: statistics.stdev([r for r in x[1] if r is not None]) if len(x[1]) > 1 else 0)

    if movie_ratings:
        most_divisive = max(
            movie_ratings.items(),
            key=lambda x: statistics.stdev([r for r in x[1] if r is not None]) if len(x[1]) > 1 else 0,
            default=("No movies", [])
        )
        most_divisive_stddev = round(statistics.stdev([r for r in most_divisive[1] if r is not None]), 2) if len(most_divisive[1]) > 1 else 0
    else:
        most_divisive = ("No movies", [])
        most_divisive_stddev = 0

    # Most liked / disliked movie
    averages = {movie: sum(r for r in ratings if r is not None) / len([r for r in ratings if r is not None]) for movie, ratings in movie_ratings.items()}
    most_liked = max(averages.items(), key=lambda x: x[1])
    least_liked = min(averages.items(), key=lambda x: x[1])

    context = {
        "summary": summary,
        "most_divisive": most_divisive,
        "most_divisive_stddev": most_divisive_stddev,
        "most_liked": most_liked,
        "least_liked": least_liked,
        "longest_review": longest_review,
        "shortest_review": shortest_review,
        "first_watch": first_watch,
    }

    save_cache(context)
    return render_template('index.html', **context)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render provides PORT env variable
    app.run(host='0.0.0.0', port=port)