from fastapi import APIRouter
from infrastructure.cache import cache

router = APIRouter()


@router.get("/cache/clear")
def clear_cache():
    cache.clear()
    return {"message": "Cache cleared"}
