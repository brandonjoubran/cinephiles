from pydantic import BaseModel, field_validator


class FilmLog(BaseModel):
    username: str
    slug: str
    title: str
    rating: float
    has_review: bool
    word_count: int
    review_link: str
    updated_at: str

    @field_validator("username")
    @classmethod
    def username_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("username cannot be empty")
        return value

    @field_validator("slug")
    @classmethod
    def slug_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("slug cannot be empty")
        return value

    @field_validator("has_review", mode="before")
    @classmethod
    def has_review_from_sheet(cls, value) -> bool:
        if isinstance(value, bool):
            return value
        if value is None or value == "":
            return False
        return str(value).strip().upper() == "TRUE"

    @field_validator("word_count", mode="before")
    @classmethod
    def word_count_from_sheet(cls, value) -> int:
        if value == "" or value is None:
            return 0
        return int(value)

    @field_validator("rating", mode="before")
    @classmethod
    def rating_must_be_between_0_and_5(cls, value) -> float:
        if value == "" or value is None:
            return 0.0
        value = float(value)
        if not (0 <= value <= 5):
            raise ValueError("rating must be between 0 and 5")
        return value

    @field_validator("word_count")
    @classmethod
    def word_count_must_be_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("word_count cannot be negative")
        return value
