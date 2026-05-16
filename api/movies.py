from fastapi import APIRouter
from pydantic import BaseModel
import service.movies_service as movies_service
from models.movie import Movie, MovieStatus

router = APIRouter()


class AddMovieRequest(BaseModel):
    title: str
    slug: str
    url: str
    added_by: str
    poster: str


class NominateRequest(BaseModel):
    username: str


class VoteRequest(BaseModel):
    username: str


@router.get("/movies")
def list_movies() -> list[Movie]:
    return movies_service.get_all_movies()


@router.get("/movies/status/{status}")
def list_movies_by_status(status: MovieStatus) -> list[Movie]:
    return movies_service.get_movies_by_status(status)


@router.get("/movies/{slug}")
def get_movie(slug: str) -> Movie:
    return movies_service.get_movie_by_slug(slug)


@router.post("/movies")
def add_movie(body: AddMovieRequest) -> Movie:
    return movies_service.add_movie(
        title=body.title,
        slug=body.slug,
        url=body.url,
        added_by=body.added_by,
        poster=body.poster,
    )


@router.post("/movies/{slug}/nominate")
def nominate_movie(slug: str, body: NominateRequest) -> Movie:
    return movies_service.toggle_nomination(slug, body.username)


@router.post("/movies/{slug}/vote")
def vote_movie(slug: str, body: VoteRequest) -> Movie:
    return movies_service.toggle_vote(slug, body.username)


@router.post("/movies/{slug}/select")
def select_movie(slug: str) -> Movie:
    return movies_service.toggle_selection(slug)


@router.post("/movies/{slug}/complete")
def complete_movie(slug: str) -> Movie:
    return movies_service.complete_movie(slug)


@router.delete("/movies/{slug}")
def delete_movie(slug: str):
    movies_service.delete_movie(slug)
    return {"detail": f"Movie '{slug}' deleted"}
