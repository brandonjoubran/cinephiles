from datetime import date

from infrastructure.dates import parse_date
from models.movie import MovieStatus
import repository.movies_repository as movies_repo


def get_selected_slugs() -> list[str]:
    watched = movies_repo.get_movies_by_status(MovieStatus.WATCHED)
    watched.sort(key=lambda movie: parse_date(movie.watched_date) or date.min)
    return [movie.slug for movie in watched]
