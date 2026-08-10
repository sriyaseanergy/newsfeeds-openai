"""
Developer-only Crawl4AI debug runner.

This runner is intended for local development and troubleshooting only.
It does not persist data and does not invoke editorial pipeline stages.
"""

from __future__ import annotations

import argparse
from uuid import UUID

from app.catalog.article.model import Article
from app.catalog.feed.model import Feed, FetchKind
from app.ingestion.acquisition import FeedAcquisitionResult
from app.ingestion.acquisition_factory import AcquisitionFactory
from app.infrastructure.database.session import SessionLocal
from sqlalchemy import Select, func, select
from sqlalchemy.orm import joinedload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Developer Crawl4AI debug runner (non-persistent)."
    )
    parser.add_argument(
        "feed",
        help="Feed ID (UUID) or feed name.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    feed = _resolve_feed(db_feed_selector=args.feed)
    if feed is None:
        print(f"Feed not found: {args.feed}")
        return

    if feed.fetch_kind != FetchKind.CRAWL:
        print(
            "Unsupported feed kind for this debug runner: "
            f"{feed.fetch_kind} (only CRAWL is supported)."
        )
        return

    factory = AcquisitionFactory()
    acquirer = factory.for_feed(feed)
    known_urls = _known_article_urls_for_feed(feed.id)
    acquisition = acquirer.acquire(feed, known_urls=known_urls)
    _print_report(feed=feed, acquisition=acquisition)


def _resolve_feed(db_feed_selector: str) -> Feed | None:
    with SessionLocal() as db:
        statement = _feed_lookup_statement(db_feed_selector)
        return db.execute(statement).scalar_one_or_none()


def _feed_lookup_statement(selector: str) -> Select[tuple[Feed]]:
    selector = selector.strip()
    statement = select(Feed).options(joinedload(Feed.technology_domain))

    feed_id = _try_parse_uuid(selector)
    if feed_id is not None:
        return statement.where(Feed.id == feed_id)

    return statement.where(func.lower(Feed.name) == selector.lower())


def _known_article_urls_for_feed(feed_id: UUID) -> set[str]:
    with SessionLocal() as db:
        statement = select(Article.url).where(Article.feed_id == feed_id)
        urls = db.execute(statement).scalars().all()
        return {str(url).strip().lower() for url in urls if str(url).strip()}


def _try_parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


def _print_report(
    feed: Feed,
    acquisition: FeedAcquisitionResult,
) -> None:
    metrics = acquisition.metrics
    listing_pages_crawled = int(metrics.get("listing_pages_crawled", 0))
    article_links_discovered = int(metrics.get("article_links_discovered", acquisition.fetched_count))
    existing_urls_skipped = int(metrics.get("existing_urls_skipped", 0))
    article_pages_crawled = int(metrics.get("article_pages_crawled", 0))
    successful_article_extractions = int(
        metrics.get("successful_article_extractions", len(acquisition.articles))
    )
    failed_article_extractions = int(metrics.get("failed_article_extractions", 0))
    average_content_length = int(metrics.get("average_content_length", 0.0))

    print("=" * 80)
    print("Crawl4AI Debug Runner")
    print("=" * 80)
    print(f"Feed ID                      : {feed.id}")
    print(f"Feed Name                    : {feed.name}")
    print(f"Feed URL                     : {feed.url}")
    print(f"Feed Kind                    : {feed.fetch_kind}")
    print(f"Technology Domain            : {feed.technology_domain.name if feed.technology_domain else '-'}")
    print(f"Crawl Depth                  : {feed.crawl_depth or 1}")
    print(f"Listing Pages Crawled        : {listing_pages_crawled}")
    print(f"Article Links Discovered     : {article_links_discovered}")
    print(f"Existing URLs Skipped        : {existing_urls_skipped}")
    print(f"Article Pages Crawled        : {article_pages_crawled}")
    print(f"Successful Extractions       : {successful_article_extractions}")
    print(f"Failed Extractions           : {failed_article_extractions}")
    print(f"Average Content Length       : {average_content_length}")
    print(f"Normalized Articles Returned : {len(acquisition.articles)}")
    if acquisition.errors:
        print(f"Acquisition Warnings         : {len(acquisition.errors)}")
    print("=" * 80)

    for idx, article in enumerate(acquisition.articles, start=1):
        print(f"[{idx}] {article.title}")
        print(f"    URL       : {article.url}")
        print(
            "    Published : "
            f"{article.published_at.isoformat() if article.published_at else '-'}"
        )
        print(f"    Summary   : {'Yes' if article.summary else 'No'}")
        content = (article.content or "").strip()
        print(f"    Content Length : {len(content)}")
        preview = content[:300]
        print(f"    Content Preview: {preview}")
        print()

    if acquisition.errors:
        print("Warnings:")
        for warning in acquisition.errors:
            print(f"  - {warning}")


if __name__ == "__main__":
    main()
