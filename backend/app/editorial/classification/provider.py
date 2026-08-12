from abc import ABC, abstractmethod

from app.editorial.classification.enums import (
    Actionability,
    ArticleType,
    Audience,
    Severity,
)
from app.editorial.classification.models import (
    ClassificationBatchItem,
    ClassificationInput,
    EditorialClassification,
)


class ClassificationProvider(ABC):
    @abstractmethod
    def classify(
        self, classification_input: ClassificationInput
    ) -> EditorialClassification:
        raise NotImplementedError

    def classify_many(
        self,
        items: list[ClassificationBatchItem],
    ) -> dict[str, EditorialClassification]:
        """
        Classify multiple articles.

        Default implementation preserves one-call-per-article behavior.
        Providers may override this with domain-grouped batching.
        """
        return {
            item.article_id: self.classify(item.classification_input)
            for item in items
        }


class MockClassificationProvider(ClassificationProvider):
    """
    Deterministic placeholder provider for architecture validation.
    """

    def classify(
        self, classification_input: ClassificationInput
    ) -> EditorialClassification:
        title_text = (classification_input.title or "").lower()
        content_text = (
            (classification_input.summary or "")
            + " "
            + (classification_input.content or "")
        ).lower()
        combined = f"{title_text} {content_text}"

        is_security = any(
            keyword in combined
            for keyword in ("cve", "vulnerability", "security", "patch", "exploit")
        )

        technologies = self._extract_technologies(combined)
        topics = self._extract_topics(combined)

        if is_security:
            article_type = ArticleType.ADVISORY
            severity = Severity.HIGH
            actionability = Actionability.ACTION_RECOMMENDED
            audience = Audience.SECURITY
            reasoning = (
                "Contains security-related indicators and potential risk signals."
            )
        else:
            article_type = ArticleType.NEWS
            severity = Severity.NONE
            actionability = Actionability.INFORMATIONAL
            audience = Audience.ENGINEERING
            reasoning = "General technical update without urgent action indicators."

        return EditorialClassification(
            article_type=article_type,
            technologies=technologies,
            companies=[],
            products=[],
            topics=topics,
            severity=severity,
            actionability=actionability,
            audience=audience,
            confidence=0.65,
            reasoning=reasoning,
        )

    @staticmethod
    def _extract_technologies(text: str) -> list[str]:
        tech_keywords = {
            "python": "Python",
            "fastapi": "FastAPI",
            "postgres": "PostgreSQL",
            "sqlalchemy": "SQLAlchemy",
            "kubernetes": "Kubernetes",
            "docker": "Docker",
        }
        return [label for keyword, label in tech_keywords.items() if keyword in text]

    @staticmethod
    def _extract_topics(text: str) -> list[str]:
        topic_keywords = {
            "security": "Security",
            "ai": "AI",
            "inference": "Inference",
            "performance": "Performance",
            "database": "Database",
            "api": "API",
        }
        return [label for keyword, label in topic_keywords.items() if keyword in text]
