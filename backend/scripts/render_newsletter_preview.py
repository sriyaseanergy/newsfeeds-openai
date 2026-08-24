"""
Developer-only newsletter HTML preview runner.

Acquires and evaluates articles like the editorial runner, collects
include=True results, and writes rendered newsletter HTML to disk.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import argparse
import logging
from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from app.catalog.article.model import Article
from app.catalog.article.repository import ArticleRepository
from app.catalog.feed.model import Feed, FetchKind
from app.catalog.feed.repository import FeedRepository
from app.core.settings import get_settings
from app.editorial.classification.enums import (
    Actionability,
    ArticleType,
    Severity,
)
from app.editorial.candidate_filter.candidates import (
    build_candidate_article,
    mark_article_processed,
)
from app.editorial.candidate_filter.enums import CandidateDecision
from app.editorial.candidate_filter.rules import (
    CandidateRule,
    EditorialWindowRule,
    EmptyContentRule,
    MissingTitleRule,
    MissingUrlRule,
)
from app.editorial.candidate_filter.service import CandidateFilterService
from app.editorial.classification.models import (
    ClassificationBatchItem,
    ClassificationInput,
)
from app.editorial.classification.openai_provider import OpenAIClassificationProvider
from app.editorial.enrichment import (
    EnrichedArticle,
    AudienceSummary,
    classified_article_from_pipeline,
    enrich_article,
)
from app.editorial.evaluation.runner import PendingEvaluation, _domain_name
from app.editorial.selection import SelectionPolicy, SelectionResult, SelectionTier
from app.editorial.newsletter import (
    NewsletterArticle,
    NewsletterRenderConfig,
    NewsletterRenderInput,
    NewsletterRenderer,
    newsletter_article_from_pipeline,
)
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.logging import configure_logging, get_logger
from app.ingestion.acquisition_factory import AcquisitionFactory
from app.ingestion.models import NormalizedArticleData

logger = get_logger(__name__)

_DEMO_DOMAIN_ID = UUID("00000000-0000-0000-0000-000000000001")


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
    parser.add_argument(
        "--rss-only",
        action="store_true",
        help="Skip crawl feeds (avoids Playwright dependency).",
    )
    parser.add_argument(
        "--demo-sections",
        action="store_true",
        help=(
            "Fill missing section types with sample articles so the HTML preview "
            "shows RELEASES, RESEARCH, and NOTABLE READS layouts."
        ),
    )
    parser.add_argument(
        "--include-processed",
        action="store_true",
        help="Re-evaluate articles already marked is_processed (dev preview only).",
    )
    return parser.parse_args()


def _build_candidate_filter(*, include_processed: bool) -> CandidateFilterService:
    rules: list[CandidateRule] = [
        MissingTitleRule(),
        MissingUrlRule(),
        EmptyContentRule(),
    ]
    if not include_processed:
        from app.editorial.candidate_filter.rules import AlreadyProcessedRule

        rules.append(AlreadyProcessedRule())
    rules.append(EditorialWindowRule())
    return CandidateFilterService(rules=rules)


def _demo_enrichment(tldr: str, *, source_url: str) -> EnrichedArticle:
    return EnrichedArticle(
        tldr=tldr,
        why_it_matters=AudienceSummary(
            executive="Sample executive impact for newsletter layout preview.",
            technical_leadership=(
                "Sample technical leadership impact for newsletter layout preview."
            ),
            engineering="Sample engineering impact for newsletter layout preview.",
        ),
        key_details=[],
        recommended_action="Review section styling in the rendered HTML.",
        tags=["preview", "demo"],
        source_urls=[source_url],
        confidence=0.9,
    )


def _section_kind_for_article(article: NewsletterArticle) -> str:
    if article.severity == Severity.CRITICAL:
        return "critical"
    if article.article_type == ArticleType.RELEASE:
        return "releases"
    if article.article_type == ArticleType.RESEARCH:
        return "research"
    return "notable_reads"


def _demo_articles_for_missing_sections(
    articles: list[NewsletterArticle],
) -> list[NewsletterArticle]:
    represented = {_section_kind_for_article(article) for article in articles}
    published = datetime(2026, 7, 6, tzinfo=UTC)
    samples: list[NewsletterArticle] = []

    if "critical" not in represented:
        demo_url = "https://example.com/api-gateway-rce-patch"
        samples.append(
            NewsletterArticle(
                title="Critical RCE patched in widely deployed API gateway",
                url=demo_url,
                source_name="CISA Alerts",
                published_at=published,
                article_type=ArticleType.NEWS,
                technology_domain_id=_DEMO_DOMAIN_ID,
                technology_domain="SECURITY",
                severity=Severity.CRITICAL,
                actionability=Actionability.IMMEDIATE_ACTION,
                enrichment=_demo_enrichment(
                    "A pre-auth remote code execution flaw affects default "
                    "configurations; vendors issued emergency patches and "
                    "exploit attempts were observed in the wild.",
                    source_url=demo_url,
                ),
            )
        )
    if "releases" not in represented:
        demo_url = "https://example.com/openai-agent-sdk"
        samples.append(
            NewsletterArticle(
                title="OpenAI launches agent SDK with built-in tool orchestration",
                url=demo_url,
                source_name="TechCrunch",
                published_at=published,
                article_type=ArticleType.RELEASE,
                technology_domain_id=_DEMO_DOMAIN_ID,
                technology_domain="AI",
                severity=Severity.NONE,
                actionability=Actionability.INFORMATIONAL,
                enrichment=_demo_enrichment(
                    "The new SDK lets developers compose multi-step agents with "
                    "memory, retrieval, and guardrails in a single configuration file.",
                    source_url=demo_url,
                ),
            )
        )
    if "research" not in represented:
        demo_url = "https://example.com/sparse-moe-scaling"
        samples.append(
            NewsletterArticle(
                title="Scaling laws for sparse mixture-of-experts at inference time",
                url=demo_url,
                source_name="ArXiv",
                published_at=published,
                article_type=ArticleType.RESEARCH,
                technology_domain_id=_DEMO_DOMAIN_ID,
                technology_domain="AI",
                severity=Severity.NONE,
                actionability=Actionability.INFORMATIONAL,
                enrichment=_demo_enrichment(
                    "Researchers report predictable quality gains when routing "
                    "tokens through wider expert pools under fixed latency budgets.",
                    source_url=demo_url,
                ),
            )
        )
    if "notable_reads" not in represented:
        demo_url = "https://example.com/retrieval-quality-agents"
        samples.append(
            NewsletterArticle(
                title="Why retrieval quality matters more than model size for agents",
                url=demo_url,
                source_name="Simon Willison",
                published_at=published,
                article_type=ArticleType.BLOG,
                technology_domain_id=_DEMO_DOMAIN_ID,
                technology_domain="AI",
                severity=Severity.NONE,
                actionability=Actionability.MONITOR,
                enrichment=_demo_enrichment(
                    "Practitioner notes argue that grounded context beats raw "
                    "parameter count for reliable tool-using workflows.",
                    source_url=demo_url,
                ),
            )
        )

    return samples


def _merge_demo_sections(
    articles: list[NewsletterArticle],
    *,
    enabled: bool,
) -> list[NewsletterArticle]:
    if not enabled:
        return articles
    demo_articles = _demo_articles_for_missing_sections(articles)
    if not demo_articles:
        return articles
    return [*articles, *demo_articles]


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


def _select_preview_feeds(
    feeds: list[Feed],
    *,
    max_feeds: int,
    rss_only: bool,
) -> list[Feed]:
    selected: list[Feed] = []
    for feed in feeds:
        if not feed.is_enabled:
            continue
        if feed.technology_domain is not None and not feed.technology_domain.is_enabled:
            continue
        if rss_only and feed.fetch_kind != FetchKind.RSS:
            continue
        selected.append(feed)
        if len(selected) >= max_feeds:
            break
    return selected


def main() -> None:
    args = parse_args()
    settings = get_settings()
    configure_logging(level=logging.INFO)

    candidate_filter = _build_candidate_filter(include_processed=args.include_processed)
    classification_provider = OpenAIClassificationProvider(settings=settings)
    selection_policy = SelectionPolicy()
    acquisition_factory = AcquisitionFactory()
    renderer = NewsletterRenderer()

    included_articles = []
    pending_evaluations: list[PendingEvaluation] = []
    article_seq = 0

    with SessionLocal() as db:
        feed_repository = FeedRepository(db)
        article_repository = ArticleRepository(db)
        feeds = _select_preview_feeds(
            feed_repository.list(),
            max_feeds=args.max_feeds,
            rss_only=args.rss_only,
        )
        print(f"Selected feeds: {len(feeds)}")

        for feed in feeds:
            try:
                acquirer = acquisition_factory.for_feed(feed)
                acquisition = acquirer.acquire(feed)
            except Exception as exc:
                print(f"  {feed.name}: acquisition failed ({type(exc).__name__}: {exc})")
                continue

            articles = acquisition.articles[: args.max_articles_per_feed]
            print(f"  {feed.name}: acquired {len(articles)} articles")

            for article_data in articles:
                article_seq += 1
                article, stored_article_id = build_candidate_article(
                    feed,
                    article_data,
                    article_repository,
                )
                filter_result = candidate_filter.evaluate(article)
                if filter_result.decision == CandidateDecision.SKIP:
                    continue

                pending_evaluations.append(
                    PendingEvaluation(
                        article_id=f"preview_{article_seq}",
                        feed=feed,
                        article_data=article_data,
                        article_index=article_seq,
                        classification_input=_to_classification_input(feed, article),
                        stored_article_id=stored_article_id,
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

        classified_by_domain: dict[str, list] = defaultdict(list)
        for pending in pending_evaluations:
            classification = classifications_by_id.get(pending.article_id)
            if classification is None:
                logger.warning(
                    "Skipping article without classification (article_id=%s).",
                    pending.article_id,
                )
                continue

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
            if selection is None or selection.tier == SelectionTier.DISCARD:
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
                enrichment = enrich_article(classified, settings=settings)
            except Exception as exc:
                logger.exception(
                    "Enrichment failed for article_id=%s url=%s error=%s",
                    pending.article_id,
                    pending.article_data.url,
                    exc,
                )
                print(
                    f"    skip (enrichment failed): "
                    f"{pending.article_data.title[:60]} ({type(exc).__name__})"
                )
                continue

            domain_name = (
                pending.feed.technology_domain.name
                if pending.feed.technology_domain is not None
                else ""
            )
            included_articles.append(
                newsletter_article_from_pipeline(
                    title=pending.article_data.title,
                    url=pending.article_data.url,
                    source_name=pending.feed.name,
                    published_at=pending.article_data.published_at,
                    technology_domain_id=pending.feed.technology_domain_id,
                    technology_domain=domain_name,
                    classification=classification,
                    enrichment=enrichment,
                    image_url=pending.article_data.image_url,
                )
            )
            print(
                f"    include: {pending.article_data.title[:70]} "
                f"[type={classification.article_type.value}, "
                f"severity={classification.severity.value}, "
                f"tier={selection.tier.value}, "
                f"domain={domain_name or 'n/a'}]"
            )

    live_count = len(included_articles)
    included_articles = _merge_demo_sections(
        included_articles,
        enabled=args.demo_sections,
    )
    if args.demo_sections and len(included_articles) > live_count:
        print(f"    demo: added {len(included_articles) - live_count} sample section filler(s)")

    render_input = NewsletterRenderInput(
        articles=included_articles,
        config=NewsletterRenderConfig(generated_at=datetime.now().astimezone()),
    )
    html_output = renderer.render(render_input)
    output_path = args.output.resolve()
    output_path.write_text(html_output, encoding="utf-8")

    critical_count = sum(
        1 for article in included_articles if article.severity.value == "Critical"
    )
    print()
    print(f"Included articles : {len(included_articles)}")
    print(f"Critical articles : {critical_count}")
    print(f"Pinned section    : {'yes' if critical_count > 0 else 'no (correctly omitted)'}")
    print(f"Rendered HTML     : {output_path}")


if __name__ == "__main__":
    main()
