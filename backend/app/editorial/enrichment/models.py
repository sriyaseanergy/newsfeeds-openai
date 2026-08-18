from __future__ import annotations

from datetime import datetime

from app.editorial.classification.models import EditorialClassification
from pydantic import BaseModel, ConfigDict, Field


class AudienceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive: str = Field(min_length=1)
    technical_leadership: str = Field(min_length=1)
    engineering: str = Field(min_length=1)


class KeyDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    value: str = Field(min_length=1)


class EnrichedArticle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tldr: str = Field(min_length=1)
    why_it_matters: AudienceSummary
    key_details: list[KeyDetail] = Field(default_factory=list)
    recommended_action: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ClassifiedArticle(BaseModel):
    """Article content plus its editorial classification, ready for enrichment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_name: str
    url: str
    published_date: str | None = None
    summary: str | None = None
    content: str | None = None
    classification: EditorialClassification


def classified_article_from_pipeline(
    *,
    source_name: str,
    url: str,
    published_at: datetime | None,
    summary: str | None,
    content: str | None,
    classification: EditorialClassification,
) -> ClassifiedArticle:
    published_date = (
        published_at.strftime("%Y-%m-%d") if published_at is not None else None
    )
    return ClassifiedArticle(
        source_name=source_name,
        url=url,
        published_date=published_date,
        summary=summary,
        content=content,
        classification=classification,
    )
