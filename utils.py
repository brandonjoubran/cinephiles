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

def build_stats(logs_by_user, selected_records, rotw_counts):
    stats = defaultdict(lambda: {'watched': 0, 'ratings': [], 'reviews': 0, 'words': [], 'rotw_count': 0})
    movie_ratings = defaultdict(list)
    first_watch = defaultdict(list)
    longest = {'user': None, 'words': 0, 'title': None, 'url': None}
    shortest = {'user': None, 'words': float('inf'), 'title': None, 'url': None}

    # Process logs by user
    for username, logs in logs_by_user.items():
        for log in logs:
            title = log['title']
            stats[username]['watched'] += 1

            if log.get('rating') is not None:
                stats[username]['ratings'].append(log['rating'])
                movie_ratings[title].append(log['rating'])

            if log.get('has_review'):
                stats[username]['reviews'] += 1
                word_count = log.get('word_count', 0)
                stats[username]['words'].append(word_count)

                if word_count > longest['words']:
                    longest = {
                        'user': username,
                        'words': word_count,
                        'title': title,
                        'url': log['url']
                    }

                if 0 < word_count < shortest['words']:
                    shortest = {
                        'user': username,
                        'words': word_count,
                        'title': title,
                        'url': log['url']
                    }

            first_watch[title].append((log['date'], username))

    # Add ROTW counts from the cache
    for username, count in rotw_counts.items():
        stats[username]['rotw_count'] = count

    # Summary stats per user
    summary = []
    for username in sorted(stats, key=lambda u: stats[u]['watched'], reverse=True):
        user_stats = stats[username]
        summary.append({
            'username': username,
            'watched': user_stats['watched'],
            'avg_rating': round(sum(user_stats['ratings']) / len(user_stats['ratings']), 2) if user_stats['ratings'] else 0,
            'reviews': user_stats['reviews'],
            'avg_words': round(sum(user_stats['words']) / len(user_stats['words']), 1) if user_stats['words'] else 0,
            'rotw_count': user_stats['rotw_count']  # Add ROTW count to the summary
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
        valid = [r for r in ratings if r is not None]
        if valid:
            averages[movie] = sum(valid) / len(valid)

    most_liked = max(averages.items(), key=lambda x: x[1], default=("N/A", 0))
    least_liked = min(averages.items(), key=lambda x: x[1], default=("N/A", 0))

    for title in first_watch:
        first_watch[title] = sorted(first_watch[title])

    return {
        'summary': summary,
        'most_divisive': divisive,
        'most_divisive_stddev': divisive_std,
        'most_liked': most_liked,
        'least_liked': least_liked,
        'longest_review': longest,
        'shortest_review': shortest,
        'first_watch': first_watch
    }