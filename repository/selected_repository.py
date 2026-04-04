from models.movie import MovieStatus
import repository.movies_repository as movies_repo


def get_selected_slugs() -> list[str]:
    watched = movies_repo.get_movies_by_status(MovieStatus.WATCHED)
    return [m.slug for m in watched]


def get_rotw_winners() -> list[str]:
    watched = movies_repo.get_movies_by_status(MovieStatus.WATCHED)
    winners = []
    for movie in watched:
        for name in movie.rotw:
            winners.append(name)
    return winners
