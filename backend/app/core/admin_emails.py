from __future__ import annotations

from app.core.settings import Settings


def parse_feed_source_admin_emails(raw: str) -> frozenset[str]:
    emails: set[str] = set()
    for part in raw.split(","):
        normalized = part.strip().lower()
        if normalized:
            emails.add(normalized)
    return frozenset(emails)


def is_feed_source_admin(email: str, settings: Settings) -> bool:
    normalized_email = email.strip().lower()
    if not normalized_email:
        return False
    return normalized_email in parse_feed_source_admin_emails(
        settings.feed_source_admin_emails
    )
