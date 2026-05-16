from enum import Enum
from pydantic import BaseModel, field_validator


class MovieStatus(str, Enum):
    BACKLOG = "backlog"
    NOMINATED = "nominated"
    SELECTED = "selected"
    WATCHED = "watched"


class Movie(BaseModel):
    title: str
    slug: str
    url: str
    added_by: str
    date_added: str
    poster: str
    status: MovieStatus
    nominated_by: str
    voted_by: list[str]
    watched_date: str

    @field_validator("title")
    @classmethod
    def title_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title cannot be empty")
        return value

    @field_validator("slug")
    @classmethod
    def slug_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("slug cannot be empty")
        return value

    @field_validator("status", mode="before")
    @classmethod
    def status_must_be_valid(cls, value) -> MovieStatus:
        if isinstance(value, MovieStatus):
            return value
        if isinstance(value, str):
            value = value.strip().lower()
            if not value:
                return MovieStatus.BACKLOG
        return MovieStatus(value)

    @field_validator("voted_by", mode="before")
    @classmethod
    def parse_voted_by(cls, value) -> list[str]:
        if isinstance(value, list):
            return [v.strip() for v in value if v.strip()]
        if isinstance(value, str):
            if not value.strip():
                return []
            return [v.strip() for v in value.split(",") if v.strip()]
        return []
