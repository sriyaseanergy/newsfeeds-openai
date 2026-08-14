from __future__ import annotations

from unittest.mock import MagicMock

from app.notifications.email.exceptions import EmailSendError
from app.notifications.email.service import EmailService
from tests.notifications.email.helpers import make_graph_settings
import pytest


def test_missing_sender_email_raises() -> None:
    settings = make_graph_settings(graph_sender_email="")
    graph_client = MagicMock()

    with pytest.raises(EmailSendError, match="GRAPH_SENDER_EMAIL"):
        EmailService(graph_client=graph_client, settings=settings)


def test_successful_send_uses_configured_mailbox_not_me() -> None:
    settings = make_graph_settings(graph_sender_email="broadcast@seanergy.ai")
    graph_client = MagicMock()
    graph_client.send_request.return_value = MagicMock(status_code=202)

    service = EmailService(graph_client=graph_client, settings=settings)
    sent = service.send_email(
        subject="Newsletter",
        html_body="<p>Hello</p>",
        recipients=["reader@example.com"],
    )

    assert sent is True
    graph_client.send_request.assert_called_once()
    args, kwargs = graph_client.send_request.call_args
    assert args[0] == "POST"
    assert args[1] == "/users/broadcast@seanergy.ai/sendMail"
    assert "/me/sendMail" not in args[1]
    assert kwargs["json_body"]["saveToSentItems"] == "false"
    assert kwargs["json_body"]["message"]["subject"] == "Newsletter"
