from fastapi import APIRouter
from infrastructure.cache import cache

router = APIRouter()


@router.get("/cache/clear")
def clear_cache():
    """Delete the on-disk sheet cache.

    Use after editing Google Sheets outside the app so the next API read
    refetches from Sheets instead of serving stale JSON.
    """
    cache.clear()
    return {"message": "Cache cleared"}
