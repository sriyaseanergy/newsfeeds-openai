"""
Developer-only newsletter HTML preview runner.

Acquires and evaluates articles like the editorial runner, collects
include=True results, and writes rendered newsletter HTML to disk.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from app.catalog.article.model import Article
from app.catalog.feed.model import Feed
from app.catalog.feed.repository import FeedRepository
from app.core.settings import get_settings
from app.editorial.candidate_filter.enums import CandidateDecision
from app.editorial.candidate_filter.service import CandidateFilterService
from app.editorial.classification.models import (
    ClassificationBatchItem,
    ClassificationInput,
)
from app.editorial.classification.openai_provider import OpenAIClassificationProvider
from app.editorial.decision import AIEditorialDecisionPolicy, EditorialDecisionEngine
from app.editorial.enrichment import OpenAIEditorialEnrichmentProvider
from app.editorial.evaluation.runner import PendingEvaluation, _select_enabled_feeds
from app.editorial.newsletter import (
    NewsletterRenderConfig,
    NewsletterRenderInput,
    NewsletterRenderer,
    newsletter_article_from_pipeline,
)
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.logging import configure_logging, get_logger
from app.ingestion.acquisition_factory import AcquisitionFactory

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render newsletter HTML from a live editorial evaluation run.",
    )
    parser.add_argument(
        "--max-feeds",
        type=int,
        default=5,
        help="Maximum number of enabled feeds to process.",
    )
    parser.add_argument(
        "--max-articles-per-feed",
        type=int,
        default=3,
        help="Maximum articles to evaluate per feed.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("newsletter_preview.html"),
        help="Path for the rendered HTML output file.",
    )
    return parser.parse_args()


def _to_candidate_article(feed: Feed, article_data) -> Article:
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
    domain_name = (
        feed.technology_domain.name if feed.technology_domain is not None else ""
    )
    return ClassificationInput(
        title=article.title or "",
        source_name=feed.name or "",
        technology_domain=domain_name,
        summary=article.summary,
        content=article.content,
    )


def main() -> None:
    args = parse_args()
    settings = get_settings()
    configure_logging(settings)

    session = SessionLocal()
    feed_repository = FeedRepository(session)
    acquisition_factory = AcquisitionFactory()
    candidate_filter = CandidateFilterService()
    classification_provider = OpenAIClassificationProvider(settings=settings)
    enrichment_provider = OpenAIEditorialEnrichmentProvider(settings=settings)
    decision_engine = EditorialDecisionEngine(policy=AIEditorialDecisionPolicy())
    renderer = NewsletterRenderer()

    included_articles: list = []
    pending_evaluations: list[PendingEvaluation] = []

    try:
        feeds = _select_enabled_feeds(
            feed_repository.list(),
            args.max_feeds,
        )
        print(f"Selected feeds: {len(feeds)}")

        for feed in feeds:
            acquirer = acquisition_factory.for_feed(feed)
            acquisition = acquirer.acquire(feed)
            articles = acquisition.articles[: args.max_articles_per_feed]
            print(f"  {feed.name}: acquired {len(articles)} articles")

            for index, article_data in enumerate(articles, start=1):
                article = _to_candidate_article(feed, article_data)
                filter_result = candidate_filter.evaluate(article)
                if filter_result.decision == CandidateDecision.SKIP:
                    continue

                pending_evaluations.append(
                    PendingEvaluation(
                        article_id=f"preview_{feed.id}_{index}",
                        feed=feed,
                        article_data=article_data,
                        article=article,
                        article_index=index,
                        classification_input=_to_classification_input(feed, article),
                    )
                )

        if pending_evaluations:
            batch_items = [
                ClassificationBatchItem(
                    article_id=pending.article_id,
                    classification_input=pending.classification_input,
                )
                for pending in pending_evaluations
            ]
            classifications_by_id = classification_provider.classify_many(batch_items)
        else:
            classifications_by_id = {}

        for pending in pending_evaluations:
            classification = classifications_by_id.get(pending.article_id)
            if classification is None:
                logger.warning(
                    "Skipping article without classification (article_id=%s).",
                    pending.article_id,
                )
                continue

            decision = decision_engine.decide(classification)
            if not decision.include_in_newsletter:
                continue

            enrichment = enrichment_provider.enrich(
                article=pending.article_data,
                classification=classification,
            )
            included_articles.append(
                newsletter_article_from_pipeline(
                    title=pending.article_data.title,
                    url=pending.article_data.url,
                    source_name=pending.feed.name,
                    published_at=pending.article_data.published_at,
                    classification=classification,
                    enrichment=enrichment,
                )
            )

        render_input = NewsletterRenderInput(
            articles=included_articles,
            config=NewsletterRenderConfig(generated_at=datetime.now(UTC)),
        )
        html_output = renderer.render(render_input)
        output_path = args.output.resolve()
        output_path.write_text(html_output, encoding="utf-8")

        print()
        print(f"Included articles : {len(included_articles)}")
        print(f"Rendered HTML     : {output_path}")
        print(
            "Sample block absent : "
            f"{('STATIC_SAMPLE_SECTIONS_START' not in html_output)}"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
