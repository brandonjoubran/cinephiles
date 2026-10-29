"""Build template context for the Stats (index) page — same shape as the old Flask app."""
from __future__ import annotations

import re
import statistics
import time
from collections import defaultdict
from datetime import datetime

import repository.film_log_repository as film_log_repo
import repository.meetings_repository as meetings_repo
import repository.selected_repository as selected_repo
import repository.users_repository as users_repo
def _normalize_film_title_for_stats(title: str) -> str:
    if not title or not isinstance(title, str):
        return title or "Unknown"
    t = title.strip()
    if " review of " in t:
        for prefix in ("A ", "An "):
            if t.startswith(prefix) and " review of " in t:
                t = t.split(" review of ", 1)[-1]
                break
    if " by " in t:
        t = t.split(" by ")[0].strip()
    if " • " in t:
        t = t.split(" • ")[0].strip()
    if t and t[-1] == ")" and "(" in t:
        last_open = t.rfind("(")
        suffix = t[last_open:]
        if "⭐" in suffix or re.match(r"^\(\d\.?\d*\)$", suffix):
            t = t[:last_open].strip().rstrip()
    return t or title


def _movies_after_date(join_dates: dict[str, str], watched_dates: dict[str, str]) -> dict[str, int]:
    date_format = "%m/%d/%Y"
    movie_dates = [
        datetime.strptime(date, date_format)
        for date in watched_dates.values()
        if date
    ]
    result = {}
    for person, person_date in join_dates.items():
        person_dt = datetime.strptime(person_date, date_format)
        result[person] = sum(1 for movie_dt in movie_dates if movie_dt >= person_dt)
    return result


def _logs_by_user_from_film_log() -> dict[str, dict[str, dict]]:
    logs_by_user: dict[str, dict[str, dict]] = defaultdict(dict)
    for log in film_log_repo.get_all_film_logs():
        logs_by_user[log.username][log.slug] = {
            "title": log.title,
            "rating": log.rating if log.rating else None,
            "has_review": log.has_review,
            "word_count": log.word_count,
            "review_link": log.review_link,
        }
    return logs_by_user


def _rotw_count_by_user() -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for name in meetings_repo.get_rotw_winners():
        counts[name] += 1
    return counts


def build_stats_page_context() -> dict:
    logs_by_user = _logs_by_user_from_film_log()
    selected_records = [
        {"SLUG": film.slug, "WATCHED_DATE": film.watched_date}
        for film in selected_repo.get_all_selected()
    ]
    rotw_counts = _rotw_count_by_user()
    join_dates = users_repo.get_join_dates()
    watched_by_slug = {film.slug: film.watched_date for film in selected_repo.get_all_selected()}
    movies_after = _movies_after_date(join_dates, watched_by_slug)

    stats = defaultdict(lambda: {"watched": 0, "ratings": [], "reviews": 0, "words": [], "rotw_count": 0})
    movie_ratings: dict[str, list[float]] = defaultdict(list)
    longest = {"user": None, "words": 0, "title": None, "url": None}
    shortest = {"user": None, "words": float("inf"), "title": None, "url": None}

    for username, logs in logs_by_user.items():
        for user_log_data in logs.values():
            title_key = _normalize_film_title_for_stats(user_log_data["title"])
            stats[username]["watched"] += 1
            if user_log_data.get("rating") is not None:
                stats[username]["ratings"].append(user_log_data["rating"])
                movie_ratings[title_key].append(user_log_data["rating"])

            if user_log_data.get("has_review"):
                stats[username]["reviews"] += 1
                word_count = user_log_data.get("word_count", 0)
                stats[username]["words"].append(word_count)

                if word_count > longest["words"]:
                    longest = {
                        "user": username,
                        "words": word_count,
                        "title": title_key,
                        "url": user_log_data["review_link"],
                    }

                if 0 < word_count < shortest["words"]:
                    shortest = {
                        "user": username,
                        "words": word_count,
                        "title": title_key,
                        "url": user_log_data["review_link"],
                    }

        stats[username]["rotw_count"] = rotw_counts.get(username, 0)

    ordered_slugs = [r["SLUG"] for r in selected_records if r.get("SLUG")]

    def _streak(username: str) -> int:
        watched = set(logs_by_user.get(username, {}).keys())
        streak = 0
        for i in range(len(ordered_slugs) - 1, -1, -1):
            if ordered_slugs[i] in watched:
                streak += 1
            else:
                break
        return streak

    summary = []
    for username in sorted(stats, key=lambda u: stats[u]["watched"], reverse=True):
        user_stats = stats[username]
        summary.append({
            "username": username,
            "watched": user_stats["watched"],
            "percentage": int(round(user_stats["watched"] / movies_after[username] * 100, 0))
            if movies_after.get(username) else 0,
            "avg_rating": round(sum(user_stats["ratings"]) / len(user_stats["ratings"]), 2)
            if user_stats["ratings"] else 0,
            "reviews": user_stats["reviews"],
            "avg_words": round(sum(user_stats["words"]) / len(user_stats["words"]), 1)
            if user_stats["words"] else 0,
            "rotw_count": user_stats["rotw_count"],
            "streak": _streak(username),
        })

    divisive = max(
        movie_ratings.items(),
        key=lambda x: statistics.stdev(x[1]) if len(x[1]) > 1 else 0,
        default=("No movies", []),
    )
    divisive_std = round(statistics.stdev(divisive[1]), 2) if len(divisive[1]) > 1 else 0

    averages = {}
    for movie, ratings in movie_ratings.items():
        valid = [r for r in ratings if r is not None]
        if valid:
            averages[movie] = sum(valid) / len(valid)

    most_liked = max(averages.items(), key=lambda x: x[1], default=("N/A", 0))
    least_liked = min(averages.items(), key=lambda x: x[1], default=("N/A", 0))

    ctx = {
        "summary": summary,
        "most_divisive": divisive,
        "most_divisive_stddev": divisive_std,
        "most_liked": most_liked,
        "least_liked": least_liked,
        "longest_review": longest,
        "shortest_review": shortest,
        "total_films": len(selected_records),
        "member_count": len(summary),
        "season_year": time.strftime("%Y"),
    }
    return ctx
