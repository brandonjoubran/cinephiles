from collections import defaultdict
import re
import statistics
import requests

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