"""Microsoft Graph HTTP client for newsletter sending.

Employee authentication (SPA login) is a separate mechanism:
    SPA -> Azure AD -> ID token -> MyWork employee lookup
    Settings: AZURE_TENANT_ID, AZURE_AUTH_CLIENT_ID

Graph email authentication:
    News Feeds backend -> GraphDelegatedAuth (device-code / cached token)
    -> delegated Mail.Send access token
    -> POST /users/{GRAPH_SENDER_EMAIL}/sendMail
"""

import time
from typing import Any

import requests
from app.core.settings import Settings, get_settings
from app.infrastructure.logging import get_logger
from app.notifications.email.exceptions import (
    EmailAuthenticationError,
    EmailSendError,
)
from app.notifications.email.graph_auth import GraphDelegatedAuth

logger = get_logger(__name__)

GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"


class GraphClient:
    """
    Microsoft Graph API client for newsletter sending.

    Responsibilities:
    - Delegate token acquisition/cache to GraphDelegatedAuth
    - Send authenticated requests to Microsoft Graph
    - Retry transient failures and Graph 429 throttling
    - Surface auth/send failures as domain-specific exceptions
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        auth: GraphDelegatedAuth | None = None,
    ):
        self.settings = settings or get_settings()
        self._auth = auth or GraphDelegatedAuth(self.settings)

    def _get_access_token(self) -> str:
        return self._auth.acquire_access_token()

    def send_request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        max_retries: int = 3,
        default_retry_after: int = 30,
    ) -> requests.Response:
        token = self._get_access_token()
        url = f"{GRAPH_API_BASE_URL}{path}"
        timeout = self.settings.graph_timeout_seconds

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        attempt = 0
        while True:
            attempt += 1
            logger.info(
                "Microsoft Graph request started (method=%s path=%s attempt=%s).",
                method,
                path,
                attempt,
            )

            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_body,
                    timeout=timeout,
                )
            except requests.RequestException as exc:
                logger.exception(
                    "Microsoft Graph request failed before receiving response."
                )
                raise EmailSendError("Failed to send request to Microsoft Graph.") from exc

            if response.status_code == 429:
                retry_after_header = response.headers.get("Retry-After")
                try:
                    retry_after = int(retry_after_header)
                except (TypeError, ValueError):
                    retry_after = default_retry_after

                body_snippet = response.text[:500]
                logger.warning(
                    "Microsoft Graph request throttled (status=429 attempt=%s "
                    "retry_after=%ss body=%s).",
                    attempt,
                    retry_after,
                    body_snippet,
                )

                if attempt > max_retries:
                    raise EmailSendError(
                        f"Graph API request throttled after {max_retries} retries: "
                        f"{body_snippet}"
                    )

                time.sleep(retry_after)
                continue

            if response.status_code in (401, 403):
                logger.warning("Microsoft Graph authentication/authorization failed.")
                raise EmailAuthenticationError(
                    f"Graph authentication failed (status={response.status_code})."
                )

            if response.status_code >= 400:
                logger.warning(
                    "Microsoft Graph request failed (status=%s).", response.status_code
                )
                body_snippet = response.text[:500]
                raise EmailSendError(
                    f"Graph API request failed (status={response.status_code}): {body_snippet}"
                )

            logger.info(
                "Microsoft Graph request completed (status=%s attempt=%s).",
                response.status_code,
                attempt,
            )
            return response
