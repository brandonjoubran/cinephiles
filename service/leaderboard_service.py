"""Leaderboard data for the HTML page (Letterboxd profile scrape per user)."""
import repository.users_repository as users_repo
from infrastructure.letterboxd_leaderboard import get_user_films_watched_this_year


def get_leaderboard() -> dict[str, int]:
    leaderboard: dict[str, int] = {}
    for username in users_repo.get_usernames():
        count = get_user_films_watched_this_year(username)
        leaderboard[username] = count if count is not None else 0
    return dict(sorted(leaderboard.items(), key=lambda item: item[1], reverse=True))
