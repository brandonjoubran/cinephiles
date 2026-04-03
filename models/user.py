from pydantic import BaseModel, field_validator


class User(BaseModel):
    username: str
    join_date: str

    @field_validator("username")
    @classmethod
    def username_must_be_non_empty_string(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("username cannot be empty")
        return value

    @field_validator("join_date")
    @classmethod
    def join_date_must_be_mm_dd_yyyy(cls, value: str) -> str:
        from datetime import datetime
        try:
            datetime.strptime(value, "%m/%d/%Y")
        except ValueError:
            raise ValueError("join_date must be in MM/DD/YYYY format (e.g. 02/11/2025)")
        return value
