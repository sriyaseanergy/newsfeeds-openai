import time
from typing import Any

import msal
import requests
from app.core.settings import Settings, get_settings
from app.infrastructure.logging import get_logger
from app.notifications.email.exceptions import (
    EmailAuthenticationError,
    EmailSendError,
)

logger = get_logger(__name__)

GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_DEFAULT_SCOPE = ["https://graph.microsoft.com/.default"]


class GraphClient:
    """
    Microsoft Graph API client with app-only authentication.

    Responsibilities:
    - Acquire and cache OAuth tokens via client credentials flow
    - Send authenticated requests to Microsoft Graph
    - Surface auth/send failures as domain-specific exceptions
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._validate_required_settings()

        authority = f"https://login.microsoftonline.com/{self.settings.azure_tenant_id}"
        self._msal_app = msal.ConfidentialClientApplication(
            client_id=self.settings.azure_client_id,
            client_credential=self.settings.azure_client_secret,
            authority=authority,
        )
        self._access_token: str | None = None
        self._expires_at: int = 0

    def _validate_required_settings(self) -> None:
        required_values = {
            "AZURE_TENANT_ID": self.settings.azure_tenant_id,
            "AZURE_CLIENT_ID": self.settings.azure_client_id,
            "AZURE_CLIENT_SECRET": self.settings.azure_client_secret,
        }

        missing = [name for name, value in required_values.items() if not value]
        if missing:
            raise EmailAuthenticationError(
                f"Missing required Graph auth settings: {', '.join(missing)}"
            )

    def _get_access_token(self) -> str:
        now = int(time.time())
        # Refresh a little before expiration to avoid edge race.
        if self._access_token and now < (self._expires_at - 60):
            logger.info("Reusing cached Microsoft Graph access token.")
            return self._access_token

        logger.info("Acquiring Microsoft Graph access token.")
        token_result = self._msal_app.acquire_token_for_client(
            scopes=GRAPH_DEFAULT_SCOPE
        )
        access_token = token_result.get("access_token")
        if not access_token:
            error_description = token_result.get("error_description", "Unknown error")
            raise EmailAuthenticationError(
                f"Failed to acquire Microsoft Graph token: {error_description}"
            )

        expires_in = int(token_result.get("expires_in", 3600))
        self._access_token = access_token
        self._expires_at = now + expires_in
        logger.info("Microsoft Graph access token acquired (expires_in=%ss).", expires_in)
        return access_token

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