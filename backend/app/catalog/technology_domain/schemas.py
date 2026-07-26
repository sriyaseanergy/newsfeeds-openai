from datetime import datetime
from uuid import UUID

from app.catalog.technology_domain.model import TechnologyDomainSchedule
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TechnologyDomainCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_enabled: bool = True
    schedule: TechnologyDomainSchedule = TechnologyDomainSchedule.DAILY

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("name must not be empty")
        return name


class TechnologyDomainUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_enabled: bool | None = None
    schedule: TechnologyDomainSchedule | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        name = value.strip()
        if not name:
            raise ValueError("name must not be empty")
        return name


class TechnologyDomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    name: str
    description: str | None
    is_enabled: bool
    schedule: TechnologyDomainSchedule
    created_at: datetime
    updated_at: datetime
