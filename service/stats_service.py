from statistics import stdev
import repository.film_log_repository as film_log_repo
from models.film_log import FilmLog
from models.user_stats import UserStats
from models.club_stats import ClubStats, FilmHighlight


def _build_user_stats(username: str, logs: list[FilmLog]) -> UserStats:
    reviews = [log for log in logs if log.has_review]
    total_words = sum(r.word_count for r in reviews)

    return UserStats(
        username=username,
        movies_watched=len(logs),
        average_rating=round(sum(log.rating for log in logs) / len(logs), 2) if logs else 0,
        num_reviews=len(reviews),
        avg_words_per_review=round(total_words / len(reviews), 2) if reviews else 0,
    )


def get_all_user_stats() -> list[UserStats]:
    all_logs = film_log_repo.get_all_film_logs()
    usernames = set(log.username for log in all_logs)

    stats = []
    for username in usernames:
        user_logs = [log for log in all_logs if log.username == username]
        stats.append(_build_user_stats(username, user_logs))

    return stats


def get_club_stats() -> ClubStats:
    all_logs = film_log_repo.get_all_film_logs()
    rated_logs = [log for log in all_logs if log.rating > 0]
    reviews = [log for log in all_logs if log.has_review]

    # Group ratings by film slug
    films: dict[str, list[FilmLog]] = {}
    for log in rated_logs:
        films.setdefault(log.slug, []).append(log)

    # Average rating per film
    film_averages = {}
    for slug, logs in films.items():
        film_averages[slug] = {
            "title": logs[0].title,
            "avg": round(sum(log.rating for log in logs) / len(logs), 2),
        }

    highest_rated = None
    lowest_rated = None
    if film_averages:
        best_slug = max(film_averages, key=lambda s: film_averages[s]["avg"])
        worst_slug = min(film_averages, key=lambda s: film_averages[s]["avg"])
        highest_rated = FilmHighlight(title=film_averages[best_slug]["title"], slug=best_slug, value=film_averages[best_slug]["avg"])
        lowest_rated = FilmHighlight(title=film_averages[worst_slug]["title"], slug=worst_slug, value=film_averages[worst_slug]["avg"])

    # Most divisive: highest standard deviation (needs 2+ ratings)
    most_divisive = None
    films_with_multiple = {slug: logs for slug, logs in films.items() if len(logs) >= 2}
    if films_with_multiple:
        divisive_slug = max(films_with_multiple, key=lambda s: stdev(log.rating for log in films_with_multiple[s]))
        deviation = round(stdev(log.rating for log in films_with_multiple[divisive_slug]), 2)
        most_divisive = FilmHighlight(title=films[divisive_slug][0].title, slug=divisive_slug, value=deviation)

    # Longest review
    longest_review = None
    if reviews:
        longest = max(reviews, key=lambda log: log.word_count)
        longest_review = FilmHighlight(title=longest.title, slug=longest.slug, value=longest.word_count)

    total_ratings = [log.rating for log in rated_logs]

    return ClubStats(
        total_movies=len(films),
        total_reviews=len(reviews),
        average_rating=round(sum(total_ratings) / len(total_ratings), 2) if total_ratings else 0,
        highest_rated=highest_rated,
        lowest_rated=lowest_rated,
        most_divisive=most_divisive,
        longest_review=longest_review,
    )
