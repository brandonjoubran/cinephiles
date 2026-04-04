import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from models.movie import Movie, MovieStatus
from service.movies_service import (
    add_movie,
    toggle_nomination,
    toggle_vote,
    toggle_selection,
    complete_movie,
    delete_movie,
    get_movie_by_slug,
)


def _movie(slug="the-substance", status="backlog", nominated_by="", voted_by=None, **overrides):
    defaults = {
        "title": slug.replace("-", " ").title(),
        "slug": slug,
        "url": f"https://letterboxd.com/film/{slug}/",
        "added_by": "bjoubs",
        "date_added": "01/01/2025",
        "poster": "https://image.tmdb.org/poster.jpg",
        "status": status,
        "nominated_by": nominated_by,
        "voted_by": voted_by or [],
        "watched_date": "",
        "rotw": [],
    }
    defaults.update(overrides)
    return Movie(**defaults)


# ── add_movie ─────────────────────────────────────────────────────────────────

def test_add_movie_creates_with_defaults():
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=None),
        patch("service.movies_service.movies_repo.add_movie") as mock_add,
    ):
        result = add_movie("The Substance", "the-substance", "https://letterboxd.com/film/the-substance/", "bjoubs", "poster.jpg")
    assert result.status == MovieStatus.BACKLOG
    assert result.voted_by == []
    assert result.nominated_by == ""
    mock_add.assert_called_once()


def test_add_movie_rejects_duplicate():
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=_movie()):
        with pytest.raises(HTTPException) as exc:
            add_movie("The Substance", "the-substance", "url", "bjoubs", "poster")
        assert exc.value.status_code == 409


# ── get_movie_by_slug ─────────────────────────────────────────────────────────

def test_get_movie_by_slug_not_found_raises_404():
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=None):
        with pytest.raises(HTTPException) as exc:
            get_movie_by_slug("nonexistent")
        assert exc.value.status_code == 404


# ── nominate_movie ────────────────────────────────────────────────────────────

def test_toggle_nomination_from_backlog():
    movie = _movie(status="backlog")
    nominated = _movie(status="nominated", nominated_by="KingKrab")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, nominated]),
        patch("service.movies_service.movies_repo.get_movies_by_status", return_value=[]),
        patch("service.movies_service.movies_repo.update_movie_fields") as mock_update,
        patch("service.movies_service.nomination_log_repo.add_nomination") as mock_log,
    ):
        result = toggle_nomination("the-substance", "KingKrab")
    mock_update.assert_called_once()
    mock_log.assert_called_once()
    assert result.status == MovieStatus.NOMINATED


def test_toggle_nomination_rejects_when_movie_selected():
    movie = _movie(status="backlog")
    selected = _movie(slug="anora", status="selected")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie),
        patch("service.movies_service.movies_repo.get_movies_by_status", return_value=[selected]),
    ):
        with pytest.raises(HTTPException) as exc:
            toggle_nomination("the-substance", "KingKrab")
        assert exc.value.status_code == 400
        assert "selected" in exc.value.detail.lower()


def test_toggle_nomination_back_to_backlog():
    movie = _movie(status="nominated", nominated_by="KingKrab", voted_by=["bjoubs"])
    backlog = _movie(status="backlog")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, backlog]),
        patch("service.movies_service.movies_repo.update_movie_fields") as mock_update,
    ):
        result = toggle_nomination("the-substance", "KingKrab")
    mock_update.assert_called_once_with("the-substance", status="backlog", nominated_by="", voted_by="")
    assert result.status == MovieStatus.BACKLOG


def test_toggle_nomination_rejects_selected():
    movie = _movie(status="selected")
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        with pytest.raises(HTTPException) as exc:
            toggle_nomination("the-substance", "KingKrab")
        assert exc.value.status_code == 400


def test_toggle_nomination_rejects_watched():
    movie = _movie(status="watched")
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        with pytest.raises(HTTPException) as exc:
            toggle_nomination("the-substance", "KingKrab")
        assert exc.value.status_code == 400


# ── toggle_vote ───────────────────────────────────────────────────────────────

def test_toggle_vote_adds_voter():
    movie = _movie(status="nominated", voted_by=[])
    updated = _movie(status="nominated", voted_by=["bjoubs"])
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, updated]),
        patch("service.movies_service.movies_repo.update_movie_fields") as mock_update,
    ):
        result = toggle_vote("the-substance", "bjoubs")
    mock_update.assert_called_once_with("the-substance", voted_by="bjoubs")
    assert result.voted_by == ["bjoubs"]


def test_toggle_vote_removes_voter():
    movie = _movie(status="nominated", voted_by=["bjoubs", "KingKrab"])
    updated = _movie(status="nominated", voted_by=["KingKrab"])
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, updated]),
        patch("service.movies_service.movies_repo.update_movie_fields") as mock_update,
    ):
        result = toggle_vote("the-substance", "bjoubs")
    mock_update.assert_called_once_with("the-substance", voted_by="KingKrab")
    assert result.voted_by == ["KingKrab"]


def test_toggle_vote_rejects_non_nominated():
    movie = _movie(status="backlog")
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        with pytest.raises(HTTPException) as exc:
            toggle_vote("the-substance", "bjoubs")
        assert exc.value.status_code == 400


# ── select_movie ──────────────────────────────────────────────────────────────

def test_toggle_selection_from_nominated():
    movie = _movie(status="nominated")
    selected = _movie(status="selected")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, selected]),
        patch("service.movies_service.movies_repo.update_movie_fields"),
    ):
        result = toggle_selection("the-substance")
    assert result.status == MovieStatus.SELECTED


def test_toggle_selection_back_to_nominated():
    movie = _movie(status="selected")
    nominated = _movie(status="nominated")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, nominated]),
        patch("service.movies_service.movies_repo.update_movie_fields") as mock_update,
    ):
        result = toggle_selection("the-substance")
    mock_update.assert_called_once_with("the-substance", status="nominated")
    assert result.status == MovieStatus.NOMINATED


def test_toggle_selection_rejects_backlog():
    movie = _movie(status="backlog")
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        with pytest.raises(HTTPException) as exc:
            toggle_selection("the-substance")
        assert exc.value.status_code == 400


def test_toggle_selection_rejects_watched():
    movie = _movie(status="watched")
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        with pytest.raises(HTTPException) as exc:
            toggle_selection("the-substance")
        assert exc.value.status_code == 400


# ── complete_movie ────────────────────────────────────────────────────────────

def test_complete_movie_full_flow():
    movie = _movie(status="selected", nominated_by="KingKrab", voted_by=["bjoubs", "GeoMoD"])
    watched = _movie(status="watched")
    other_nominated = _movie(slug="anora", status="nominated", nominated_by="bjoubs", voted_by=["GeoMoD"])

    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", side_effect=[movie, watched]),
        patch("service.movies_service.movies_repo.update_movie_fields") as mock_update,
        patch("service.movies_service.movies_repo.get_movies_by_status", return_value=[other_nominated]),
        patch("service.movies_service.nomination_log_repo.add_nomination") as mock_nom_log,
        patch("service.movies_service.meetings_repo.add_meeting") as mock_meeting,
    ):
        result = complete_movie(
            slug="the-substance",
            rotw_winners=["bjoubs"],
            meeting_start_time="19:00",
            meeting_end_time="21:30",
            participants=["bjoubs", "KingKrab", "GeoMoD"],
        )

    assert result.status == MovieStatus.WATCHED
    # Both the completed movie and the other nominated movie should be logged
    assert mock_nom_log.call_count == 2
    mock_meeting.assert_called_once()
    # Should have updated: the completed movie + the other nominated movie reset
    assert mock_update.call_count == 2


def test_complete_movie_rejects_non_selected():
    movie = _movie(status="nominated")
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        with pytest.raises(HTTPException) as exc:
            complete_movie("the-substance", ["bjoubs"], "19:00", "21:30", ["bjoubs"])
        assert exc.value.status_code == 400


# ── delete_movie ─────────────────────────────────────────────────────────────

def test_delete_movie_backlog():
    movie = _movie(status="backlog")
    with (
        patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie),
        patch("service.movies_service.movies_repo.delete_movie") as mock_delete,
    ):
        delete_movie("the-substance")
    mock_delete.assert_called_once_with("the-substance")


def test_delete_movie_rejects_nominated():
    movie = _movie(status="nominated")
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        with pytest.raises(HTTPException) as exc:
            delete_movie("the-substance")
        assert exc.value.status_code == 400


def test_delete_movie_rejects_watched():
    movie = _movie(status="watched")
    with patch("service.movies_service.movies_repo.get_movie_by_slug", return_value=movie):
        with pytest.raises(HTTPException) as exc:
            delete_movie("the-substance")
        assert exc.value.status_code == 400
