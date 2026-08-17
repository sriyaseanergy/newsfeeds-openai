from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ArticleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feed_id: UUID
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl
    author: str | None = Field(default=None, max_length=255)
    published_at: datetime | None = None
    summary: str | None = None
    content: str | None = None
    image_url: str | None = Field(default=None, max_length=2048)
    is_processed: bool = False

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("title must not be empty")
        return title


class ArticleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feed_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    url: HttpUrl | None = None
    author: str | None = Field(default=None, max_length=255)
    published_at: datetime | None = None
    summary: str | None = None
    content: str | None = None
    image_url: str | None = Field(default=None, max_length=2048)
    is_processed: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        title = value.strip()
        if not title:
            raise ValueError("title must not be empty")
        return title


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    feed_id: UUID
    title: str
    url: str
    author: str | None
    published_at: datetime | None
    summary: str | None
    content: str | None
    image_url: str | None
    is_processed: bool
    created_at: datetime
    updated_at: datetime

