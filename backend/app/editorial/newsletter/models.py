from __future__ import annotations

from datetime import datetime
from enum import Enum

from app.editorial.classification.enums import ArticleType
from app.editorial.classification.models import EditorialClassification
from app.editorial.enrichment.models import EditorialEnrichment
from pydantic import BaseModel, ConfigDict, Field


class NewsletterSectionKind(str, Enum):
    RELEASES = "releases"
    RESEARCH = "research"
    NOTABLE_READS = "notable_reads"


class NewsletterArticle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2048)
    source_name: str = Field(min_length=1, max_length=255)
    published_at: datetime | None = None
    article_type: ArticleType
    enrichment: EditorialEnrichment
    image_url: str | None = None


class NewsletterRenderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    header_title: str = "Intelligence Brief"
    header_subtitle: str = "Seanergy Intelligence Brief"
    summary_signature: str = "— The Editorial Intelligence Desk"
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
        enrichment=enrichment,
        image_url=image_url,
    )
