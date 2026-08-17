from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.catalog.article.model import Article
from app.catalog.article.repository import ArticleRepository
from app.catalog.article.schemas import ArticleCreate
from app.catalog.feed.model import Feed
from app.ingestion.models import NormalizedArticleData


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
            is_processed=stored.is_processed if stored is not None else False,
            feed=feed,
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
    article = None
    if stored_article_id is not None:
        article = article_repository.get_by_id(stored_article_id)
    if article is None:
        article = article_repository.get_by_url(article_data.url)

    if article is not None:
        if not article.is_processed:
            article_repository.mark_processed(article)
        return

    try:
        article_repository.create(
            ArticleCreate(
                feed_id=feed.id,
                title=article_data.title,
                url=article_data.url,
                author=article_data.author,
                published_at=article_data.published_at,
                summary=article_data.summary,
                content=article_data.content,
                is_processed=True,
            )
        )
    except IntegrityError:
        article_repository.db.rollback()
        article = article_repository.get_by_url(article_data.url)
        if article is not None and not article.is_processed:
            article_repository.mark_processed(article)
