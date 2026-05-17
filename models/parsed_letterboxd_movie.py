from pydantic import BaseModel, field_validator


class ParsedLetterboxdMovie(BaseModel):
    """Film metadata scraped from a Letterboxd film page before adding to Movies."""

    title: str
    slug: str
    url: str
    poster: str

    @field_validator("title", "slug", "url")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value
