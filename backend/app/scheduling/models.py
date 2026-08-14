from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DigestScheduleName(StrEnum):
    DAILY_AI_SECURITY = "daily_ai_security"
    WEEKLY_ENGINEERING = "weekly_engineering"


@dataclass(frozen=True)
class DigestTriggerRequest:
    schedule_name: DigestScheduleName
    policy: str
    audience_filter: str


DAILY_AI_SECURITY_DIGEST = DigestTriggerRequest(
    schedule_name=DigestScheduleName.DAILY_AI_SECURITY,
    policy="ai_security_daily",
    audience_filter="ai_security",
)

WEEKLY_ENGINEERING_DIGEST = DigestTriggerRequest(
    schedule_name=DigestScheduleName.WEEKLY_ENGINEERING,
    policy="engineering_weekly",
    audience_filter="engineering",
)
