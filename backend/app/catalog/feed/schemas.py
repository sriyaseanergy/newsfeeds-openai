from datetime import datetime
from uuid import UUID

from app.catalog.feed.model import FetchKind
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class FeedCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technology_domain_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    url: HttpUrl
    is_enabled: bool = True
    fetch_kind: FetchKind = FetchKind.RSS
    crawl_depth: int | None = Field(default=1, ge=1)
    max_new_articles_per_crawl: int | None = Field(default=20, ge=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("name must not be empty")
        return name


class FeedUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technology_domain_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    url: HttpUrl | None = None
    is_enabled: bool | None = None
    fetch_kind: FetchKind | None = None
    crawl_depth: int | None = Field(default=None, ge=1)
    max_new_articles_per_crawl: int | None = Field(default=None, ge=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        name = value.strip()
        if not name:
            raise ValueError("name must not be empty")
        return name


class FeedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    technology_domain_id: UUID
    name: str
    description: str | None
    url: str
    is_enabled: bool
    fetch_kind: FetchKind
    crawl_depth: int | None
    max_new_articles_per_crawl: int | None
    created_at: datetime
    updated_at: datetime

