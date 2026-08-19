from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class EntraIdentity(BaseModel):
    """Validated Entra identity passed into UserService (not an ID token)."""

    model_config = ConfigDict(extra="forbid")

    oid: str = Field(min_length=1)
    tid: str = Field(min_length=1)
    email: EmailStr | None = None
    display_name: str | None = None

    @field_validator("oid", "tid", "display_name", mode="before")
    @classmethod
    def strip_string_fields(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        return value.strip()

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        return normalized or None
