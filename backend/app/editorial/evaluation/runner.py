"""
Developer-only editorial evaluation runner.

This runner is intended for local development only and does not:
- send emails
- alter production execution paths
"""

from __future__ import annotations

import argparse
import logging
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from time import perf_counter
from uuid import UUID

from app.catalog.article.model import Article
from app.catalog.article.repository import ArticleRepository
from app.catalog.feed.model import Feed
from app.catalog.feed.repository import FeedRepository
from app.core.settings import get_settings
from app.editorial.candidate_filter.candidates import (
    build_candidate_article,
    mark_article_processed,
)
from app.editorial.candidate_filter.enums import CandidateDecision
from app.editorial.candidate_filter.service import CandidateFilterService
from app.editorial.classification.models import (
    ClassificationBatchItem,
    ClassificationInput,
    EditorialClassification,
)
from app.editorial.classification.openai_provider import OpenAIClassificationProvider
from app.editorial.enrichment import classified_article_from_pipeline, enrich_article
from app.editorial.selection import SelectionPolicy, SelectionResult, SelectionTier
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.logging import configure_logging, get_logger
from app.ingestion.acquisition_factory import AcquisitionFactory
from app.ingestion.models import NormalizedArticleData

logger = get_logger(__name__)


@dataclass
class DomainSelectionStats:
    selected_for_enrichment: int = 0
    shown_on_ui: int = 0
    discarded: int = 0


@dataclass
class RunnerStats:
    feeds_processed: int = 0
    total_ingested: int = 0
    deduped_skipped: int = 0
    classified: int = 0
    enrichments_completed: int = 0
    failures: int = 0
    domain_stats: dict[str, DomainSelectionStats] = field(default_factory=dict)


@dataclass
class PendingEvaluation:
    article_id: str
    feed: Feed
    article_data: NormalizedArticleData
    article_index: int
    classification_input: ClassificationInput
    stored_article_id: UUID | None = None


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
    selection_policy = SelectionPolicy()
    acquisition_factory = AcquisitionFactory()
    pending_evaluations: list[PendingEvaluation] = []
    article_seq = 0

    logger.info(
        "editorial.run.start max_feeds=%s max_articles_per_feed=%s "
        "policy=SelectionPolicy classification_batch_size=%s",
        args.max_feeds,
        args.max_articles_per_feed,
        settings.classification_batch_size,
    )

    with SessionLocal() as db:
        feed_repository = FeedRepository(db)
        article_repository = ArticleRepository(db)
        feeds = _select_enabled_feeds(feed_repository.list(), args.max_feeds)

        if not feeds:
            logger.warning("editorial.run.no_feeds")
            _log_run_summary(stats=stats, run_started=run_started)
            return

        for feed in feeds:
            stats.feeds_processed += 1
            logger.info(
                "editorial.feed.start feed_id=%s feed_name=%s fetch_kind=%s url=%s",
                feed.id,
                feed.name,
                feed.fetch_kind,
                feed.url,
            )

            try:
                acquirer = acquisition_factory.for_feed(feed)
                acquisition = acquirer.acquire(feed)
            except Exception as exc:
                stats.failures += 1
                logger.exception(
                    "editorial.feed.acquire_failed feed_id=%s error=%s",
                    feed.id,
                    exc,
                )
                continue

            acquired = acquisition.articles[: args.max_articles_per_feed]
            stats.total_ingested += len(acquired)
            logger.info(
                "editorial.feed.acquired feed_id=%s acquired=%s raw_discovered=%s warnings=%s",
                feed.id,
                len(acquired),
                acquisition.fetched_count,
                len(acquisition.errors),
            )
            for warning in acquisition.errors[:5]:
                logger.warning(
                    "editorial.feed.acquire_warning feed_id=%s warning=%s",
                    feed.id,
                    warning,
                )

            for idx, article_data in enumerate(acquired, start=1):
                article, stored_article_id = build_candidate_article(
                    feed,
                    article_data,
                    article_repository,
                )

                try:
                    filter_result = candidate_filter.evaluate(article)
                except Exception as exc:
                    stats.failures += 1
                    logger.exception(
                        "editorial.dedup.failed feed_id=%s url=%s error=%s",
                        feed.id,
                        article_data.url,
                        exc,
                    )
                    continue

                if filter_result.decision == CandidateDecision.SKIP:
                    stats.deduped_skipped += 1
                    logger.info(
                        "editorial.dedup.skip feed_id=%s url=%s reason=%s title=%s",
                        feed.id,
                        article_data.url,
                        filter_result.reason,
                        article_data.title,
                    )
                    continue

                article_seq += 1
                article_id = f"eval_{article_seq}"
                pending_evaluations.append(
                    PendingEvaluation(
                        article_id=article_id,
                        feed=feed,
                        article_data=article_data,
                        article_index=idx,
                        classification_input=_to_classification_input(feed, article),
                        stored_article_id=stored_article_id,
                    )
                )
                logger.info(
                    "editorial.dedup.pass article_id=%s feed_id=%s url=%s",
                    article_id,
                    feed.id,
                    article_data.url,
                )

        classifications_by_id: dict[str, EditorialClassification] = {}
        if pending_evaluations:
            logger.info(
                "editorial.classification.batch_start count=%s batch_size=%s",
                len(pending_evaluations),
                settings.classification_batch_size,
            )
            try:
                batch_items = [
                    ClassificationBatchItem(
                        article_id=item.article_id,
                        classification_input=item.classification_input,
                    )
                    for item in pending_evaluations
                ]
                classifications_by_id = classification_provider.classify_many(batch_items)
            except Exception as exc:
                stats.failures += len(pending_evaluations)
                logger.exception(
                    "editorial.classification.batch_failed count=%s error=%s",
                    len(pending_evaluations),
                    exc,
                )
                _log_run_summary(stats=stats, run_started=run_started)
                return

        classified_by_domain: dict[str, list[tuple[str, EditorialClassification]]] = (
            defaultdict(list)
        )
        for pending in pending_evaluations:
            classification = classifications_by_id.get(pending.article_id)
            if classification is None:
                stats.failures += 1
                logger.error(
                    "editorial.classification.missing article_id=%s feed_id=%s url=%s",
                    pending.article_id,
                    pending.feed.id,
                    pending.article_data.url,
                )
                continue

            stats.classified += 1
            logger.info(
                "editorial.classification article_id=%s article_type=%s severity=%s "
                "actionability=%s confidence=%.2f",
                pending.article_id,
                classification.article_type.value,
                classification.severity.value,
                classification.actionability.value,
                classification.confidence,
            )

            mark_article_processed(
                article_repository,
                pending.feed,
                pending.article_data,
                stored_article_id=pending.stored_article_id,
            )
            classified_by_domain[_domain_name(pending)].append(
                (pending.article_id, classification)
            )

        selection_by_id: dict[str, SelectionResult] = {}
        for domain_name, classified in classified_by_domain.items():
            selection_by_id.update(
                selection_policy.select_for_domain(domain_name, classified)
            )

        for pending in pending_evaluations:
            selection = selection_by_id.get(pending.article_id)
            if selection is None:
                continue

            domain_name = _domain_name(pending)
            _record_selection(stats, domain_name, selection.tier)
            logger.info(
                "editorial.selection article_id=%s domain=%s group_key=%s "
                "rank_within_group=%s rank_score=%s tier=%s",
                pending.article_id,
                domain_name,
                selection.group_key,
                selection.rank_within_group,
                selection.rank_score,
                selection.tier.value,
            )

            if selection.tier != SelectionTier.SELECTED_FOR_ENRICHMENT:
                continue

            classification = classifications_by_id[pending.article_id]
            try:
                classified = classified_article_from_pipeline(
                    source_name=pending.feed.name or "",
                    url=pending.article_data.url,
                    published_at=pending.article_data.published_at,
                    summary=pending.article_data.summary,
                    content=pending.article_data.content,
                    classification=classification,
                )
                enrich_article(classified, settings=settings)
                stats.enrichments_completed += 1
            except Exception as exc:
                stats.failures += 1
                logger.exception(
                    "editorial.enrichment.failed article_id=%s feed_id=%s url=%s error=%s",
                    pending.article_id,
                    pending.feed.id,
                    pending.article_data.url,
                    exc,
                )

    _log_run_summary(stats=stats, run_started=run_started)


def _domain_name(pending: PendingEvaluation) -> str:
    domain = pending.feed.technology_domain
    return domain.name if domain is not None else "UNKNOWN"


def _record_selection(
    stats: RunnerStats,
    domain_name: str,
    tier: SelectionTier,
) -> None:
    domain_stats = stats.domain_stats.setdefault(domain_name, DomainSelectionStats())
    if tier == SelectionTier.SELECTED_FOR_ENRICHMENT:
        domain_stats.selected_for_enrichment += 1
    elif tier == SelectionTier.SHOWN_ON_UI:
        domain_stats.shown_on_ui += 1
    else:
        domain_stats.discarded += 1


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


def _to_classification_input(feed: Feed, article: Article) -> ClassificationInput:
    domain = feed.technology_domain
    return ClassificationInput(
        title=article.title or "",
        source_name=feed.name or "",
        technology_domain=domain.name if domain is not None else "",
        technology_domain_description=domain.description if domain is not None else None,
        summary=article.summary,
        content=article.content,
    )


def _format_domain_stats(stats: RunnerStats) -> str:
    if not stats.domain_stats:
        return "none"
    parts: list[str] = []
    for domain_name in sorted(stats.domain_stats):
        domain_stats = stats.domain_stats[domain_name]
        parts.append(
            f"{domain_name}:selected={domain_stats.selected_for_enrichment},"
            f"ui={domain_stats.shown_on_ui},discard={domain_stats.discarded}"
        )
    return ";".join(parts)


def _log_run_summary(stats: RunnerStats, run_started: float) -> None:
    logger.info(
        "editorial.run.summary total_ingested=%s deduped_skipped=%s classified=%s "
        "enrichments_completed=%s domain_counts=%s failures=%s duration_s=%.2f",
        stats.total_ingested,
        stats.deduped_skipped,
        stats.classified,
        stats.enrichments_completed,
        _format_domain_stats(stats),
        stats.failures,
        perf_counter() - run_started,
    )


if __name__ == "__main__":
    configure_logging(level=logging.INFO)
    main()
