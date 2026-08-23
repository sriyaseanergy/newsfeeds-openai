from uuid import UUID

from app.catalog.technology_domain.model import TechnologyDomainSchedule
from pydantic import BaseModel, ConfigDict, Field


class DomainPreferenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technology_domain_id: UUID
    name: str
    slug: str
    description: str | None
    frequency: TechnologyDomainSchedule
    system_enabled: bool
    user_enabled: bool
    effective_enabled: bool
    feed_count: int


class DomainPreferenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technology_domain_id: UUID
    enabled: bool


class DomainPreferenceBulkUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferences: list[DomainPreferenceItem] = Field(min_length=1)


class DomainPreferenceToggle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
