"""
Scheduled newsletter pipeline: acquire → classify → select → enrich → render → send.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter
from uuid import UUID, uuid4

from app.catalog.article.model import Article
from app.catalog.article.repository import ArticleRepository
from app.catalog.feed.model import Feed
from app.catalog.feed.repository import FeedRepository
from app.catalog.technology_domain.model import TechnologyDomainSchedule
from app.catalog.technology_domain.repository import TechnologyDomainRepository
from app.catalog.user.repository import UserRepository
from app.catalog.user_category_preference.repository import UserCategoryPreferenceRepository
from app.catalog.user_category_preference.service import UserCategoryPreferenceService
from app.core.settings import Settings, get_settings
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
from app.editorial.enrichment import (
    classified_article_from_pipeline,
    enrich_article,
)
from app.editorial.enrichment.models import EnrichedArticle
from app.editorial.newsletter.models import (
    NewsletterArticle,
    NewsletterRenderConfig,
    NewsletterRenderInput,
    newsletter_article_from_pipeline,
)
from app.editorial.newsletter.logo_attachment import build_logo_attachment, ensure_logo_cid_reference
from app.editorial.newsletter.renderer import NewsletterRenderer
from app.editorial.selection import SelectionPolicy, SelectionResult, SelectionTier
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.logging import get_logger
from app.ingestion.acquisition_factory import AcquisitionFactory
from app.ingestion.models import NormalizedArticleData
from app.notifications.email.exceptions import EmailSendError
from app.notifications.email.service import EmailService

logger = get_logger(__name__)

_TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


@dataclass
class DigestRunStats:
    run_id: str
    schedule_name: str
    policy: str
    audience_filter: str
    domain_schedule: str
    feeds_eligible: int = 0
    feeds_processed: int = 0
    feeds_failed: int = 0
    articles_acquired: int = 0
    articles_dedup_skipped: int = 0
    articles_classify_candidates: int = 0
    articles_classified: int = 0
    articles_selected: int = 0
    articles_enriched: int = 0
    articles_in_newsletter: int = 0
    enrichment_failures: int = 0
    classification_failures: int = 0
    users_eligible: int = 0
    users_sent: int = 0
    users_skipped_no_domains: int = 0
    users_skipped_no_content: int = 0
    users_send_failures: int = 0
    recipients: list[str] = field(default_factory=list)
    email_sent: bool = False
    email_subject: str = ""
    skip_reason: str | None = None


@dataclass
class _PendingArticle:
    article_id: str
    feed: Feed
    article_data: NormalizedArticleData
    classification_input: ClassificationInput
    stored_article_id: UUID | None = None


def run_scheduled_digest(
    *,
    schedule_name: str,
    policy: str,
    audience_filter: str,
    domain_schedule: TechnologyDomainSchedule,
    settings: Settings | None = None,
) -> DigestRunStats:
    """
    Execute the full digest pipeline for a scheduler trigger.

    Only articles with tier SELECTED_FOR_ENRICHMENT are enriched and emailed.
    """
    resolved_settings = settings or get_settings()
    run_id = uuid4().hex[:12]
    started = perf_counter()
    stats = DigestRunStats(
        run_id=run_id,
        schedule_name=schedule_name,
        policy=policy,
        audience_filter=audience_filter,
        domain_schedule=domain_schedule.value,
    )

    logger.info(
        "digest.run.start run_id=%s schedule=%s policy=%s audience=%s "
        "domain_schedule=%s max_articles_per_feed=%s sender=%s",
        run_id,
        schedule_name,
        policy,
        audience_filter,
        domain_schedule.value,
        resolved_settings.digest_max_articles_per_feed,
        resolved_settings.graph_sender_email or "(not configured)",
    )

    try:
        newsletter_articles = _build_newsletter_articles(
            stats=stats,
            domain_schedule=domain_schedule,
            settings=resolved_settings,
        )
        stats.articles_in_newsletter = len(newsletter_articles)

        _send_personalized_digests(
            run_id=run_id,
            newsletter_articles=newsletter_articles,
            domain_schedule=domain_schedule,
            stats=stats,
            settings=resolved_settings,
        )
        _log_run_summary(stats, started)
        return stats

    except Exception:
        logger.exception(
            "digest.run.failed run_id=%s schedule=%s duration_s=%.2f",
            run_id,
            schedule_name,
            perf_counter() - started,
        )
        raise


def _build_newsletter_articles(
    *,
    stats: DigestRunStats,
    domain_schedule: TechnologyDomainSchedule,
    settings: Settings,
) -> list[NewsletterArticle]:
    candidate_filter = CandidateFilterService()
    classification_provider = OpenAIClassificationProvider(settings=settings)
    selection_policy = SelectionPolicy()
    acquisition_factory = AcquisitionFactory()
    pending: list[_PendingArticle] = []
    article_seq = 0

    with SessionLocal() as db:
        feed_repository = FeedRepository(db)
        article_repository = ArticleRepository(db)
        feeds = _select_scheduled_feeds(
            feed_repository.list(),
            domain_schedule=domain_schedule,
        )
        stats.feeds_eligible = len(feeds)
        logger.info(
            "digest.feeds.selected run_id=%s count=%s names=%s",
            stats.run_id,
            len(feeds),
            ",".join(feed.name for feed in feeds) or "(none)",
        )

        if not feeds:
            return []

        for feed in feeds:
            stats.feeds_processed += 1
            logger.info(
                "digest.feed.start run_id=%s feed_id=%s feed_name=%s "
                "fetch_kind=%s domain=%s url=%s",
                stats.run_id,
                feed.id,
                feed.name,
                feed.fetch_kind,
                _feed_domain_name(feed),
                feed.url,
            )
            try:
                acquisition = acquisition_factory.for_feed(feed).acquire(feed)
            except Exception:
                stats.feeds_failed += 1
                logger.exception(
                    "digest.feed.acquire_failed run_id=%s feed_id=%s feed_name=%s",
                    stats.run_id,
                    feed.id,
                    feed.name,
                )
                continue

            acquired = acquisition.articles[: settings.digest_max_articles_per_feed]
            stats.articles_acquired += len(acquired)
            logger.info(
                "digest.feed.acquired run_id=%s feed_id=%s feed_name=%s "
                "acquired=%s fetched=%s warnings=%s",
                stats.run_id,
                feed.id,
                feed.name,
                len(acquired),
                acquisition.fetched_count,
                len(acquisition.errors),
            )
            for warning in acquisition.errors[:3]:
                logger.warning(
                    "digest.feed.acquire_warning run_id=%s feed_id=%s warning=%s",
                    stats.run_id,
                    feed.id,
                    warning,
                )

            for article_data in acquired:
                article, stored_article_id = build_candidate_article(
                    feed,
                    article_data,
                    article_repository,
                )
                filter_result = candidate_filter.evaluate(article)
                if filter_result.decision == CandidateDecision.SKIP:
                    stats.articles_dedup_skipped += 1
                    logger.info(
                        "digest.article.dedup_skip run_id=%s feed_id=%s url=%s "
                        "reason=%s title=%s",
                        stats.run_id,
                        feed.id,
                        article_data.url,
                        filter_result.reason,
                        _truncate(article_data.title, 80),
                    )
                    continue

                article_seq += 1
                article_id = f"digest_{stats.run_id}_{article_seq}"
                pending.append(
                    _PendingArticle(
                        article_id=article_id,
                        feed=feed,
                        article_data=article_data,
                        classification_input=_to_classification_input(feed, article),
                        stored_article_id=stored_article_id,
                    )
                )
                logger.info(
                    "digest.article.dedup_pass run_id=%s article_id=%s feed_id=%s url=%s",
                    stats.run_id,
                    article_id,
                    feed.id,
                    article_data.url,
                )

        stats.articles_classify_candidates = len(pending)
        if not pending:
            logger.warning(
                "digest.classify.skip run_id=%s reason=no_candidates_after_dedup",
                stats.run_id,
            )
            return []

        logger.info(
            "digest.classify.start run_id=%s count=%s batch_size=%s",
            stats.run_id,
            len(pending),
            settings.classification_batch_size,
        )
        batch_items = [
            ClassificationBatchItem(
                article_id=item.article_id,
                classification_input=item.classification_input,
            )
            for item in pending
        ]
        classifications_by_id = classification_provider.classify_many(batch_items)
        logger.info(
            "digest.classify.complete run_id=%s returned=%s expected=%s",
            stats.run_id,
            len(classifications_by_id),
            len(pending),
        )

        classified_by_domain: dict[str, list[tuple[str, EditorialClassification]]] = (
            defaultdict(list)
        )
        for item in pending:
            classification = classifications_by_id.get(item.article_id)
            if classification is None:
                stats.classification_failures += 1
                logger.error(
                    "digest.classify.missing run_id=%s article_id=%s feed_id=%s url=%s",
                    stats.run_id,
                    item.article_id,
                    item.feed.id,
                    item.article_data.url,
                )
                continue

            stats.articles_classified += 1
            mark_article_processed(
                article_repository,
                item.feed,
                item.article_data,
                stored_article_id=item.stored_article_id,
            )
            domain_name = _feed_domain_name(item.feed)
            classified_by_domain[domain_name].append((item.article_id, classification))
            logger.info(
                "digest.classify.result run_id=%s article_id=%s type=%s severity=%s "
                "actionability=%s confidence=%.2f domain=%s",
                stats.run_id,
                item.article_id,
                classification.article_type.value,
                classification.severity.value,
                classification.actionability.value,
                classification.confidence,
                domain_name,
            )

        selection_by_id: dict[str, SelectionResult] = {}
        for domain_name, classified in classified_by_domain.items():
            selection_by_id.update(
                selection_policy.select_for_domain(domain_name, classified)
            )

        newsletter_articles: list[NewsletterArticle] = []
        for item in pending:
            selection = selection_by_id.get(item.article_id)
            if selection is None:
                continue

            logger.info(
                "digest.select.result run_id=%s article_id=%s domain=%s tier=%s "
                "group=%s rank=%s score=%s",
                stats.run_id,
                item.article_id,
                _feed_domain_name(item.feed),
                selection.tier.value,
                selection.group_key,
                selection.rank_within_group,
                selection.rank_score,
            )

            if selection.tier != SelectionTier.SELECTED_FOR_ENRICHMENT:
                continue

            stats.articles_selected += 1
            classification = classifications_by_id[item.article_id]
            enrichment = _enrich_selected_article(
                stats=stats,
                item=item,
                classification=classification,
                settings=settings,
            )
            if enrichment is None:
                continue

            newsletter_articles.append(
                newsletter_article_from_pipeline(
                    title=item.article_data.title,
                    url=item.article_data.url,
                    source_name=item.feed.name or "",
                    published_at=item.article_data.published_at,
                    technology_domain_id=item.feed.technology_domain_id,
                    technology_domain=_feed_domain_name(item.feed),
                    classification=classification,
                    enrichment=enrichment,
                    image_url=item.article_data.image_url,
                )
            )

        return newsletter_articles


def _enrich_selected_article(
    *,
    stats: DigestRunStats,
    item: _PendingArticle,
    classification: EditorialClassification,
    settings: Settings,
) -> EnrichedArticle | None:
    logger.info(
        "digest.enrich.start run_id=%s article_id=%s url=%s title=%s",
        stats.run_id,
        item.article_id,
        item.article_data.url,
        _truncate(item.article_data.title, 80),
    )
    try:
        classified = classified_article_from_pipeline(
            source_name=item.feed.name or "",
            url=item.article_data.url,
            published_at=item.article_data.published_at,
            summary=item.article_data.summary,
            content=item.article_data.content,
            classification=classification,
        )
        enrichment = enrich_article(classified, settings=settings)
        stats.articles_enriched += 1
        logger.info(
            "digest.enrich.ok run_id=%s article_id=%s confidence=%.2f tldr=%s",
            stats.run_id,
            item.article_id,
            enrichment.confidence,
            _truncate(enrichment.tldr, 100),
        )
        return enrichment
    except Exception:
        stats.enrichment_failures += 1
        logger.exception(
            "digest.enrich.failed run_id=%s article_id=%s feed_id=%s url=%s",
            stats.run_id,
            item.article_id,
            item.feed.id,
            item.article_data.url,
        )
        return None


def _send_personalized_digests(
    *,
    run_id: str,
    newsletter_articles: list[NewsletterArticle],
    domain_schedule: TechnologyDomainSchedule,
    stats: DigestRunStats,
    settings: Settings,
) -> None:
    with SessionLocal() as db:
        users = UserRepository(db).list_active_with_email()

    stats.users_eligible = len(users)
    logger.info(
        "digest.users.eligible run_id=%s count=%s pool_articles=%s",
        run_id,
        len(users),
        len(newsletter_articles),
    )

    if not users:
        stats.skip_reason = "no_eligible_users"
        logger.warning("digest.run.skip_send run_id=%s reason=%s", run_id, stats.skip_reason)
        return

    if not newsletter_articles:
        stats.skip_reason = "no_articles_selected_for_enrichment"
        logger.warning(
            "digest.run.skip_send run_id=%s reason=%s "
            "(feeds_processed=%s acquired=%s classified=%s selected=%s)",
            run_id,
            stats.skip_reason,
            stats.feeds_processed,
            stats.articles_acquired,
            stats.articles_classified,
            stats.articles_selected,
        )
        return

    for user in users:
        email = (user.email or "").strip()
        if not email:
            logger.warning(
                "digest.user.skip run_id=%s user_id=%s reason=missing_email",
                run_id,
                user.id,
            )
            continue

        with SessionLocal() as db:
            preference_service = UserCategoryPreferenceService(
                UserCategoryPreferenceRepository(db),
                TechnologyDomainRepository(db),
                FeedRepository(db),
            )
            enabled_domain_ids = preference_service.list_effective_enabled_for_schedule(
                user.id,
                domain_schedule,
            )

        if not enabled_domain_ids:
            stats.users_skipped_no_domains += 1
            logger.info(
                "digest.user.skip run_id=%s user_id=%s email=%s reason=no_enabled_domains",
                run_id,
                user.id,
                email,
            )
            continue

        user_articles = [
            article
            for article in newsletter_articles
            if article.technology_domain_id in enabled_domain_ids
        ]
        if not user_articles:
            stats.users_skipped_no_content += 1
            logger.info(
                "digest.user.skip run_id=%s user_id=%s email=%s reason=no_matching_articles",
                run_id,
                user.id,
                email,
            )
            continue

        html_body, subject = _render_newsletter(user_articles)
        html_body = ensure_logo_cid_reference(html_body)
        if not stats.email_subject:
            stats.email_subject = subject

        try:
            _send_digest_email(
                run_id=run_id,
                subject=subject,
                html_body=html_body,
                recipients=[email],
                settings=settings,
            )
        except EmailSendError:
            stats.users_send_failures += 1
            logger.exception(
                "digest.user.send_failed run_id=%s user_id=%s email=%s subject=%r",
                run_id,
                user.id,
                email,
                subject,
            )
            continue

        stats.users_sent += 1
        stats.recipients.append(email)
        logger.info(
            "digest.user.send_ok run_id=%s user_id=%s email=%s articles=%s subject=%r",
            run_id,
            user.id,
            email,
            len(user_articles),
            subject,
        )

    stats.email_sent = stats.users_sent > 0
    if not stats.email_sent and stats.skip_reason is None:
        stats.skip_reason = "no_recipients_or_content"


def _render_newsletter(articles: list[NewsletterArticle]) -> tuple[str, str]:
    renderer = NewsletterRenderer()
    render_input = NewsletterRenderInput(
        articles=articles,
        config=NewsletterRenderConfig(generated_at=datetime.now().astimezone()),
    )
    html_body = renderer.render(render_input)
    subject = _extract_subject(html_body)
    logger.info(
        "digest.render.complete articles=%s html_chars=%s subject=%r",
        len(articles),
        len(html_body),
        subject,
    )
    return html_body, subject


def _send_digest_email(
    *,
    run_id: str,
    subject: str,
    html_body: str,
    recipients: list[str],
    settings: Settings,
) -> None:
    logger.info(
        "digest.email.send_start run_id=%s subject=%r recipients=%s html_chars=%s",
        run_id,
        subject,
        ",".join(recipients),
        len(html_body),
    )
    try:
        EmailService(settings=settings).send_email(
            subject=subject,
            html_body=html_body,
            recipients=recipients,
            attachments=[build_logo_attachment()],
        )
    except EmailSendError:
        logger.exception(
            "digest.email.send_failed run_id=%s subject=%r recipients=%s",
            run_id,
            subject,
            ",".join(recipients),
        )
        raise

    logger.info(
        "digest.email.send_ok run_id=%s subject=%r recipient_count=%s",
        run_id,
        subject,
        len(recipients),
    )


def _select_scheduled_feeds(
    feeds: list[Feed],
    *,
    domain_schedule: TechnologyDomainSchedule,
) -> list[Feed]:
    selected: list[Feed] = []
    for feed in feeds:
        if not feed.is_enabled:
            continue
        domain = feed.technology_domain
        if domain is None or not domain.is_enabled:
            continue
        if domain.schedule != domain_schedule:
            continue
        selected.append(feed)
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


def _feed_domain_name(feed: Feed) -> str:
    domain = feed.technology_domain
    return domain.name if domain is not None else "UNKNOWN"


def _extract_subject(html: str) -> str:
    match = _TITLE_PATTERN.search(html)
    if match is None:
        return "Executive Intelligence Briefing"
    subject = re.sub(r"\s+", " ", match.group(1)).strip()
    return subject or "Executive Intelligence Briefing"


def _truncate(value: str, max_len: int) -> str:
    text = (value or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _log_run_summary(stats: DigestRunStats, started: float) -> None:
    logger.info(
        "digest.run.summary run_id=%s schedule=%s email_sent=%s skip_reason=%s "
        "feeds_eligible=%s feeds_processed=%s feeds_failed=%s "
        "acquired=%s dedup_skipped=%s classify_candidates=%s classified=%s "
        "selected=%s enriched=%s in_newsletter=%s enrichment_failures=%s "
        "classification_failures=%s users_eligible=%s users_sent=%s "
        "users_skipped_no_domains=%s users_skipped_no_content=%s "
        "users_send_failures=%s recipients=%s subject=%r duration_s=%.2f",
        stats.run_id,
        stats.schedule_name,
        stats.email_sent,
        stats.skip_reason or "none",
        stats.feeds_eligible,
        stats.feeds_processed,
        stats.feeds_failed,
        stats.articles_acquired,
        stats.articles_dedup_skipped,
        stats.articles_classify_candidates,
        stats.articles_classified,
        stats.articles_selected,
        stats.articles_enriched,
        stats.articles_in_newsletter,
        stats.enrichment_failures,
        stats.classification_failures,
        stats.users_eligible,
        stats.users_sent,
        stats.users_skipped_no_domains,
        stats.users_skipped_no_content,
        stats.users_send_failures,
        len(stats.recipients),
        stats.email_subject or "(none)",
        perf_counter() - started,
    )
