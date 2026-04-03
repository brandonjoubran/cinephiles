from unittest.mock import patch
from models.film_log import FilmLog
from service.stats_service import get_all_user_stats, _build_user_stats, get_club_stats

FAKE_LOGS = [
    FilmLog(username="bjoubs", slug="the-substance", title="The Substance", rating=4.0, has_review=True, word_count=120, review_link="https://example.com", updated_at="2025-03-01"),
    FilmLog(username="bjoubs", slug="dune-part-two", title="Dune: Part Two", rating=3.0, has_review=False, word_count=0, review_link="", updated_at="2025-03-02"),
    FilmLog(username="kingkrab", slug="dune-part-two", title="Dune: Part Two", rating=4.5, has_review=True, word_count=80, review_link="https://example.com", updated_at="2025-03-02"),
]


# ── _build_user_stats ────────────────────────────────────────────────────────

def test_build_user_stats_computes_movies_watched():
    bjoubs_logs = [r for r in FAKE_LOGS if r.username == "bjoubs"]
    stats = _build_user_stats("bjoubs", bjoubs_logs)
    assert stats.movies_watched == 2


def test_build_user_stats_computes_average_rating():
    bjoubs_logs = [r for r in FAKE_LOGS if r.username == "bjoubs"]
    stats = _build_user_stats("bjoubs", bjoubs_logs)
    assert stats.average_rating == 3.5


def test_build_user_stats_computes_num_reviews():
    bjoubs_logs = [r for r in FAKE_LOGS if r.username == "bjoubs"]
    stats = _build_user_stats("bjoubs", bjoubs_logs)
    assert stats.num_reviews == 1


def test_build_user_stats_computes_avg_words_per_review():
    bjoubs_logs = [r for r in FAKE_LOGS if r.username == "bjoubs"]
    stats = _build_user_stats("bjoubs", bjoubs_logs)
    assert stats.avg_words_per_review == 120.0


def test_build_user_stats_no_reviews_returns_zero_avg_words():
    logs = [FilmLog(username="x", slug="a", title="A", rating=3.0, has_review=False, word_count=0, review_link="", updated_at="2025-01-01")]
    stats = _build_user_stats("x", logs)
    assert stats.num_reviews == 0
    assert stats.avg_words_per_review == 0


def test_build_user_stats_empty_logs():
    stats = _build_user_stats("nobody", [])
    assert stats.movies_watched == 0
    assert stats.average_rating == 0
    assert stats.num_reviews == 0
    assert stats.avg_words_per_review == 0


# ── get_all_user_stats ────────────────────────────────────────────────────────

def _patch_repos(logs, usernames):
    return (
        patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=logs),
        patch("service.stats_service.users_repo.get_usernames", return_value=usernames),
    )


def test_get_all_user_stats_returns_one_entry_per_user():
    logs_patch, users_patch = _patch_repos(FAKE_LOGS, ["bjoubs", "kingkrab"])
    with logs_patch, users_patch:
        result = get_all_user_stats()
    usernames = [s.username for s in result]
    assert sorted(usernames) == ["bjoubs", "kingkrab"]


def test_get_all_user_stats_correct_values():
    logs_patch, users_patch = _patch_repos(FAKE_LOGS, ["bjoubs", "kingkrab"])
    with logs_patch, users_patch:
        result = get_all_user_stats()
    by_name = {s.username: s for s in result}

    assert by_name["bjoubs"].movies_watched == 2
    assert by_name["bjoubs"].average_rating == 3.5
    assert by_name["kingkrab"].movies_watched == 1
    assert by_name["kingkrab"].average_rating == 4.5


def test_get_all_user_stats_includes_user_with_no_logs():
    logs_patch, users_patch = _patch_repos(FAKE_LOGS, ["bjoubs", "kingkrab", "newuser"])
    with logs_patch, users_patch:
        result = get_all_user_stats()
    by_name = {s.username: s for s in result}

    assert by_name["newuser"].movies_watched == 0
    assert by_name["newuser"].average_rating == 0


def test_get_all_user_stats_empty():
    logs_patch, users_patch = _patch_repos([], [])
    with logs_patch, users_patch:
        result = get_all_user_stats()
    assert result == []


# ── get_club_stats ────────────────────────────────────────────────────────────

def test_club_stats_total_movies():
    with patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=FAKE_LOGS):
        result = get_club_stats()
    assert result.total_movies == 2


def test_club_stats_total_reviews():
    with patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=FAKE_LOGS):
        result = get_club_stats()
    assert result.total_reviews == 2


def test_club_stats_average_rating():
    with patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=FAKE_LOGS):
        result = get_club_stats()
    assert result.average_rating == 3.83


def test_club_stats_highest_rated():
    with patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=FAKE_LOGS):
        result = get_club_stats()
    assert result.highest_rated.title == "The Substance"
    assert result.highest_rated.value == 4.0


def test_club_stats_lowest_rated():
    with patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=FAKE_LOGS):
        result = get_club_stats()
    assert result.lowest_rated.title == "Dune: Part Two"
    assert result.lowest_rated.value == 3.75


def test_club_stats_most_divisive():
    with patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=FAKE_LOGS):
        result = get_club_stats()
    assert result.most_divisive.title == "Dune: Part Two"
    assert result.most_divisive.value == 1.06


def test_club_stats_longest_review():
    with patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=FAKE_LOGS):
        result = get_club_stats()
    assert result.longest_review.title == "The Substance"
    assert result.longest_review.value == 120


def test_club_stats_empty():
    with patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=[]):
        result = get_club_stats()
    assert result.total_movies == 0
    assert result.total_reviews == 0
    assert result.average_rating == 0
    assert result.highest_rated is None
    assert result.lowest_rated is None
    assert result.most_divisive is None
    assert result.longest_review is None


def test_club_stats_single_rating_no_divisive():
    logs = [FilmLog(username="bjoubs", slug="x", title="X", rating=4.0, has_review=False, word_count=0, review_link="", updated_at="2025-01-01")]
    with patch("service.stats_service.film_log_repo.get_all_film_logs", return_value=logs):
        result = get_club_stats()
    assert result.most_divisive is None
