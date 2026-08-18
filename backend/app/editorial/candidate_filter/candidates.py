from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.catalog.article.model import Article
from app.catalog.article.repository import ArticleRepository
from app.catalog.article.schemas import ArticleCreate
from app.catalog.feed.model import Feed
from app.ingestion.models import NormalizedArticleData
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


def build_candidate_article(
    feed: Feed,
    article_data: NormalizedArticleData,
    article_repository: ArticleRepository,
) -> tuple[Article, UUID | None]:
    stored = article_repository.get_by_url(article_data.url)
    return (
        Article(
            feed_id=feed.id,
            title=article_data.title,
            url=article_data.url,
            source_identifier=article_data.source_identifier,
            author=article_data.author,
            published_at=article_data.published_at,
            summary=article_data.summary,
            content=article_data.content,
            image_url=article_data.image_url or (stored.image_url if stored else None),
            is_processed=stored.is_processed if stored is not None else False,
        ),
        stored.id if stored is not None else None,
    )


def mark_article_processed(
    article_repository: ArticleRepository,
    feed: Feed,
    article_data: NormalizedArticleData,
    *,
    stored_article_id: UUID | None = None,
) -> None:
    article_id = stored_article_id
    if article_id is None:
        stored = article_repository.get_by_url(article_data.url)
        article_id = stored.id if stored is not None else None

    if article_id is not None:
        persisted = article_repository.mark_processed(article_id)
        if persisted is not None:
            logger.info(
                "editorial.article.marked_processed article_id=%s persisted=True",
                persisted.id,
            )
        return

    try:
        created = article_repository.create(
            ArticleCreate(
                feed_id=feed.id,
                title=article_data.title,
                url=article_data.url,
                author=article_data.author,
                published_at=article_data.published_at,
                summary=article_data.summary,
                content=article_data.content,
                image_url=article_data.image_url,
                is_processed=True,
            )
        )
    except IntegrityError:
        article_repository.db.rollback()
        stored = article_repository.get_by_url(article_data.url)
        if stored is None:
            return
        persisted = article_repository.mark_processed(stored.id)
        if persisted is not None:
            logger.info(
                "editorial.article.marked_processed article_id=%s persisted=True",
                persisted.id,
            )
        return

    logger.info(
        "editorial.article.marked_processed article_id=%s persisted=True",
        created.id,
    )
