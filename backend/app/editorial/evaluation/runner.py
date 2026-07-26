"""
Developer evaluation runner.

This runner is intended for local development only.

Responsibilities:
- Load a limited number of feeds
- Fetch articles
- Execute the editorial pipeline
- Print readable results

This is NOT part of the production application.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from time import perf_counter
from uuid import UUID

from app.catalog.article.model import Article
from app.catalog.feed.model import Feed
from app.catalog.feed.repository import FeedRepository
from app.editorial.candidate_filter.enums import CandidateDecision
from app.editorial.candidate_filter.service import CandidateFilterService
from app.editorial.classification.models import (
    ClassificationInput,
    EditorialClassification,
)
from app.editorial.classification.openai_provider import OpenAIClassificationProvider
from app.infrastructure.logging import configure_logging, get_logger
from app.infrastructure.database.session import SessionLocal
from app.ingestion.mapper import ArticleMapper
from app.ingestion.models import NormalizedArticleData
from app.ingestion.rss_client import RSSClient
from pydantic import ValidationError

logger = get_logger(__name__)


@dataclass
class RunnerStats:
    selected_feeds: int = 0
    fetched_entries: int = 0
    candidate_count: int = 0
    classified_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Editorial Intelligence Evaluation Runner"
    )

    parser.add_argument(
        "--domain",
        required=True,
        choices=["AI", "SECURITY", "ML"],
        help="Technology domain to evaluate.",
    )

    parser.add_argument(
        "--max-feeds",
        type=int,
        default=5,
        help="Maximum number of enabled feeds to process.",
    )

    return parser.parse_args()


def main() -> None:
    run_started = perf_counter()
    args = parse_args()
    logger.info("Starting evaluation runner")
    logger.info("==============================")
    logger.info("Newsletter Run Started")
    logger.info("==============================")
    logger.info("Selected newsletter domain: %s", args.domain)
    print("=" * 70)
    print("Editorial Intelligence Evaluation")
    print("=" * 70)
    print(f"Domain     : {args.domain}")
    print(f"Max Feeds  : {args.max_feeds}")
    print("=" * 70)
    print()

    with SessionLocal() as db:
        feed_repository = FeedRepository(db)
        rss_client = RSSClient()
        article_mapper = ArticleMapper()
        candidate_filter = CandidateFilterService()
        classification_provider = OpenAIClassificationProvider()

        feeds = _select_feeds(
            feeds=feed_repository.list(),
            domain=args.domain,
            max_feeds=args.max_feeds,
        )
        logger.info("Feeds selected: %s", len(feeds))

        stats = RunnerStats(selected_feeds=len(feeds))
        seen_urls: set[str] = set()

        if not feeds:
            print("No enabled feeds found for the selected domain.")
            print()
            _print_summary(stats)
            logger.info("Run completed with no eligible feeds.")
            logger.info("Evaluation completed.")
            return

        for feed in feeds:
            feed_started = perf_counter()
            print(f"Feed: {feed.name} ({feed.url})")
            try:
                entries = rss_client.fetch_feed_entries(feed)
            except Exception as exc:
                stats.failed_count += 1
                print(f"  - fetch_failed: {exc}")
                logger.exception("Feed failed (feed_id=%s name=%s).", feed.id, feed.name)
                continue

            stats.fetched_entries += len(entries)
            logger.info(
                "Feed fetched (feed_id=%s name=%s entries=%s duration=%.2fs).",
                feed.id,
                feed.name,
                len(entries),
                perf_counter() - feed_started,
            )

            for entry in entries:
                try:
                    article_data = article_mapper.map_entry_to_article_data(feed, entry)
                except (ValidationError, ValueError) as exc:
                    stats.skipped_count += 1
                    print(f"  - skipped(mapper): {exc}")
                    continue
                except Exception as exc:
                    stats.failed_count += 1
                    print(f"  - failed(mapper): {exc}")
                    continue

                normalized_url = article_data.url.strip().lower()
                if normalized_url in seen_urls:
                    stats.skipped_count += 1
                    print(f"  - skipped(duplicate_url): {article_data.url}")
                    continue
                seen_urls.add(normalized_url)

                article = _to_candidate_article(feed, article_data)
                filter_result = candidate_filter.evaluate(article)
                if filter_result.decision == CandidateDecision.SKIP:
                    stats.skipped_count += 1
                    print(f"  - skipped({filter_result.reason}): {article_data.title}")
                    logger.info(
                        "Candidate rejected (reason=%s feed_id=%s).",
                        filter_result.reason,
                        feed.id,
                    )
                    continue

                stats.candidate_count += 1
                logger.info("Candidate accepted (feed_id=%s).", feed.id)
                classification_input = _to_classification_input(feed, article)

                try:
                    classification_started = perf_counter()
                    classification = classification_provider.classify(
                        classification_input
                    )
                    logger.info(
                        "Classification completed (feed_id=%s duration=%.2fs).",
                        feed.id,
                        perf_counter() - classification_started,
                    )
                except Exception as exc:
                    stats.failed_count += 1
                    print(f"  - failed(classification): {exc}")
                    logger.exception(
                        "Failed to classify article (feed_id=%s article_url=%s).",
                        feed.id,
                        article_data.url,
                    )
                    continue

                stats.classified_count += 1
                _print_classification_result(
                    feed, article.id, article_data.url, classification
                )

        print()
        _print_summary(stats)
        logger.info("Articles fetched: %s", stats.fetched_entries)
        logger.info("Articles after filtering: %s", stats.candidate_count)
        logger.info("Articles classified: %s", stats.classified_count)
        logger.info("Run completed. Duration: %.2fs", perf_counter() - run_started)
        logger.info("==============================")

    logger.info("Evaluation completed.")


def _select_feeds(feeds: Iterable[Feed], domain: str, max_feeds: int) -> list[Feed]:
    selected: list[Feed] = []
    for feed in feeds:
        if not feed.is_enabled:
            continue
        if feed.technology_domain is None or not feed.technology_domain.is_enabled:
            continue
        if feed.technology_domain.name.strip().upper() != domain.upper():
            continue
        selected.append(feed)
        if len(selected) >= max_feeds:
            break
    return selected


def _to_candidate_article(feed: Feed, article_data: NormalizedArticleData) -> Article:
    return Article(
        feed_id=feed.id,
        title=article_data.title,
        url=article_data.url,
        source_identifier=article_data.source_identifier,
        author=article_data.author,
        published_at=article_data.published_at,
        summary=article_data.summary,
        content=article_data.content,
        is_processed=article_data.is_processed,
        feed=feed,
    )


def _to_classification_input(feed: Feed, article: Article) -> ClassificationInput:
    domain_name = ""
    if feed.technology_domain is not None:
        domain_name = feed.technology_domain.name

    return ClassificationInput(
        title=article.title,
        source_name=feed.name,
        technology_domain=domain_name,
        summary=article.summary,
        content=article.content,
    )


def _print_classification_result(
    feed: Feed,
    article_id: UUID,
    url: str,
    classification: EditorialClassification,
) -> None:
    print(f"  - classified: {classification.article_type.value} | {url}")
    print(
        f"    severity={classification.severity.value} actionability={classification.actionability.value} audience={classification.audience.value} confidence={classification.confidence:.2f}"
    )
    if classification.topics:
        print(f"    topics={', '.join(classification.topics)}")
    if classification.technologies:
        print(f"    technologies={', '.join(classification.technologies)}")
    print(f"    feed={feed.name} article_id={article_id}")


def _print_summary(stats: RunnerStats) -> None:
    print("=" * 70)
    print("Run Summary")
    print("=" * 70)
    print(f"Selected Feeds   : {stats.selected_feeds}")
    print(f"Fetched Entries  : {stats.fetched_entries}")
    print(f"Candidates       : {stats.candidate_count}")
    print(f"Classified       : {stats.classified_count}")
    print(f"Skipped          : {stats.skipped_count}")
    print(f"Failed           : {stats.failed_count}")
    print("=" * 70)


if __name__ == "__main__":
    configure_logging(level=logging.INFO)

    main()
