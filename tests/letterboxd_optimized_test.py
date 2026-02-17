import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import time
from cache import *
from scraper_optimized import get_all_user_logs
from utils_optimized import get_rotw_counts, build_stats
from db import get_watchlist_sheet, get_users_sheet, get_nominations_sheet, get_selected_sheet, get_meetings_sheet, get_selected_records, get_meetings_records


def test():
    start_time = time.time()  # Start timer for the entire function

    logs_by_user = {}
    rotw_counts = {}
    
    # 🔧 Load the cache if it exists
    cache = load_all_stats_caches_in_memory()
    print(cache)
    print(cache is not None)

    user_sheet = get_users_sheet()
    usernames = [row[0] for row in user_sheet.get_all_values()[1:]]
    users_joins = [row[1] for row in user_sheet.get_all_values()[1:]]
    print(f"User joins: {users_joins}")
    selected_sheet = get_selected_sheet()
    selected_records = selected_sheet.get_all_records()
    selected_slugs = [row["SLUG"] for row in selected_records if "SLUG" in row]
    selected_dates = [row["WATCHED_DATE"] for row in selected_records if "WATCHED_DATE" in row]
    print(f"Selected slugs: {selected_slugs}")
    print(f"Selected dates: {selected_dates}")
    movies_after_date_object = movies_after_date(dict(zip(usernames, users_joins)), dict(zip(selected_slugs, selected_dates)))

    if cache is not None:
        print('here')
        # usernames = ['bjoubs', 'KingKrab', 'GeoMoD', 'mskills43', 'raymondeezy']
        for username in usernames:
            if username in cache and cache[username] != {} and 'films' in cache.get(username, {}) and cache[username]['films'] != {}:
                print(f"Using cached films for {username}")
                logs_by_user[username] = cache[username]['films']
            else:
                print(f"♻️ Recomputing films cache for {username}")
                logs_by_user[username] = get_all_user_logs(username, selected_slugs)[username]['films']
            if username in cache and cache[username] != {} and 'stats' in cache.get(username, {}) and cache[username]['stats'] != {}:
                print(f"Using cached stats for {username}")
                rotw_counts[username] = cache[username]
            else:
                print(f"♻️ Recomputing stats cache for {username}")
                rotw_counts = get_rotw_counts(selected_records)

    end_time = time.time()
    print(f"✅ Total index() execution time: {end_time - start_time:.2f} seconds")
    print(f"Logs by user: {logs_by_user}")
    print(f"ROTW counts: {rotw_counts}")
    print(f"Stats: {build_stats(logs_by_user, selected_records, rotw_counts, movies_after_date_object)}")

from datetime import datetime

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

test()
