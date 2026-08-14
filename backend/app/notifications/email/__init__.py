from app.notifications.email.exceptions import (
    EmailAuthenticationError,
    EmailError,
    EmailSendError,
)
from app.notifications.email.graph_auth import (
    GraphDelegatedAuth,
    ensure_graph_delegated_auth,
)
from app.notifications.email.graph_client import GraphClient
from app.notifications.email.models import EmailAttachment, EmailMessage, EmailRecipient
from app.notifications.email.service import EmailService

__all__ = [
    "EmailAttachment",
    "EmailAuthenticationError",
    "EmailError",
    "EmailMessage",
    "EmailRecipient",
    "EmailSendError",
    "EmailService",
    "GraphClient",
    "GraphDelegatedAuth",
    "ensure_graph_delegated_auth",
]

