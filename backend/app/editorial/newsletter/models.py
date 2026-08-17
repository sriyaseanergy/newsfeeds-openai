from __future__ import annotations

from datetime import datetime

from app.editorial.classification.enums import (
    Actionability,
    ArticleType,
    Severity,
)
from app.editorial.classification.models import EditorialClassification
from app.editorial.enrichment.models import EditorialEnrichment
from pydantic import BaseModel, ConfigDict, Field


class NewsletterArticle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2048)
    source_name: str = Field(min_length=1, max_length=255)
    published_at: datetime | None = None
    article_type: ArticleType
    technology_domain: str = Field(default="", max_length=128)
    severity: Severity
    actionability: Actionability
    enrichment: EditorialEnrichment
    image_url: str | None = None


class NewsletterRenderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    header_subtitle: str = "Intelligence Briefing"
    summary_signature: str = "— The Editorial Intelligence Desk"
    dashboard_url: str = "http://localhost:5173/feed-alerts/"
    generated_at: datetime | None = None


class NewsletterRenderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    articles: list[NewsletterArticle] = Field(default_factory=list)
    config: NewsletterRenderConfig = Field(default_factory=NewsletterRenderConfig)


def newsletter_article_from_pipeline(
    *,
    title: str,
    url: str,
    source_name: str,
    published_at: datetime | None,
    technology_domain: str,
    classification: EditorialClassification,
    enrichment: EditorialEnrichment,
    image_url: str | None = None,
) -> NewsletterArticle:
    return NewsletterArticle(
        title=title,
        url=url,
        source_name=source_name,
        published_at=published_at,
        article_type=classification.article_type,
        technology_domain=technology_domain,
        severity=classification.severity,
        actionability=classification.actionability,
        enrichment=enrichment,
        image_url=image_url,
    )
