from fastapi import APIRouter
from pydantic import BaseModel

import service.nominators_service as nominators_service

router = APIRouter()


class GenerateNominatorsResponse(BaseModel):
    movie_slug: str
    nominators: list[str]


@router.get("/nominators/generate")
def generate_nominators() -> GenerateNominatorsResponse:
    """Pick 3 random members who watched the latest completed club film."""
    movie_slug, nominators = nominators_service.generate_nominators()
    return GenerateNominatorsResponse(movie_slug=movie_slug, nominators=nominators)
