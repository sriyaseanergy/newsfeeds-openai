from uuid import UUID

from app.catalog.article.model import Article
from app.catalog.article.repository import ArticleRepository
from app.catalog.article.schemas import ArticleCreate, ArticleUpdate
from app.catalog.feed.repository import FeedRepository
from sqlalchemy.exc import IntegrityError


class ArticleNotFoundError(Exception):
    pass


class ArticleDuplicateUrlError(Exception):
    pass


class ArticleFeedNotFoundError(Exception):
    pass


class ArticleService:
    def __init__(self, repository: ArticleRepository, feed_repository: FeedRepository):
        self.repository = repository
        self.feed_repository = feed_repository

    def create(self, payload: ArticleCreate) -> Article:
        self._ensure_feed_exists(payload.feed_id)

        existing = self.repository.get_by_url(str(payload.url))
        if existing is not None:
            raise ArticleDuplicateUrlError(
                f"Article with URL '{payload.url}' already exists."
            )

        try:
            return self.repository.create(payload)
        except IntegrityError as exc:
            raise ArticleDuplicateUrlError(
                f"Article with URL '{payload.url}' already exists."
            ) from exc

    def get_by_id(self, article_id: UUID) -> Article:
        article = self.repository.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError(f"Article with id '{article_id}' was not found.")
        return article

    def list(self) -> list[Article]:
        return self.repository.list()

    def update(self, article_id: UUID, payload: ArticleUpdate) -> Article:
        article = self.get_by_id(article_id)

        if payload.feed_id is not None:
            self._ensure_feed_exists(payload.feed_id)

        if payload.url is not None:
            existing = self.repository.get_by_url(str(payload.url))
            if existing is not None and existing.id != article.id:
                raise ArticleDuplicateUrlError(
                    f"Article with URL '{payload.url}' already exists."
                )

        try:
            return self.repository.update(article, payload)
        except IntegrityError as exc:
            raise ArticleDuplicateUrlError("Article URL must be unique.") from exc

    def delete(self, article_id: UUID) -> None:
        article = self.get_by_id(article_id)
        self.repository.delete(article)

    def _ensure_feed_exists(self, feed_id: UUID) -> None:
        feed = self.feed_repository.get_by_id(feed_id)
        if feed is None:
            raise ArticleFeedNotFoundError(f"Feed with id '{feed_id}' was not found.")

