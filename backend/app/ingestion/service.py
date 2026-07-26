from collections.abc import Sequence
from uuid import UUID

from app.catalog.article.model import Article
from app.catalog.feed.model import Feed
from app.catalog.technology_domain.model import (
    TechnologyDomain,
    TechnologyDomainSchedule,
)
from app.ingestion.mapper import ArticleMapper
from app.ingestion.models import IngestionResult, NormalizedArticleData
from app.ingestion.rss_client import RSSClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class IngestionService:
    def __init__(
        self,
        db: Session,
        rss_client: RSSClient | None = None,
        article_mapper: ArticleMapper | None = None,
    ):
        self.db = db
        self.rss_client = rss_client or RSSClient()
        self.article_mapper = article_mapper or ArticleMapper()

    def ingest_feed(self, feed_id: UUID) -> IngestionResult:
        feed = self.db.execute(
            select(Feed).where(Feed.id == feed_id)
        ).scalar_one_or_none()
        if feed is None:
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
        if not technology_domain.is_enabled:
            return [
                IngestionResult(
                    technology_domain_id=technology_domain.id,
                    errors=["Technology domain is disabled."],
                )
            ]

        results: list[IngestionResult] = []
        for feed in technology_domain.feeds:
            if not feed.is_enabled:
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
        try:
            entries = self.rss_client.fetch_feed_entries(feed)
        except Exception as exc:
            result.errors.append(f"Feed fetch failed: {exc}")
            return result

        result.fetched_count = len(entries)

        for entry in entries:
            try:
                article_data = self.article_mapper.map_entry_to_article_data(
                    feed, entry
                )
            except (ValidationError, ValueError) as exc:
                result.skipped_count += 1
                result.errors.append(f"Entry skipped: {exc}")
                continue
            except Exception as exc:
                result.skipped_count += 1
                result.errors.append(f"Entry mapping failed: {exc}")
                continue

            existing = self.db.execute(
                select(Article.id).where(Article.url == article_data.url)
            ).scalar_one_or_none()
            if existing is not None:
                result.skipped_count += 1
                continue

            article = self._to_article_entity(article_data)
            self.db.add(article)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                result.skipped_count += 1
                continue
            result.created_count += 1

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
            is_processed=article_data.is_processed,
        )
