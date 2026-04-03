from fastapi import APIRouter
import service.stats_service as stats_service
from models.user_stats import UserStats
from models.club_stats import ClubStats

router = APIRouter()


@router.get("/stats")
def list_user_stats() -> list[UserStats]:
    return stats_service.get_all_user_stats()


@router.get("/stats/club")
def club_stats() -> ClubStats:
    return stats_service.get_club_stats()
