from models.user_stats import UserStats


def test_user_stats_creation():
    stats = UserStats(
        username="bjoubs",
        movies_watched=50,
        average_rating=3.75,
        num_reviews=10,
        avg_words_per_review=85.5,
    )
    assert stats.username == "bjoubs"
    assert stats.movies_watched == 50
    assert stats.average_rating == 3.75
    assert stats.num_reviews == 10
    assert stats.avg_words_per_review == 85.5


def test_user_stats_serializes_to_dict():
    stats = UserStats(
        username="bjoubs",
        movies_watched=50,
        average_rating=3.75,
        num_reviews=10,
        avg_words_per_review=85.5,
    )
    d = stats.model_dump()
    assert d == {
        "username": "bjoubs",
        "movies_watched": 50,
        "average_rating": 3.75,
        "num_reviews": 10,
        "avg_words_per_review": 85.5,
    }
