"""Manually run a scheduled digest (acquire → enrich → email)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.infrastructure.logging import configure_logging, get_logger
from app.scheduling.models import DAILY_AI_SECURITY_DIGEST, WEEKLY_ENGINEERING_DIGEST
from app.scheduling.triggers import run_digest_trigger

logger = get_logger(__name__)

_SCHEDULES = {
    "daily": DAILY_AI_SECURITY_DIGEST,
    "weekly": WEEKLY_ENGINEERING_DIGEST,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a scheduled newsletter digest immediately.",
    )
    parser.add_argument(
        "schedule",
        choices=sorted(_SCHEDULES),
        help="Which digest schedule to run (daily or weekly).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging()
    request = _SCHEDULES[args.schedule]
    logger.info("Manual digest run requested for schedule=%s.", request.schedule_name.value)
    run_digest_trigger(request)
    print(f"Digest run finished: {request.schedule_name.value}")


if __name__ == "__main__":
    main()
