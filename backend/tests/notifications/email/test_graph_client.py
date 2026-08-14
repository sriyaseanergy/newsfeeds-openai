from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.notifications.email.exceptions import EmailAuthenticationError, EmailSendError
from app.notifications.email.graph_client import GRAPH_API_BASE_URL, GraphClient
from tests.notifications.email.helpers import make_graph_settings
import pytest


def _client(auth: MagicMock | None = None) -> GraphClient:
    token_auth = auth or MagicMock()
    token_auth.acquire_access_token.return_value = "delegated-access-token"
    return GraphClient(settings=make_graph_settings(), auth=token_auth)


def test_graph_client_init_does_not_acquire_token() -> None:
    auth = MagicMock()
    GraphClient(settings=make_graph_settings(), auth=auth)
    auth.acquire_access_token.assert_not_called()


def test_successful_graph_send_uses_delegated_token() -> None:
    auth = MagicMock()
    auth.acquire_access_token.return_value = "delegated-access-token"
    client = _client(auth)
    response = MagicMock(status_code=202, text="")

    with patch(
        "app.notifications.email.graph_client.requests.request",
        return_value=response,
    ) as request:
        result = client.send_request(
            "POST",
            "/users/broadcast@seanergy.ai/sendMail",
            json_body={"message": {"subject": "Hello"}},
        )

    assert result is response
    request.assert_called_once_with(
        method="POST",
        url=f"{GRAPH_API_BASE_URL}/users/broadcast@seanergy.ai/sendMail",
        headers={
            "Authorization": "Bearer delegated-access-token",
            "Content-Type": "application/json",
        },
        json={"message": {"subject": "Hello"}},
        timeout=15,
    )
    auth.acquire_access_token.assert_called_once()


@pytest.mark.parametrize("status_code", [401, 403])
def test_graph_auth_errors_raise_email_authentication_error(status_code: int) -> None:
    client = _client()
    response = MagicMock(status_code=status_code, text="denied")

    with patch(
        "app.notifications.email.graph_client.requests.request",
        return_value=response,
    ):
        with pytest.raises(
            EmailAuthenticationError,
            match=f"status={status_code}",
        ):
            client.send_request("POST", "/users/broadcast@seanergy.ai/sendMail")


def test_graph_429_retries_then_succeeds() -> None:
    client = _client()
    throttled = MagicMock(status_code=429, text="throttled")
    throttled.headers = {"Retry-After": "1"}
    success = MagicMock(status_code=202, text="")

    with (
        patch(
            "app.notifications.email.graph_client.requests.request",
            side_effect=[throttled, success],
        ) as request,
        patch("app.notifications.email.graph_client.time.sleep") as sleep,
    ):
        result = client.send_request("POST", "/users/broadcast@seanergy.ai/sendMail")

    assert result is success
    assert request.call_count == 2
    sleep.assert_called_once_with(1)


def test_graph_429_raises_after_max_retries() -> None:
    client = _client()
    throttled = MagicMock(status_code=429, text="still throttled")
    throttled.headers = {"Retry-After": "2"}

    with (
        patch(
            "app.notifications.email.graph_client.requests.request",
            return_value=throttled,
        ) as request,
        patch("app.notifications.email.graph_client.time.sleep") as sleep,
    ):
        with pytest.raises(EmailSendError, match="throttled after 3 retries"):
            client.send_request(
                "POST",
                "/users/broadcast@seanergy.ai/sendMail",
                max_retries=3,
            )

    assert request.call_count == 4
    assert sleep.call_count == 3
    sleep.assert_called_with(2)


def test_graph_timeout_is_passed_from_settings() -> None:
    auth = MagicMock()
    auth.acquire_access_token.return_value = "delegated-access-token"
    client = GraphClient(
        settings=make_graph_settings(graph_timeout_seconds=7),
        auth=auth,
    )
    response = MagicMock(status_code=202, text="")

    with patch(
        "app.notifications.email.graph_client.requests.request",
        return_value=response,
    ) as request:
        client.send_request("POST", "/users/broadcast@seanergy.ai/sendMail")

    assert request.call_args.kwargs["timeout"] == 7
