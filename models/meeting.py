from pydantic import BaseModel, field_validator


class Meeting(BaseModel):
    date: str
    movie_name: str
    movie_slug: str
    start_time: str
    end_time: str
    participants: list[str]
    rotw: list[str] = []

    @field_validator("movie_slug")
    @classmethod
    def movie_slug_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("movie_slug cannot be empty")
        return value

    @field_validator("date")
    @classmethod
    def date_must_be_mm_dd_yyyy(cls, value: str) -> str:
        from datetime import datetime
        try:
            datetime.strptime(value, "%m/%d/%Y")
        except ValueError:
            raise ValueError("date must be in MM/DD/YYYY format (e.g. 02/11/2025)")
        return value

    @field_validator("participants", mode="before")
    @classmethod
    def parse_participants(cls, value) -> list[str]:
        if isinstance(value, list):
            return [v.strip() for v in value if v.strip()]
        if isinstance(value, str):
            if not value.strip():
                return []
            return [v.strip() for v in value.split(",") if v.strip()]
        return []

    @field_validator("rotw", mode="before")
    @classmethod
    def parse_rotw(cls, value) -> list[str]:
        if isinstance(value, list):
            return [v.strip() for v in value if v.strip()]
        if isinstance(value, str):
            if not value.strip():
                return []
            return [v.strip() for v in value.split(",") if v.strip()]
        return []
