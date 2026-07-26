from app.editorial.classification.enums import (
    Actionability,
    ArticleType,
    Audience,
    Severity,
)
from pydantic import BaseModel, ConfigDict, Field


class EditorialClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    article_type: ArticleType
    technologies: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    severity: Severity
    actionability: Actionability
    audience: Audience
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1, max_length=1000)


class ClassificationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    source_name: str
    technology_domain: str
    summary: str | None = None
    content: str | None = None
