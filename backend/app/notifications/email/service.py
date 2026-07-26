import logging

from app.core.settings import Settings, get_settings
from app.notifications.email.exceptions import EmailSendError
from app.notifications.email.graph_client import GraphClient
from app.notifications.email.models import EmailAttachment, EmailMessage, EmailRecipient

logger = logging.getLogger(__name__)


class EmailService:
    """
    Reusable email service backed by Microsoft Graph sendMail.
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

        logger.info("Email send started via Microsoft Graph.")
        response = self.graph_client.send_request("POST", path, json_body=payload)

        # Graph sendMail typically returns 202 Accepted.
        if response.status_code not in (200, 202):
            raise EmailSendError(
                f"Unexpected Graph sendMail status: {response.status_code}"
            )

        logger.info("Email send completed via Microsoft Graph.")
        return True

