from app.catalog.article.model import Article
from app.editorial.classification.models import (
    ClassificationBatchItem,
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

    def classify_articles(
        self,
        articles: list[tuple[str, Article]],
    ) -> dict[str, EditorialClassification]:
        """
        Classify many articles with provider-level batching when available.

        articles: list of (article_id, Article)
        """
        items = [
            ClassificationBatchItem(
                article_id=article_id,
                classification_input=self._map_article_to_input(article),
            )
            for article_id, article in articles
        ]
        return self.provider.classify_many(items)

    @staticmethod
    def _map_article_to_input(article: Article) -> ClassificationInput:
        source_name = ""
        technology_domain = ""
        technology_domain_description = None

        if article.feed is not None:
            source_name = article.feed.name or ""
            if article.feed.technology_domain is not None:
                domain = article.feed.technology_domain
                technology_domain = domain.name or ""
                technology_domain_description = domain.description

        return ClassificationInput(
            title=article.title or "",
            source_name=source_name,
            technology_domain=technology_domain,
            technology_domain_description=technology_domain_description,
            summary=article.summary,
            content=article.content,
        )
