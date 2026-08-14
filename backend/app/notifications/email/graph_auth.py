"""
Delegated Microsoft Graph authentication for newsletter sending.

Confidential-client authorization-code flow. Every token request --
the initial exchange (oauth_routes.py) and every refresh
(token_store.py) -- includes AZURE_CLIENT_SECRET, so no "Allow public
client flows" toggle is needed. The Azure app registration just needs
a "Web" platform with AZURE_REDIRECT_URI registered.

Startup does not attempt login itself -- there's no way to open a
browser from a server process. If no token is on file, sends will fail
with EmailAuthenticationError until an operator visits /login once.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.core.settings import Settings, get_settings
from app.infrastructure.logging import get_logger
from app.notifications.email.exceptions import EmailAuthenticationError
from app.notifications.email.token_store import TokenError, load_tokens

logger = get_logger(__name__)


def graph_login_base_url(settings: Settings | None = None) -> str:
    """Public app base URL derived from REDIRECT_URI (host + port)."""
    resolved = settings or get_settings()
    redirect_uri = resolved.redirect_uri.strip()
    if redirect_uri:
        parsed = urlparse(redirect_uri)
        scheme = parsed.scheme or "http"
        host = parsed.hostname or "localhost"
        if parsed.port:
            return f"{scheme}://{host}:{parsed.port}"
        return f"{scheme}://{host}"
    return "http://localhost:8000"


class GraphDelegatedAuth:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._validate_required_settings()

    def _validate_required_settings(self) -> None:
        required_values = {
            "AZURE_TENANT_ID": self.settings.azure_tenant_id,
            "AZURE_CLIENT_ID": self.settings.azure_client_id,
            "AZURE_CLIENT_SECRET": self.settings.azure_client_secret,
            "REDIRECT_URI": self.settings.redirect_uri,
        }
        missing = [name for name, value in required_values.items() if not value]
        if missing:
            raise EmailAuthenticationError(
                f"Missing required Graph auth settings: {', '.join(missing)}"
            )

    def acquire_access_token(self) -> str:
        try:
            token_data = load_tokens(self.settings)
        except TokenError as e:
            raise EmailAuthenticationError(str(e)) from e
        return token_data["access_token"]


def ensure_graph_delegated_auth(settings: Settings | None = None) -> None:
    """Check readiness at startup without blocking it -- see module docstring."""
    resolved = settings or get_settings()
    required = (
        resolved.azure_tenant_id,
        resolved.azure_client_id,
        resolved.azure_client_secret,
        resolved.redirect_uri,
    )
    if not all(str(v).strip() for v in required):
        logger.error(
            "Microsoft Graph startup check skipped. Set AZURE_TENANT_ID, "
            "AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_REDIRECT_URI."
        )
        return

    try:
        GraphDelegatedAuth(resolved).acquire_access_token()
        logger.info("Microsoft Graph delegated authentication is ready.")
    except EmailAuthenticationError:
        logger.warning(
            "No Microsoft Graph token on file yet. Visit %s/login once to "
            "sign in as the account that sends from %s. Complete sign-in "
            "without restarting the server. The app will start normally; "
            "sends will fail until sign-in is done.",
            graph_login_base_url(resolved),
            resolved.graph_sender_email or "GRAPH_SENDER_EMAIL",
        )