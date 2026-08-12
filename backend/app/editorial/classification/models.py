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


class ClassificationBatchItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    article_id: str = Field(min_length=1, max_length=64)
    classification_input: ClassificationInput


class BatchedArticleClassification(BaseModel):
    """
    One article classification inside a batch OpenAI response.

    Includes the stable article_id so results can be matched back to inputs.
    """

    model_config = ConfigDict(extra="forbid")

    article_id: str = Field(min_length=1, max_length=64)
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

    def to_editorial_classification(self) -> EditorialClassification:
        return EditorialClassification(
            article_type=self.article_type,
            technologies=self.technologies,
            companies=self.companies,
            products=self.products,
            topics=self.topics,
            severity=self.severity,
            actionability=self.actionability,
            audience=self.audience,
            confidence=self.confidence,
            reasoning=self.reasoning,
        )


class BatchedClassificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classifications: list[BatchedArticleClassification] = Field(default_factory=list)
