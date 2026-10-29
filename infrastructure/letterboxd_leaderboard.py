"""Scrape Letterboxd profile stats for the leaderboard page (same as aaa-old)."""
import re

from bs4 import BeautifulSoup

from infrastructure import http


def get_user_films_watched_this_year(username: str) -> int | None:
    url = f"https://letterboxd.com/{username}/"
    try:
        response = http.get(url)
        response.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    user_stats_element = soup.select_one("div.profile-stats.js-profile-stats")
    if not user_stats_element:
        return None

    user_stats_individual_elements = user_stats_element.select("h4.profile-statistic.statistic")
    target_element = None

    if len(user_stats_individual_elements) >= 2:
        target_element = user_stats_individual_elements[1]
        definition = target_element.select_one("span.definition")
        if definition and definition.get_text(strip=True) != "This year":
            return 0
    else:
        target_element = user_stats_element.select_one('a[href$="/films/"] span.value') or user_stats_element.select_one(
            "span.value"
        )

    if not target_element:
        return None

    digits = re.sub(r"[^\d]", "", target_element.get_text(strip=True))
    if not digits:
        return None
    return int(digits)
