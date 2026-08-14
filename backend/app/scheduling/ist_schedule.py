from __future__ import annotations

import re
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

_TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")

_WEEKDAY_TO_CRON = {
    "monday": "mon",
    "tuesday": "tue",
    "wednesday": "wed",
    "thursday": "thu",
    "friday": "fri",
    "saturday": "sat",
    "sunday": "sun",
}


def parse_ist_time_of_day(value: str, *, field_name: str) -> tuple[int, int]:
    normalized = value.strip()
    match = _TIME_PATTERN.fullmatch(normalized)
    if match is None:
        msg = f"{field_name} must use HH:MM format (00:00-23:59)."
        raise ValueError(msg)
    return int(match.group(1)), int(match.group(2))


def parse_weekly_digest_day(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in _WEEKDAY_TO_CRON:
        allowed = ", ".join(day.title() for day in _WEEKDAY_TO_CRON)
        msg = f"weekly_digest_day must be one of: {allowed}."
        raise ValueError(msg)
    return _WEEKDAY_TO_CRON[normalized]
