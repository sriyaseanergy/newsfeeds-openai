"""Validate digest scheduler configuration and stub trigger behavior."""

from __future__ import annotations

import argparse
from datetime import datetime

from app.core.settings import Settings, get_settings
from app.infrastructure.logging import configure_logging, get_logger
from app.scheduling.ist_schedule import IST
from app.scheduling.scheduler import (
    create_scheduler,
    describe_next_runs,
    fire_all_triggers_now,
    schedule_immediate_demo,
)

configure_logging()
logger = get_logger(__name__)


def _print_config(settings: Settings) -> None:
    print("Digest scheduler configuration:")
    print(f"  daily_digest_time   = {settings.daily_digest_time!r} (IST)")
    print(f"  weekly_digest_day   = {settings.weekly_digest_day!r}")
    print(f"  weekly_digest_time  = {settings.weekly_digest_time!r} (IST)")
    print(f"  scheduler_enabled   = {settings.scheduler_enabled}")
    print(f"  server_now_ist      = {datetime.now(tz=IST).isoformat()}")


def _print_next_runs(settings: Settings) -> None:
    print("\nNext scheduled runs (IST):")
    for item in describe_next_runs(settings):
        print(f"  {item['schedule']}: {item['next_run_ist']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Digest scheduler dry-run utility.")
    parser.add_argument(
        "--fire-now",
        action="store_true",
        help="Immediately run both digest pipelines (acquire → enrich → email).",
    )
    parser.add_argument(
        "--demo-in-seconds",
        type=int,
        default=0,
        help="Schedule both triggers to fire after N seconds via APScheduler.",
    )
    args = parser.parse_args()
    settings = get_settings()

    _print_config(settings)
    _print_next_runs(settings)

    if args.fire_now:
        print("\nFiring both digest triggers now...")
        fire_all_triggers_now()

    if args.demo_in_seconds > 0:
        import time

        print(f"\nScheduling demo triggers in {args.demo_in_seconds} seconds...")
        scheduler = create_scheduler(settings)
        scheduler.start()
        schedule_immediate_demo(scheduler, delay_seconds=args.demo_in_seconds)
        time.sleep(args.demo_in_seconds + 3)
        scheduler.shutdown(wait=False)

    if not args.fire_now and args.demo_in_seconds <= 0:
        print(
            "\nUse --fire-now to run both digest pipelines immediately, "
            "or python scripts/run_digest_now.py daily for a single schedule."
        )


if __name__ == "__main__":
    main()
