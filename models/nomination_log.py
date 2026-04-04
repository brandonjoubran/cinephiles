from pydantic import BaseModel, field_validator


class NominationLog(BaseModel):
    slug: str
    nominated_by: str
    voted_by: list[str]
    date_nominated: str

    @field_validator("slug")
    @classmethod
    def slug_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("slug cannot be empty")
        return value

    @field_validator("nominated_by")
    @classmethod
    def nominated_by_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("nominated_by cannot be empty")
        return value

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

    @field_validator("date_nominated")
    @classmethod
    def date_nominated_must_be_mm_dd_yyyy(cls, value: str) -> str:
        from datetime import datetime
        try:
            datetime.strptime(value, "%m/%d/%Y")
        except ValueError:
            raise ValueError("date_nominated must be in MM/DD/YYYY format (e.g. 02/11/2025)")
        return value
