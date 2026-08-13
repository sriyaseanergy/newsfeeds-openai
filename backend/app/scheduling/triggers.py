from __future__ import annotations

from app.infrastructure.logging import get_logger
from app.scheduling.models import DigestTriggerRequest

logger = get_logger(__name__)


def generate_and_send_newsletter(
    policy: str,
    audience_filter: str,
    *,
    schedule_name: str,
) -> None:
    """
    Stub entry point for scheduled newsletter generation and delivery.

    Real implementation will run policy selection and email delivery.
    """
    logger.info(
        "Newsletter trigger fired: schedule=%s policy=%s audience_filter=%s",
        schedule_name,
        policy,
        audience_filter,
    )


def run_digest_trigger(request: DigestTriggerRequest) -> None:
    generate_and_send_newsletter(
        request.policy,
        request.audience_filter,
        schedule_name=request.schedule_name.value,
    )
