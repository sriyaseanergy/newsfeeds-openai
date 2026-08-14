from time import perf_counter

from app.core.settings import Settings, get_settings
from app.infrastructure.logging import get_logger
from app.notifications.email.exceptions import EmailSendError
from app.notifications.email.graph_client import GraphClient
from app.notifications.email.models import EmailAttachment, EmailMessage, EmailRecipient

logger = get_logger(__name__)


class EmailService:
    """
    Reusable email service backed by Microsoft Graph sendMail.

    Sends from GRAPH_SENDER_EMAIL via POST /users/{sender}/sendMail.
    The delegated Graph user must already be allowed to send as that
    mailbox. This does not use /me/sendMail and is not employee SPA login.
    """

    def __init__(
        self,
        graph_client: GraphClient | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.graph_client = graph_client or GraphClient(settings=self.settings)

        if not self.settings.graph_sender_email:
            raise EmailSendError("GRAPH_SENDER_EMAIL is not configured.")

    def send_email(
        self,
        subject: str,
        html_body: str,
        recipients: list[str],
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[EmailAttachment] | None = None,
    ) -> bool:
        if not recipients:
            raise EmailSendError("At least one recipient is required.")

        message = EmailMessage(
            subject=subject,
            html_body=html_body,
            to_recipients=[EmailRecipient(email=email) for email in recipients],
            cc_recipients=[EmailRecipient(email=email) for email in (cc or [])],
            bcc_recipients=[EmailRecipient(email=email) for email in (bcc or [])],
            attachments=attachments or [],
        )

        payload = {
            "message": message.to_graph_payload(),
            "saveToSentItems": "false",
        }

        sender = self.settings.graph_sender_email
        path = f"/users/{sender}/sendMail"

        recipient_count = len(recipients)
        logger.info(
            "Email send started via Microsoft Graph (sender=%s recipient_count=%s).",
            sender,
            recipient_count,
        )
        started_at = perf_counter()
        response = self.graph_client.send_request("POST", path, json_body=payload)
        elapsed_seconds = perf_counter() - started_at

        # Graph sendMail typically returns 202 Accepted.
        if response.status_code not in (200, 202):
            raise EmailSendError(
                f"Unexpected Graph sendMail status: {response.status_code}"
            )

        logger.info(
            "Email send completed via Microsoft Graph (status=%s duration=%.2fs).",
            response.status_code,
            elapsed_seconds,
        )
        return True

