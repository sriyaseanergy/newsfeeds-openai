from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NormalizedArticleData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feed_id: UUID
    title: str
    url: str
    author: str | None = None
    published_at: datetime | None = None
    summary: str | None = None
    content: str | None = None
    source_identifier: str | None = None
    image_url: str | None = None
    is_processed: bool = False


class IngestionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    technology_domain_id: UUID | None = None
    feed_id: UUID | None = None
    fetched_count: int = Field(default=0, ge=0)
    created_count: int = Field(default=0, ge=0)
    updated_count: int = Field(default=0, ge=0)
    skipped_count: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)
