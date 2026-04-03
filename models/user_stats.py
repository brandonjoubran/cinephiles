from pydantic import BaseModel


class UserStats(BaseModel):
    username: str
    movies_watched: int
    average_rating: float
    num_reviews: int
    avg_words_per_review: float
