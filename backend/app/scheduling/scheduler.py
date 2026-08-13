from __future__ import annotations

from datetime import datetime, timedelta

from app.core.settings import Settings, get_settings
from app.infrastructure.logging import get_logger
from app.scheduling.ist_schedule import IST, parse_ist_time_of_day, parse_weekly_digest_day
from app.scheduling.models import DAILY_AI_SECURITY_DIGEST, WEEKLY_ENGINEERING_DIGEST
from app.scheduling.triggers import run_digest_trigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

logger = get_logger(__name__)

SCHEDULER_TIMEZONE = IST


def _daily_trigger(settings: Settings) -> CronTrigger:
    hour, minute = parse_ist_time_of_day(settings.daily_digest_time, field_name="daily_digest_time")
    return CronTrigger(
        hour=hour,
        minute=minute,
        timezone=SCHEDULER_TIMEZONE,
    )


def _weekly_trigger(settings: Settings) -> CronTrigger:
    hour, minute = parse_ist_time_of_day(settings.weekly_digest_time, field_name="weekly_digest_time")
    day_of_week = parse_weekly_digest_day(settings.weekly_digest_day)
    return CronTrigger(
        day_of_week=day_of_week,
        hour=hour,
        minute=minute,
        timezone=SCHEDULER_TIMEZONE,
    )


def register_digest_jobs(scheduler: BackgroundScheduler, settings: Settings | None = None) -> None:
    resolved_settings = settings or get_settings()

    scheduler.add_job(
        run_digest_trigger,
        trigger=_daily_trigger(resolved_settings),
        args=[DAILY_AI_SECURITY_DIGEST],
        id="daily_ai_security_digest",
        replace_existing=True,
        name="Daily AI/Security digest (IST)",
    )
    scheduler.add_job(
        run_digest_trigger,
        trigger=_weekly_trigger(resolved_settings),
        args=[WEEKLY_ENGINEERING_DIGEST],
        id="weekly_engineering_digest",
        replace_existing=True,
        name="Weekly Engineering digest (IST)",
    )


def create_scheduler(settings: Settings | None = None) -> BackgroundScheduler:
    resolved_settings = settings or get_settings()
    scheduler = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE)
    if resolved_settings.scheduler_enabled:
        register_digest_jobs(scheduler, resolved_settings)
    return scheduler


def describe_next_runs(settings: Settings | None = None) -> list[dict[str, str]]:
    resolved_settings = settings or get_settings()
    now = datetime.now(tz=IST)
    schedules = [
        ("daily_ai_security", _daily_trigger(resolved_settings)),
        ("weekly_engineering", _weekly_trigger(resolved_settings)),
    ]
    descriptions: list[dict[str, str]] = []
    for schedule_name, trigger in schedules:
        next_run = trigger.get_next_fire_time(previous_fire_time=None, now=now)
        descriptions.append(
            {
                "schedule": schedule_name,
                "next_run_ist": next_run.isoformat() if next_run else "never",
            }
        )
    return descriptions


def fire_all_triggers_now() -> None:
    logger.info("Manually firing all digest triggers.")
    run_digest_trigger(DAILY_AI_SECURITY_DIGEST)
    run_digest_trigger(WEEKLY_ENGINEERING_DIGEST)


def schedule_immediate_demo(scheduler: BackgroundScheduler, *, delay_seconds: int = 2) -> None:
    run_at = datetime.now(tz=IST).replace(microsecond=0) + timedelta(seconds=delay_seconds)
    scheduler.add_job(
        run_digest_trigger,
        trigger=DateTrigger(run_date=run_at, timezone=SCHEDULER_TIMEZONE),
        args=[DAILY_AI_SECURITY_DIGEST],
        id="demo_daily_ai_security",
        replace_existing=True,
    )
    scheduler.add_job(
        run_digest_trigger,
        trigger=DateTrigger(run_date=run_at, timezone=SCHEDULER_TIMEZONE),
        args=[WEEKLY_ENGINEERING_DIGEST],
        id="demo_weekly_engineering",
        replace_existing=True,
    )
    logger.info("Scheduled demo digest triggers at %s IST.", run_at.isoformat())
