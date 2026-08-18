from collections.abc import Sequence
from time import perf_counter
from uuid import UUID

from app.catalog.article.model import Article
from app.catalog.feed.model import Feed
from app.catalog.technology_domain.model import (
    TechnologyDomain,
    TechnologyDomainSchedule,
)
from app.ingestion.acquisition_factory import AcquisitionFactory
from app.ingestion.mapper import ArticleMapper
from app.ingestion.models import IngestionResult, NormalizedArticleData
from app.ingestion.rss_client import RSSClient
from app.infrastructure.logging import get_logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class IngestionService:
    def __init__(
        self,
        db: Session,
        rss_client: RSSClient | None = None,
        article_mapper: ArticleMapper | None = None,
        acquisition_factory: AcquisitionFactory | None = None,
    ):
        self.db = db
        if acquisition_factory is not None:
            self.acquisition_factory = acquisition_factory
            return

        if rss_client is not None or article_mapper is not None:
            from app.ingestion.rss_fetcher import RSSFeedAcquirer

            self.acquisition_factory = AcquisitionFactory(
                rss_acquirer=RSSFeedAcquirer(
                    rss_client=rss_client or RSSClient(),
                    article_mapper=article_mapper or ArticleMapper(),
                )
            )
            return

        self.acquisition_factory = AcquisitionFactory()

    def ingest_feed(self, feed_id: UUID) -> IngestionResult:
        logger.info("Feed loading started (feed_id=%s).", feed_id)
        feed = self.db.execute(
            select(Feed).where(Feed.id == feed_id)
        ).scalar_one_or_none()
        if feed is None:
            logger.warning("Feed loading failed: feed not found (feed_id=%s).", feed_id)
            return IngestionResult(
                feed_id=feed_id,
                errors=[f"Feed with id '{feed_id}' was not found."],
            )

        result = IngestionResult(
            technology_domain_id=feed.technology_domain_id,
            feed_id=feed.id,
        )
        return self._ingest_feed(feed, result)

    def ingest_technology_domain(
        self, technology_domain_id: UUID
    ) -> Sequence[IngestionResult]:
        domain = self.db.execute(
            select(TechnologyDomain).where(TechnologyDomain.id == technology_domain_id)
        ).scalar_one_or_none()
        if domain is None:
            return [
                IngestionResult(
                    technology_domain_id=technology_domain_id,
                    errors=[
                        f"Technology domain with id '{technology_domain_id}' was not found."
                    ],
                )
            ]

        return self.ingest_domain(domain)

    def ingest_domain(
        self, technology_domain: TechnologyDomain
    ) -> Sequence[IngestionResult]:
        logger.info(
            "Ingestion run started for technology domain (domain_id=%s name=%s).",
            technology_domain.id,
            technology_domain.name,
        )
        if not technology_domain.is_enabled:
            logger.info(
                "Ingestion skipped: technology domain disabled (domain_id=%s).",
                technology_domain.id,
            )
            return [
                IngestionResult(
                    technology_domain_id=technology_domain.id,
                    errors=["Technology domain is disabled."],
                )
            ]

        results: list[IngestionResult] = []
        for feed in technology_domain.feeds:
            if not feed.is_enabled:
                logger.info("Feed skipped: disabled (feed_id=%s name=%s).", feed.id, feed.name)
                results.append(
                    IngestionResult(
                        technology_domain_id=technology_domain.id,
                        feed_id=feed.id,
                        skipped_count=1,
                        errors=["Feed is disabled."],
                    )
                )
                continue

            feed_result = IngestionResult(
                technology_domain_id=technology_domain.id,
                feed_id=feed.id,
            )
            results.append(self._ingest_feed(feed, feed_result))

        logger.info(
            "Ingestion domain run completed (domain_id=%s feed_count=%s).",
            technology_domain.id,
            len(results),
        )
        return results

    def ingest_scheduled_domains(
        self, schedule: TechnologyDomainSchedule
    ) -> Sequence[IngestionResult]:
        domains = (
            self.db.execute(
                select(TechnologyDomain).where(
                    TechnologyDomain.is_enabled.is_(True),
                    TechnologyDomain.schedule == schedule,
                )
            )
            .scalars()
            .all()
        )

        results: list[IngestionResult] = []
        for domain in domains:
            results.extend(self.ingest_domain(domain))
        return results

    def _ingest_feed(self, feed: Feed, result: IngestionResult) -> IngestionResult:
        logger.info("Feed fetch started (feed_id=%s name=%s).", feed.id, feed.name)
        started_at = perf_counter()
        try:
            acquirer = self.acquisition_factory.for_feed(feed)
            known_urls = self._known_article_urls_for_feed(feed.id)
            acquisition = acquirer.acquire(feed, known_urls=known_urls)
        except Exception as exc:
            logger.exception("Feed failed during fetch (feed_id=%s name=%s).", feed.id, feed.name)
            result.errors.append(f"Feed fetch failed: {exc}")
            return result
        fetch_elapsed = perf_counter() - started_at

        result.fetched_count = acquisition.fetched_count
        logger.info(
            "Feed fetched successfully (feed_id=%s entries=%s duration=%.2fs).",
            feed.id,
            result.fetched_count,
            fetch_elapsed,
        )

        if acquisition.errors:
            result.skipped_count += len(acquisition.errors)
            result.errors.extend(acquisition.errors)

        for article_data in acquisition.articles:
            existing = self.db.execute(
                select(Article.id).where(Article.url == article_data.url)
            ).scalar_one_or_none()
            if existing is not None:
                result.skipped_count += 1
                logger.info("Duplicate removed (feed_id=%s article_url=%s).", feed.id, article_data.url)
                continue

            article = self._to_article_entity(article_data)
            self.db.add(article)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                result.skipped_count += 1
                logger.info("Duplicate removed at persistence (feed_id=%s article_url=%s).", feed.id, article_data.url)
                continue
            result.created_count += 1
            logger.info("Article created (feed_id=%s article_url=%s).", feed.id, article_data.url)

        logger.info(
            "Feed processing completed (feed_id=%s fetched=%s created=%s skipped=%s).",
            feed.id,
            result.fetched_count,
            result.created_count,
            result.skipped_count,
        )
        return result

    @staticmethod
    def _to_article_entity(article_data: NormalizedArticleData) -> Article:
        return Article(
            feed_id=article_data.feed_id,
            title=article_data.title,
            url=article_data.url,
            author=article_data.author,
            published_at=article_data.published_at,
            summary=article_data.summary,
            content=article_data.content,
            source_identifier=article_data.source_identifier,
            image_url=article_data.image_url,
            is_processed=article_data.is_processed,
        )

    def _known_article_urls_for_feed(self, feed_id: UUID) -> set[str]:
        statement = select(Article.url).where(Article.feed_id == feed_id)
        urls = self.db.execute(statement).scalars().all()
        return {str(url).strip().lower() for url in urls if str(url).strip()}
