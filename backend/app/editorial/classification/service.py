from app.catalog.article.model import Article
from app.editorial.classification.models import (
    ClassificationInput,
    EditorialClassification,
)
from app.editorial.classification.provider import (
    ClassificationProvider,
    MockClassificationProvider,
)


class ClassificationService:
    def __init__(self, provider: ClassificationProvider | None = None):
        self.provider = provider or MockClassificationProvider()

    def classify_article(self, article: Article) -> EditorialClassification:
        classification_input = self._map_article_to_input(article)
        return self.provider.classify(classification_input)

    @staticmethod
    def _map_article_to_input(article: Article) -> ClassificationInput:
        source_name = ""
        technology_domain = ""

        if article.feed is not None:
            source_name = article.feed.name or ""
            if article.feed.technology_domain is not None:
                technology_domain = article.feed.technology_domain.name or ""

        return ClassificationInput(
            title=article.title or "",
            source_name=source_name,
            technology_domain=technology_domain,
            summary=article.summary,
            content=article.content,
        )
