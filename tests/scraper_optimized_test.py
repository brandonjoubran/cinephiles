import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# now safe to import project modules
from scraper_optimized import *

single_user = "bjoubs"
all_users  = [
        "bjoubs",
        "KingKrab",
        "raymondeezy",
        "GeoMoD",
        "meganyip1211",
        "ArnoZeld",
        "sarasantos28",
        "BrittWilliamss",
        "emilylush11",
        "dantheman1836",
        "eyz00",
        "mskills43",
    ]

all_slugs = [
    "the-count-of-monte-cristo-2024",
    "et-the-extra-terrestrial",
    "my-neighbor-totoro",
    "portrait-of-a-lady-on-fire",
    "everybody-wants-some",
    "dead-poets-society",
    "schindlers-list",
    "children-of-men",
    "the-shawshank-redemption",
    "eyes-wide-shut",
    "the-hunt-2012",
    "brazil",
    "blue-valentine",
    "moonrise-kingdom",
    "the-fantastic-4-first-steps",
    "amelie",
    "the-florida-project",
    "rain-man",
    "moneyball",
    "the-thing",
    "the-rocky-horror-picture-show",
    "titanic-1997",
    "inglourious-basterds",
    "die-hard",
    "the-nightmare-before-christmas",
]

def test_get_user_number_of_movies_watched():
    # Test with a valid username
    print(f"Testing user: {single_user}...")
    count = get_user_number_of_movies_watched(single_user)
    print(f"Number of movies watched by {single_user}: {count}")

def test_get_all_users_number_of_movies_watched():
    print(f"Testing all users number of movies watched  ...")
    for username in all_users:
        count = get_user_number_of_movies_watched(username)
        print(f"Number of movies watched by {username}: {count}")

def test_get_single_user_stats_from_tag_page_all_slugs():
    print(f"Testing user: {single_user} stats...")
    start_time = time.time()
    logs = get_all_user_logs(single_user, all_slugs)
    end_time = time.time()
    print(f"Found {len(logs)} movies for {single_user} in {end_time - start_time} seconds")
    for log in logs:
        print(f"  - {log['slug']} ({log['title']}): {log['rating']}⭐, {log['word_count']} words")

def test_get_all_users_stats_from_tag_page_all_slugs():
    for username in all_users:
        start_time = time.time()
        logs = get_all_user_logs(username, all_slugs)
        end_time = time.time()
        print(f"Found {len(logs)} movies for {username} in {end_time - start_time} seconds")
        for log in logs:
            print(f"  - {log['slug']} ({log['title']}): {log['rating']}⭐, {log['word_count']} words")

# test_get_user_number_of_movies_watched()
test_get_all_users_number_of_movies_watched()
# test_get_single_user_stats_from_tag_page_all_slugs()
# test_get_all_users_stats_from_tag_page_all_slugs()