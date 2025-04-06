from flask import Flask, render_template
from collections import defaultdict
import statistics
import requests
from bs4 import BeautifulSoup
import time
import re

app = Flask(__name__)

# Include all your existing functions here (slugify, extract_full_date, parse_rating, count_review_words, get_all_user_logs)

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
    usernames = ['bjoubs',
                 'KingKrab',
                 'raymondeezy',
                 'meganyip1211',
                 'GeoMoD',
                 'ArnoZeld',
                 "BrittWilliamss",
                 "emilylush11",
                 "sarasantos28"]
    
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

    for movie_title in movie_titles:
        for username in usernames:
            logs = get_all_user_logs(username, movie_title)

            if logs:
                user_stats[username]['watched'] += 1
                for log in logs:
                    movie_ratings[movie_title].append(log['rating'])

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
                    first_watch[movie_title].append((log['date'], username))

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

    return render_template('index.html', summary=summary, most_divisive=most_divisive, most_divisive_stddev=most_divisive_stddev, most_liked=most_liked, least_liked=least_liked, longest_review=longest_review, shortest_review=shortest_review, first_watch=first_watch)

if __name__ == '__main__':
    app.run(debug=True)