import re
from datetime import datetime
from uuid import UUID

from app.catalog.technology_domain.model import TechnologyDomainSchedule
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def slugify_technology_domain_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise ValueError("name must contain at least one letter or number")
    return slug


class TechnologyDomainCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_enabled: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("name must not be empty")
        return name

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        slug = value.strip().lower()
        if not slug:
            raise ValueError("slug must not be empty")
        if not _SLUG_PATTERN.fullmatch(slug):
            raise ValueError(
                "slug must contain lowercase letters, numbers, and hyphens only"
            )
        return slug

    @model_validator(mode="after")
    def default_slug_from_name(self) -> "TechnologyDomainCreate":
        if self.slug is None:
            self.slug = slugify_technology_domain_name(self.name)
        return self


class TechnologyDomainUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_enabled: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        name = value.strip()
        if not name:
            raise ValueError("name must not be empty")
        return name

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        slug = value.strip().lower()
        if not slug:
            raise ValueError("slug must not be empty")
        if not _SLUG_PATTERN.fullmatch(slug):
            raise ValueError(
                "slug must contain lowercase letters, numbers, and hyphens only"
            )
        return slug


class TechnologyDomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    name: str
    slug: str
    description: str | None
    is_enabled: bool
    frequency: TechnologyDomainSchedule
    created_at: datetime
    updated_at: datetime

    @field_validator("frequency", mode="before")
    @classmethod
    def normalize_frequency(cls, value: object) -> TechnologyDomainSchedule:
        if isinstance(value, TechnologyDomainSchedule):
            return value
        if hasattr(value, "value"):
            return TechnologyDomainSchedule(str(value.value))
        return TechnologyDomainSchedule(str(value))
