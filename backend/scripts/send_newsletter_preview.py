"""
Send rendered newsletter HTML via Microsoft Graph.

Reads newsletter_preview.html (or a custom path) and delivers it using
the same EmailService path as production digests.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.editorial.newsletter.logo_attachment import build_logo_attachments, ensure_logo_cid_reference
from app.infrastructure.logging import configure_logging, get_logger
from app.notifications.email.service import EmailService
from sqlalchemy import text

from app.infrastructure.database.session import SessionLocal

logger = get_logger(__name__)

_TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send newsletter preview HTML as an email via Microsoft Graph.",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=Path("newsletter_preview.html"),
        help="Path to the rendered newsletter HTML file.",
    )
    parser.add_argument(
        "--to",
        action="append",
        dest="recipients",
        help="Recipient email. Repeat for multiple. Falls back to DB enabled recipients.",
    )
    parser.add_argument(
        "--subject",
        help="Email subject. Defaults to the HTML <title> tag.",
    )
    return parser.parse_args()


def _extract_subject(html: str) -> str:
    match = _TITLE_PATTERN.search(html)
    if match is None:
        return "Executive Intelligence Briefing"
    subject = re.sub(r"\s+", " ", match.group(1)).strip()
    return subject or "Executive Intelligence Briefing"


def _resolve_recipients(cli_recipients: list[str] | None) -> list[str]:
    if cli_recipients:
        return cli_recipients

    env_recipient = os.getenv("GRAPH_TEST_RECIPIENT", "").strip()
    if env_recipient:
        return [env_recipient]

    with SessionLocal() as db:
        rows = db.execute(
            text(
                "SELECT email FROM email_recipients "
                "WHERE is_enabled = true ORDER BY created_at DESC"
            )
        ).fetchall()

    recipients = [str(row[0]).strip() for row in rows if str(row[0]).strip()]
    if recipients:
        return recipients

    raise SystemExit(
        "No recipients found. Pass --to, set GRAPH_TEST_RECIPIENT, "
        "or add enabled rows to email_recipients."
    )


def main() -> None:
    args = parse_args()
    configure_logging(level=logging.INFO)

    html_path = args.html.resolve()
    if not html_path.is_file():
        raise SystemExit(f"Newsletter HTML not found: {html_path}")

    html_body = html_path.read_text(encoding="utf-8")
    html_body = ensure_logo_cid_reference(html_body)
    subject = args.subject or _extract_subject(html_body)
    recipients = _resolve_recipients(args.recipients)

    logger.info(
        "Sending newsletter preview (path=%s subject=%r recipients=%s).",
        html_path,
        subject,
        recipients,
    )

    service = EmailService()
    service.send_email(
        subject=subject,
        html_body=html_body,
        recipients=recipients,
        attachments=build_logo_attachments(),
    )

    print(f"Newsletter sent to: {', '.join(recipients)}")
    print(f"Subject: {subject}")
    print(f"Source: {html_path}")


if __name__ == "__main__":
    main()
