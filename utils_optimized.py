from collections import defaultdict
import re
import statistics
import requests
from db import *
from cache import *
from datetime import datetime

def expand_short_url(url):
    try:
        return requests.head(url, allow_redirects=True).url
    except:
        return url

def resolve_letterboxd_url(short_url):
    response = requests.get(short_url, allow_redirects=True)
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

def movies_after_date(people, movies):
    date_format = "%m/%d/%Y"

    # Convert movie dates once
    movie_dates = [
        datetime.strptime(date, date_format)
        for date in movies.values()
    ]

    result = {}

    for person, person_date in people.items():
        person_dt = datetime.strptime(person_date, date_format)

        count = sum(
            1 for movie_dt in movie_dates
            if movie_dt >= person_dt
        )

        result[person] = count

    print(f"Movies after date: {result}")

    return result


def _normalize_film_title_for_stats(title):
    """Use film name only for stats (most liked, least liked, divisive, longest/shortest review). Strips Letterboxd og:title wrappers."""
    if not title or not isinstance(title, str):
        return title or "Unknown"
    t = title.strip()
    # "A ★★★★★ review of City of God (2002) (5.0⭐)" or "An ... review of ..." -> film name only
    if " review of " in t:
        for prefix in ("A ", "An "):
            if t.startswith(prefix) and " review of " in t:
                t = t.split(" review of ", 1)[-1]
                break
    if " by " in t:
        t = t.split(" by ")[0].strip()
    if " • " in t:
        t = t.split(" • ")[0].strip()
    # Trailing " (5.0⭐)" or " (5.0)" is rating; don't strip " (2002)" (year)
    if t and t[-1] == ")" and "(" in t:
        last_open = t.rfind("(")
        suffix = t[last_open:]
        if "⭐" in suffix or re.match(r"^\(\d\.?\d*\)$", suffix):
            t = t[:last_open].strip().rstrip()
    return t or title


def build_stats(logs_by_user, selected_records, rotw_counts, movies_after_date):
    stats = defaultdict(lambda: {'watched': 0, 'ratings': [], 'reviews': 0, 'words': [], 'rotw_count': 0})
    movie_ratings = defaultdict(list)
    longest = {'user': None, 'words': 0, 'title': None, 'url': None}
    shortest = {'user': None, 'words': float('inf'), 'title': None, 'url': None}
    # print(logs_by_user)

    # return
    # Process logs by user
    for username, logs in logs_by_user.items():
        print(f"Processing logs for user: {username}")
        print(f"logs: {logs}")
        print(f"len logs: {len(logs)}")
        # print(f"user_film_logs: {user_film_logs}")
        for key, user_log_data in logs.items():
            print(user_log_data)
            print(f"dfd{key}: {user_log_data}")
            print(user_log_data)
            # return
            title = user_log_data['title']
            title_key = _normalize_film_title_for_stats(title)  # film name only for most/least liked, divisive, longest/shortest
            stats[username]['watched'] += 1
            if user_log_data.get('rating') is not None:
                stats[username]['ratings'].append(user_log_data['rating'])
                movie_ratings[title_key].append(user_log_data['rating'])

            if user_log_data.get('has_review'):
                stats[username]['reviews'] += 1
                word_count = user_log_data.get('word_count', 0)
                stats[username]['words'].append(word_count)

                if word_count > longest['words']:
                    longest = {
                        'user': username,
                        'words': word_count,
                        'title': title_key,
                        'url': user_log_data['review_link']
                    }

                if 0 < word_count < shortest['words']:
                    shortest = {
                        'user': username,
                        'words': word_count,
                        'title': title_key,
                        'url': user_log_data['review_link']
                    }
        # Add ROTW counts from the cache
        # for username, count in rotw_counts.items():
        #     stats[username]['rotw_count'] = count
        print(f"ROTW counts: {rotw_counts} {username} {rotw_counts.get(username, 0)}")
        if username in rotw_counts:
            print(rotw_counts[username])
            stats[username]['rotw_count'] = rotw_counts.get(username, {}).get('stats', {}).get('rotw_count', 0)
        else:
            stats[username]['rotw_count'] = 0
        print(stats[username]['rotw_count'])

    # Streak: consecutive films watched from the end of the list (ordered by selected_records)
    ordered_slugs = [r['SLUG'] for r in selected_records if r.get('SLUG')]

    def _streak(username):
        watched = set(logs_by_user.get(username, {}).keys())
        streak = 0
        for i in range(len(ordered_slugs) - 1, -1, -1):
            if ordered_slugs[i] in watched:
                streak += 1
            else:
                break
        return streak

    # Summary stats per user
    summary = []
    for username in sorted(stats, key=lambda u: stats[u]['watched'], reverse=True):
        user_stats = stats[username]
        streak = _streak(username)
        summary.append({
            'username': username,
            'watched': user_stats['watched'],
            'percentage': int(round(user_stats['watched'] / movies_after_date[username] * 100, 0)) if len(selected_records) > 0 else 0,
            'avg_rating': round(sum(user_stats['ratings']) / len(user_stats['ratings']), 2) if user_stats['ratings'] else 0,
            'reviews': user_stats['reviews'],
            'avg_words': round(sum(user_stats['words']) / len(user_stats['words']), 1) if user_stats['words'] else 0,
            'rotw_count': user_stats['rotw_count'],
            'streak': streak,
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
        print(f"Movie: {movie}, Ratings: {ratings}")
        valid = [r for r in ratings if r is not None]
        if valid:
            averages[movie] = sum(valid) / len(valid)

    most_liked = max(averages.items(), key=lambda x: x[1], default=("N/A", 0))
    least_liked = min(averages.items(), key=lambda x: x[1], default=("N/A", 0))

    return {
        'summary': summary,
        'most_divisive': divisive,
        'most_divisive_stddev': divisive_std,
        'most_liked': most_liked,
        'least_liked': least_liked,
        'longest_review': longest,
        'shortest_review': shortest,
    }

def build_stats_optimized(logs_by_user, selected_records, rotw_counts):
    stats = defaultdict(lambda: {'watched': 0, 'ratings': [], 'reviews': 0, 'words': [], 'rotw_count': 0, 'review_link': ''})
    movie_ratings = defaultdict(list)
    longest = {'user': None, 'words': 0, 'title': None, 'url': None}
    shortest = {'user': None, 'words': float('inf'), 'title': None, 'url': None}
    for username, data in logs_by_user.items():
        pass

def get_users_watched_summary(user_film_logs, username):
    user_stats = defaultdict(lambda: {'username': username, 'watched': 0, 'avg_rating': 0, 'reviews': 0, 'avg_words': 0, 'rotw_count': 0})
    film_stats = defaultdict(lambda: {'slug': 0, 'title': 0, 'ratings_list': 0, 'review_count_list': 0})
    number_of_movies_watched = len(user_film_logs)
    rating_sum = 0
    number_of_reviews = 0
    review_length_sum = 0

    for log in user_film_logs:
        if log.get('rating') is not None:
            rating_sum += log['rating']
            film_stats[log['slug']]['ratings_list'].append(log['rating'])
        if log.get('has_review'):
            number_of_reviews += 1
            review_length_sum += log.get('word_count', 0)

    user_stats['watched'] = number_of_movies_watched
    user_stats['avg_rating'] = round(rating_sum / number_of_movies_watched, 2) if number_of_movies_watched > 0 else 0
    user_stats['reviews'] = number_of_reviews
    user_stats['avg_words'] = round(review_length_sum / number_of_reviews, 1) if number_of_reviews > 0 else 0

    

def get_rotw_counts(selected_records):
    rotw_counts = {}
    for record in selected_records:
            rotw_value = record.get("ROTW", "")
            if rotw_value:
                for username in map(str.strip, rotw_value.split(",")):
                    rotw_counts.setdefault(username, {}).setdefault("stats", {})
                    if rotw_counts[username]["stats"].get("rotw_count") is not None:
                        rotw_counts[username]["stats"]["rotw_count"] += 1
                    else:
                        rotw_counts[username]["stats"]["rotw_count"] = 1
    cache_rotw_counts(rotw_counts)
    return rotw_counts

def cache_rotw_counts(rotw_counts):
    print(f"Caching ROTW counts: {rotw_counts}")
    for username, data in rotw_counts.items():
        user_cache = load_stats_cache(username)
        user_cache.setdefault(username, {}).setdefault("stats", {})
        user_cache[username]['stats'] = data.get('stats', {})
        print(f"Saving ROTW count for {username}: {user_cache[username]['stats']}")
        save_stats_cache(username, user_cache)

# selected_sheet = get_selected_sheet()
# selected_records = selected_sheet.get_all_records()
# selected_slugs = [row["SLUG"] for row in selected_records if "SLUG" in row]

# print(get_rotw_counts(selected_records))

