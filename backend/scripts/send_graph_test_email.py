from __future__ import annotations

import argparse
import logging
import os

from app.notifications.email.service import EmailService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a Graph API test email.")
    parser.add_argument(
        "--to",
        help="Recipient email address. Falls back to GRAPH_TEST_RECIPIENT env var.",
    )
    parser.add_argument(
        "--subject",
        default="Graph API Test Email",
        help="Email subject for the test message.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    recipient = args.to or os.getenv("GRAPH_TEST_RECIPIENT", "").strip()
    if not recipient:
        raise SystemExit(
            "Missing recipient. Provide --to or set GRAPH_TEST_RECIPIENT."
        )

    service = EmailService()
    html_body = "<p>This is a Microsoft Graph API test email.</p>"
    service.send_email(
        subject=args.subject,
        html_body=html_body,
        recipients=[recipient],
    )

    print("Test email sent successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()

