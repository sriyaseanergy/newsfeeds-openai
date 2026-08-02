from uuid import UUID

from app.catalog.feed.model import Feed, FetchKind
from app.catalog.feed.repository import FeedRepository
from app.catalog.feed.schemas import FeedCreate, FeedUpdate
from app.catalog.technology_domain.repository import TechnologyDomainRepository
from sqlalchemy.exc import IntegrityError


class FeedNotFoundError(Exception):
    pass


class FeedDuplicateUrlError(Exception):
    pass


class FeedTechnologyDomainNotFoundError(Exception):
    pass


class FeedService:
    def __init__(
        self,
        repository: FeedRepository,
        technology_domain_repository: TechnologyDomainRepository,
    ):
        self.repository = repository
        self.technology_domain_repository = technology_domain_repository

    def create(self, payload: FeedCreate) -> Feed:
        normalized_payload = self._normalize_create_payload(payload)
        self._ensure_technology_domain_exists(normalized_payload.technology_domain_id)

        existing = self.repository.get_by_url(str(normalized_payload.url))
        if existing is not None:
            raise FeedDuplicateUrlError(f"Feed with URL '{normalized_payload.url}' already exists.")

        try:
            return self.repository.create(normalized_payload)
        except IntegrityError as exc:
            raise FeedDuplicateUrlError(
                f"Feed with URL '{normalized_payload.url}' already exists."
            ) from exc

    def get_by_id(self, feed_id: UUID) -> Feed:
        feed = self.repository.get_by_id(feed_id)
        if feed is None:
            raise FeedNotFoundError(f"Feed with id '{feed_id}' was not found.")
        return feed

    def list(self) -> list[Feed]:
        return self.repository.list()

    def update(self, feed_id: UUID, payload: FeedUpdate) -> Feed:
        feed = self.get_by_id(feed_id)
        normalized_payload = self._normalize_update_payload(feed, payload)

        if normalized_payload.technology_domain_id is not None:
            self._ensure_technology_domain_exists(normalized_payload.technology_domain_id)

        if normalized_payload.url is not None:
            existing = self.repository.get_by_url(str(normalized_payload.url))
            if existing is not None and existing.id != feed.id:
                raise FeedDuplicateUrlError(
                    f"Feed with URL '{normalized_payload.url}' already exists."
                )

        try:
            return self.repository.update(feed, normalized_payload)
        except IntegrityError as exc:
            raise FeedDuplicateUrlError("Feed URL must be unique.") from exc

    def delete(self, feed_id: UUID) -> None:
        feed = self.get_by_id(feed_id)
        self.repository.delete(feed)

    def _ensure_technology_domain_exists(self, technology_domain_id: UUID) -> None:
        technology_domain = self.technology_domain_repository.get_by_id(technology_domain_id)
        if technology_domain is None:
            raise FeedTechnologyDomainNotFoundError(
                f"Technology domain with id '{technology_domain_id}' was not found."
            )

    @staticmethod
    def _normalize_create_payload(payload: FeedCreate) -> FeedCreate:
        if payload.fetch_kind != FetchKind.CRAWL:
            return payload.model_copy(update={"crawl_depth": None})
        return payload

    @staticmethod
    def _normalize_update_payload(feed: Feed, payload: FeedUpdate) -> FeedUpdate:
        effective_kind = payload.fetch_kind or feed.fetch_kind
        should_ignore_crawl_depth = (
            effective_kind != FetchKind.CRAWL
            and (payload.fetch_kind is not None or payload.crawl_depth is not None)
        )
        if should_ignore_crawl_depth:
            return payload.model_copy(update={"crawl_depth": None})
        return payload

