"""
Developer-only editorial evaluation runner.

This runner is intended for local development only and does not:
- persist data
- read article rows from the database
- send emails
- alter production execution paths
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from time import perf_counter

from app.catalog.article.model import Article
from app.catalog.feed.model import Feed
from app.catalog.feed.repository import FeedRepository
from app.core.settings import get_settings
from app.editorial.candidate_filter.enums import CandidateDecision
from app.editorial.candidate_filter.service import CandidateFilterService
from app.editorial.classification.models import ClassificationInput, EditorialClassification
from app.editorial.classification.openai_provider import OpenAIClassificationProvider
from app.editorial.decision import (
    DecisionDiagnostics,
    EditorialDecision,
    EditorialDecisionEngine,
)
from app.editorial.enrichment import (
    EditorialEnrichment,
    OpenAIEditorialEnrichmentProvider,
)
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.logging import configure_logging, get_logger
from app.ingestion.acquisition_factory import AcquisitionFactory
from app.ingestion.models import NormalizedArticleData
from pydantic import BaseModel, ConfigDict, Field

logger = get_logger(__name__)


@dataclass
class RunnerStats:
    feeds_processed: int = 0
    articles_acquired: int = 0
    articles_evaluated: int = 0
    classifications_completed: int = 0
    enrichments_completed: int = 0
    decisions_made: int = 0
    failures: int = 0

class NewsletterCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str = Field(min_length=1, max_length=200)
    source: str = Field(min_length=1, max_length=255)
    article_url: str = Field(min_length=1, max_length=2048)
    highlights: list[str] = Field(default_factory=list)
    decision_label: str = Field(min_length=1, max_length=64)

class NewsletterCardGenerator:
    def generate(
        self,
        *,
        feed: Feed,
        article: NormalizedArticleData,
        classification: EditorialClassification,
        enrichment: EditorialEnrichment,
        decision: EditorialDecision,
    ) -> NewsletterCard:
        highlights = []
        highlights.extend(enrichment.key_points[:3])
        if classification.topics:
            highlights.append(f"Topics: {', '.join(classification.topics[:3])}")
        if classification.technologies:
            highlights.append(
                f"Technologies: {', '.join(classification.technologies[:3])}"
            )

        label = "Include" if decision.include_in_newsletter else "Skip"
        label = f"{label} ({decision.priority})"

        return NewsletterCard(
            headline=article.title,
            source=feed.name,
            article_url=article.url,
            highlights=highlights[:5],
            decision_label=label,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Developer-only Editorial Evaluation Runner"
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
        help="Maximum acquired articles to evaluate per feed.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_started = perf_counter()
    stats = RunnerStats()

    settings = get_settings()
    candidate_filter = CandidateFilterService()
    classification_provider = OpenAIClassificationProvider(settings=settings)
    enrichment_provider = OpenAIEditorialEnrichmentProvider(settings=settings)
    decision_engine = EditorialDecisionEngine()
    card_generator = NewsletterCardGenerator()
    acquisition_factory = AcquisitionFactory()

    print("=" * 88)
    print("Developer Editorial Evaluation Runner")
    print("=" * 88)
    print(f"Max feeds              : {args.max_feeds}")
    print(f"Max articles per feed  : {args.max_articles_per_feed}")
    print("=" * 88)
    print()

    with SessionLocal() as db:
        feed_repository = FeedRepository(db)
        feeds = _select_enabled_feeds(feed_repository.list(), args.max_feeds)

        if not feeds:
            print("No enabled feeds available.")
            print()
            _print_summary(stats, run_started)
            return

        for feed in feeds:
            stats.feeds_processed += 1
            print(
                f"Feed: {feed.name} | kind={feed.fetch_kind} | crawl_depth={feed.crawl_depth or 1}"
            )
            print(f"  URL: {feed.url}")

            try:
                acquirer = acquisition_factory.for_feed(feed)
                acquisition = acquirer.acquire(feed)
            except Exception as exc:
                stats.failures += 1
                print(f"  - acquire_failed: {exc}")
                logger.exception("Feed acquisition failed (feed_id=%s).", feed.id)
                print()
                continue

            stats.articles_acquired += len(acquisition.articles)
            print(
                f"  Acquired: {len(acquisition.articles)} normalized articles "
                f"(raw discovered={acquisition.fetched_count})"
            )
            if acquisition.errors:
                print(f"  Acquisition warnings: {len(acquisition.errors)}")
                for warning in acquisition.errors[:5]:
                    print(f"    - {warning}")

            for idx, article_data in enumerate(
                acquisition.articles[: args.max_articles_per_feed], start=1
            ):
                stats.articles_evaluated += 1
                print(f"  Article #{idx}: {article_data.title}")
                print(f"    URL: {article_data.url}")

                article = _to_candidate_article(feed, article_data)

                try:
                    filter_result = candidate_filter.evaluate(article)
                    print(
                        "    Candidate Filter: "
                        f"{filter_result.decision.value} ({filter_result.reason})"
                    )
                except Exception as exc:
                    stats.failures += 1
                    print(f"    Candidate Filter Failed: {exc}")
                    logger.exception(
                        "Candidate filter failed (feed_id=%s url=%s).",
                        feed.id,
                        article_data.url,
                    )
                    continue

                if filter_result.decision == CandidateDecision.SKIP:
                    print("    Classification: skipped")
                    print("    Enrichment: skipped")
                    print("    Decision: skipped")
                    print("    Newsletter Card: skipped")
                    print()
                    continue

                classification_input = _to_classification_input(feed, article)
                try:
                    classification = classification_provider.classify(classification_input)
                    stats.classifications_completed += 1
                    _print_classification(classification)
                except Exception as exc:
                    stats.failures += 1
                    print(f"    Classification Failed: {exc}")
                    logger.exception(
                        "Classification failed (feed_id=%s url=%s).",
                        feed.id,
                        article_data.url,
                    )
                    print()
                    continue

                try:
                    decision = decision_engine.decide(classification)
                    stats.decisions_made += 1
                    _print_decision(decision, phase="pre-enrichment")
                    diagnostics = decision_engine.build_diagnostics(
                        classification=classification,
                        decision=decision,
                    )
                    _print_decision_diagnostics(diagnostics)
                except Exception as exc:
                    stats.failures += 1
                    print(f"    Decision Engine Failed: {exc}")
                    logger.exception(
                        "Decision engine failed (feed_id=%s url=%s).",
                        feed.id,
                        article_data.url,
                    )
                    print()
                    continue

                if not decision.include_in_newsletter:
                    print(
                        "    Enrichment: skipped intentionally "
                        "(decision include=False)"
                    )
                    print(
                        "    Newsletter Card: skipped intentionally "
                        "(decision include=False)"
                    )
                    print()
                    continue

                try:
                    enrichment = enrichment_provider.enrich(
                        article=article_data,
                        classification=classification,
                    )
                    stats.enrichments_completed += 1
                    _print_enrichment(enrichment)
                except Exception as exc:
                    stats.failures += 1
                    print(f"    Enrichment Failed: {exc}")
                    logger.exception(
                        "Enrichment failed (feed_id=%s url=%s).",
                        feed.id,
                        article_data.url,
                    )
                    print()
                    continue

                decision = decision_engine.finalize_with_enrichment(decision, enrichment)
                _print_decision(decision, phase="final")

                try:
                    card = card_generator.generate(
                        feed=feed,
                        article=article_data,
                        classification=classification,
                        enrichment=enrichment,
                        decision=decision,
                    )
                    _print_newsletter_card(card)
                except Exception as exc:
                    stats.failures += 1
                    print(f"    Newsletter Card Failed: {exc}")
                    logger.exception(
                        "Card generation failed (feed_id=%s url=%s).",
                        feed.id,
                        article_data.url,
                    )

                print()

            print()

    _print_summary(stats, run_started)


def _select_enabled_feeds(feeds: Iterable[Feed], max_feeds: int) -> list[Feed]:
    selected: list[Feed] = []
    for feed in feeds:
        if not feed.is_enabled:
            continue
        if feed.technology_domain is not None and not feed.technology_domain.is_enabled:
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


def _print_classification(classification: EditorialClassification) -> None:
    print(
        "    Classification: "
        f"type={classification.article_type.value} "
        f"severity={classification.severity.value} "
        f"actionability={classification.actionability.value} "
        f"audience={classification.audience.value} "
        f"confidence={classification.confidence:.2f}"
    )
    if classification.topics:
        print(f"      Topics: {', '.join(classification.topics)}")
    if classification.technologies:
        print(f"      Technologies: {', '.join(classification.technologies)}")


def _print_enrichment(enrichment: EditorialEnrichment) -> None:
    print("    Enrichment:")
    if enrichment.key_points:
        for point in enrichment.key_points:
            print(f"      - {point}")
    print(f"      Business Impact: {enrichment.business_impact}")
    print(f"      Recommended Action: {enrichment.recommended_action}")


def _print_decision(decision: EditorialDecision, phase: str) -> None:
    print(
        f"    Decision Engine ({phase}): "
        f"include={decision.include_in_newsletter} "
        f"priority={decision.priority} "
        f"rationale={decision.rationale}"
    )


def _print_newsletter_card(card: NewsletterCard) -> None:
    print("    Newsletter Card:")
    print(f"      Headline: {card.headline}")
    print(f"      Source: {card.source}")
    print(f"      URL: {card.article_url}")
    print(f"      Decision: {card.decision_label}")
    if card.highlights:
        for highlight in card.highlights:
            print(f"      Highlight: {highlight}")


def _print_decision_diagnostics(diagnostics: DecisionDiagnostics) -> None:
    print("    Decision Diagnostics:")
    for signal in diagnostics.signals:
        print(
            f"      {signal.name}: {signal.value} -> +{signal.contribution}"
        )
    print(f"      Final Score: {diagnostics.final_score}")
    print(f"      Threshold: {diagnostics.threshold}")
    print(f"      Result: include={diagnostics.include}")
    if diagnostics.rejection_reasons:
        print("      Rejection Reasons:")
        for reason in diagnostics.rejection_reasons:
            print(f"        - {reason}")


def _print_summary(stats: RunnerStats, run_started: float) -> None:
    print("=" * 88)
    print("Run Summary")
    print("=" * 88)
    print(f"Feeds processed           : {stats.feeds_processed}")
    print(f"Articles acquired         : {stats.articles_acquired}")
    print(f"Articles evaluated        : {stats.articles_evaluated}")
    print(f"Classifications completed : {stats.classifications_completed}")
    print(f"Enrichments completed     : {stats.enrichments_completed}")
    print(f"Decisions made            : {stats.decisions_made}")
    print(f"Failures                  : {stats.failures}")
    print(f"Duration (s)              : {perf_counter() - run_started:.2f}")
    print("=" * 88)


if __name__ == "__main__":
    configure_logging(level=logging.INFO)
    main()
