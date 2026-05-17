from pydantic import BaseModel, field_validator


class SelectedFilm(BaseModel):
    """One row on the Selected sheet (club watch history after complete)."""

    title: str
    slug: str
    url: str
    added_by: str
    date_added: str
    poster: str
    nominated_by: str
    voted_by: list[str]
    watched_date: str

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
