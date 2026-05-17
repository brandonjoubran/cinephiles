"""Pick random club members to nominate for the next film."""
import random

from fastapi import HTTPException

import repository.film_log_repository as film_log_repo
import repository.selected_repository as selected_repo
import repository.users_repository as users_repo

NOMINATOR_COUNT = 3


def generate_nominators(count: int = NOMINATOR_COUNT) -> tuple[str, list[str]]:
    """Return up to ``count`` random users who watched the latest completed club film.

    Uses the last entry on the Selected sheet and FilmLog (same data as post-complete RSS sync).
    """
    movie_slug = selected_repo.get_latest_completed_slug()
    if not movie_slug:
        raise HTTPException(
            status_code=400,
            detail="No completed club films on the Selected sheet.",
        )

    watched = {name.lower() for name in film_log_repo.get_usernames_for_slug(movie_slug)}
    eligible = [
        username
        for username in users_repo.get_usernames()
        if username.lower() in watched
    ]

    pick_count = min(count, len(eligible))
    if pick_count == 0:
        return movie_slug, []

    return movie_slug, random.sample(eligible, pick_count)
