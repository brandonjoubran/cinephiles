from pydantic import BaseModel


class FilmHighlight(BaseModel):
    title: str
    slug: str
    value: float


class ClubStats(BaseModel):
    total_movies: int
    total_reviews: int
    average_rating: float
    highest_rated: FilmHighlight | None
    lowest_rated: FilmHighlight | None
    most_divisive: FilmHighlight | None
    longest_review: FilmHighlight | None
