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

import base64
import json
from urllib.parse import urlparse

from app.core.settings import Settings, get_settings
from app.infrastructure.logging import get_logger
from app.notifications.email.exceptions import EmailAuthenticationError
from app.notifications.email.token_store import TokenError, load_tokens

logger = get_logger(__name__)


def graph_login_base_url(settings: Settings | None = None) -> str:
    """Public backend base URL for Graph OAuth routes (includes ROOT_PATH when set)."""
    resolved = settings or get_settings()
    redirect_uri = resolved.redirect_uri.strip()
    if redirect_uri:
        parsed = urlparse(redirect_uri)
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc or "localhost"
        path = parsed.path.rstrip("/")
        if path.endswith("/callback"):
            path = path[: -len("/callback")]
        return f"{scheme}://{netloc}{path}".rstrip("/")

    root = resolved.root_path.rstrip("/")
    return f"http://localhost:8000{root}".rstrip("/")


def graph_login_url(settings: Settings | None = None) -> str:
    return f"{graph_login_base_url(settings)}/login"


def decode_access_token_identity(access_token: str) -> dict[str, str]:
    """Best-effort JWT payload decode for logging (no signature verification)."""
    try:
        payload_segment = access_token.split(".")[1]
        padding = "=" * (-len(payload_segment) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_segment + padding))
    except (IndexError, json.JSONDecodeError, ValueError):
        return {}

    identity = (
        claims.get("preferred_username")
        or claims.get("upn")
        or claims.get("unique_name")
        or claims.get("email")
        or ""
    )
    return {
        "signed_in_as": str(identity),
        "name": str(claims.get("name") or ""),
        "oid": str(claims.get("oid") or ""),
    }


def graph_token_status(settings: Settings | None = None) -> dict[str, str | bool]:
    resolved = settings or get_settings()
    status: dict[str, str | bool] = {
        "authenticated": False,
        "signed_in_as": "",
        "configured_sender": resolved.graph_sender_email or "",
        "login_url": graph_login_url(resolved),
        "redirect_uri": resolved.redirect_uri or "",
    }
    try:
        token_data = load_tokens(resolved)
    except TokenError:
        return status

    status["authenticated"] = True
    identity = decode_access_token_identity(token_data.get("access_token", ""))
    status["signed_in_as"] = identity.get("signed_in_as", "")
    status["token_name"] = identity.get("name", "")
    return status


class GraphDelegatedAuth:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._validate_required_settings()

    def _validate_required_settings(self) -> None:
        required_values = {
            "AZURE_TENANT_ID": self.settings.azure_tenant_id,
            "AZURE_CLIENT_ID": self.settings.azure_client_id,
            "REDIRECT_URI": self.settings.redirect_uri,
        }
        if not self.settings.azure_graph_public_client:
            required_values["AZURE_CLIENT_SECRET"] = self.settings.azure_client_secret
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
        resolved.redirect_uri,
    )
    if not resolved.azure_graph_public_client:
        required = (*required, resolved.azure_client_secret)
    if not all(str(v).strip() for v in required):
        logger.error(
            "Microsoft Graph startup check skipped. Set AZURE_TENANT_ID, "
            "AZURE_CLIENT_ID, REDIRECT_URI, and AZURE_CLIENT_SECRET "
            "(unless AZURE_GRAPH_PUBLIC_CLIENT=true)."
        )
        return

    try:
        GraphDelegatedAuth(resolved).acquire_access_token()
        token_status = graph_token_status(resolved)
        signed_in_as = token_status.get("signed_in_as") or "(unknown)"
        configured_sender = resolved.graph_sender_email or "(not set)"
        logger.info(
            "Microsoft Graph delegated authentication is ready "
            "(signed_in_as=%s configured_sender=%s).",
            signed_in_as,
            configured_sender,
        )
        if (
            signed_in_as != "(unknown)"
            and configured_sender != "(not set)"
            and signed_in_as.lower() != configured_sender.lower()
        ):
            logger.warning(
                "Graph token identity (%s) differs from GRAPH_SENDER_EMAIL (%s). "
                "Send may fail unless that account has Send As permission on the "
                "configured mailbox. Re-sign in at %s as the sender account, or "
                "update GRAPH_SENDER_EMAIL.",
                signed_in_as,
                configured_sender,
                graph_login_url(resolved),
            )
    except EmailAuthenticationError:
        logger.warning(
            "No Microsoft Graph token on file yet. Visit %s once to "
            "sign in as the account that sends from %s. Complete sign-in "
            "without restarting the server. The app will start normally; "
            "sends will fail until sign-in is done.",
            graph_login_url(resolved),
            resolved.graph_sender_email or "GRAPH_SENDER_EMAIL",
        )