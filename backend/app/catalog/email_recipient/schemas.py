from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class EmailRecipientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    is_enabled: bool = True

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class EmailRecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    email: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
