import requests
from bs4 import BeautifulSoup
import time
import re
from collections import defaultdict
import statistics

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

def get_all_user_logs(username, movie_title, max_pages=3):
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

        time.sleep(1)

    return logs

# Users and movies
usernames = ['bjoubs', 'KingKrab', 'raymondeezy', 'meganyip1211', 'GeoMoD', 'ArnoZeld']
movie_titles = ["The count of monte cristo 2024", 
                "E.T. the Extra-Terrestrial",
                "My Neighbor Totoro",
                "Everybody Wants Some",
                "Portrait of a lady on fire",
                "Schindler's list"]
#movie_titles = ["The count of monte cristo 2024"]

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
    print(f"\n=== {movie_title} ===")
    for username in usernames:
        logs = get_all_user_logs(username, movie_title)

        if logs:
            user_stats[username]['watched'] += 1
            print(f"{username}'s logs for '{movie_title}':")
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

                print(f" - {log['date']}: {log['rating_str']} ({'Review' if log['has_review'] else 'No review'}) {log['url']}")
        else:
            print(f"No logs found for '{movie_title}' by {username}.")

# Summary
print("\n=== Summary ===")
for username in sorted(user_stats, key=lambda u: user_stats[u]['watched'], reverse=True):
    stats = user_stats[username]
    avg_rating = round(sum(stats['ratings']) / len(stats['ratings']), 2) if stats['ratings'] else 0
    avg_words = round(sum(stats['words']) / len(stats['words']), 1) if stats['words'] else 0
    print(f"{username}: {stats['watched']} movies watched, avg rating {avg_rating}, {stats['reviews']} written reviews, avg words {avg_words}")

# Most divisive movie
most_divisive = max(movie_ratings.items(), key=lambda x: statistics.stdev([r for r in x[1] if r is not None]) if len(x[1]) > 1 else 0)
print(f"\nMost divisive movie: {most_divisive[0]} (std dev: {round(statistics.stdev(most_divisive[1]), 2)})")

# Most liked / disliked movie
averages = {movie: sum(r for r in ratings if r is not None) / len([r for r in ratings if r is not None]) for movie, ratings in movie_ratings.items()}
most_liked = max(averages.items(), key=lambda x: x[1])
least_liked = min(averages.items(), key=lambda x: x[1])
print(f"Most liked movie: {most_liked[0]} ({round(most_liked[1], 2)}⭐)")
print(f"Least liked movie: {least_liked[0]} ({round(least_liked[1], 2)}⭐)")

# Longest / Shortest review
print(f"\nLongest review: {longest_review['words']} words by {longest_review['user']} on '{longest_review['title']}' → {longest_review['url']}")
print(f"Shortest review: {shortest_review['words']} words by {shortest_review['user']} on '{shortest_review['title']}' → {shortest_review['url']}")

# First watchers
print("\n=== First to Watch Each Movie ===")
for movie, watches in first_watch.items():
    sorted_watches = sorted([w for w in watches if w[0] != 'Unknown date'])
    if sorted_watches:
        print(f"{movie}: {sorted_watches[0][1]} on {sorted_watches[0][0]}")
