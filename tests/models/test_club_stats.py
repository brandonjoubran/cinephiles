from models.club_stats import ClubStats, FilmHighlight


def test_club_stats_creation():
    stats = ClubStats(
        total_movies=10,
        total_reviews=5,
        average_rating=3.5,
        highest_rated=FilmHighlight(title="The Substance", slug="the-substance", value=4.5),
        lowest_rated=FilmHighlight(title="Dune: Part Two", slug="dune-part-two", value=2.0),
        most_divisive=FilmHighlight(title="Dune: Part Two", slug="dune-part-two", value=1.5),
        longest_review=FilmHighlight(title="The Substance", slug="the-substance", value=300),
    )
    assert stats.total_movies == 10
    assert stats.highest_rated.title == "The Substance"
    assert stats.most_divisive.value == 1.5


def test_club_stats_with_none_highlights():
    stats = ClubStats(
        total_movies=0,
        total_reviews=0,
        average_rating=0,
        highest_rated=None,
        lowest_rated=None,
        most_divisive=None,
        longest_review=None,
    )
    assert stats.highest_rated is None
    assert stats.lowest_rated is None


def test_club_stats_serializes_to_dict():
    stats = ClubStats(
        total_movies=10,
        total_reviews=5,
        average_rating=3.5,
        highest_rated=FilmHighlight(title="The Substance", slug="the-substance", value=4.5),
        lowest_rated=None,
        most_divisive=None,
        longest_review=None,
    )
    d = stats.model_dump()
    assert d["total_movies"] == 10
    assert d["highest_rated"]["title"] == "The Substance"
    assert d["lowest_rated"] is None
