from __future__ import annotations

from time import perf_counter

from app.catalog.technology_domain.model import TechnologyDomainSchedule
from app.core.settings import get_settings
from app.editorial.newsletter.pipeline import run_scheduled_digest
from app.infrastructure.logging import get_logger
from app.scheduling.models import DigestScheduleName, DigestTriggerRequest

logger = get_logger(__name__)

_SCHEDULE_DOMAIN: dict[DigestScheduleName, TechnologyDomainSchedule] = {
    DigestScheduleName.DAILY_AI_SECURITY: TechnologyDomainSchedule.DAILY,
    DigestScheduleName.WEEKLY_ENGINEERING: TechnologyDomainSchedule.WEEKLY,
}


def generate_and_send_newsletter(
    policy: str,
    audience_filter: str,
    *,
    schedule_name: str,
) -> None:
    """Run the full digest pipeline for a scheduler trigger."""
    started = perf_counter()
    schedule_key = DigestScheduleName(schedule_name)
    domain_schedule = _SCHEDULE_DOMAIN[schedule_key]

    logger.info(
        "digest.trigger.start schedule=%s policy=%s audience=%s domain_schedule=%s",
        schedule_name,
        policy,
        audience_filter,
        domain_schedule.value,
    )

    try:
        stats = run_scheduled_digest(
            schedule_name=schedule_name,
            policy=policy,
            audience_filter=audience_filter,
            domain_schedule=domain_schedule,
            settings=get_settings(),
        )
        logger.info(
            "digest.trigger.complete schedule=%s run_id=%s email_sent=%s "
            "newsletter_articles=%s duration_s=%.2f",
            schedule_name,
            stats.run_id,
            stats.email_sent,
            stats.articles_in_newsletter,
            perf_counter() - started,
        )
    except Exception:
        logger.exception(
            "digest.trigger.failed schedule=%s policy=%s duration_s=%.2f",
            schedule_name,
            policy,
            perf_counter() - started,
        )
        raise


def run_digest_trigger(request: DigestTriggerRequest) -> None:
    generate_and_send_newsletter(
        request.policy,
        request.audience_filter,
        schedule_name=request.schedule_name.value,
    )
