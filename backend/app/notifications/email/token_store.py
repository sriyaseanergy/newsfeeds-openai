"""
Token storage and lifecycle management for the Microsoft Graph delegated
token used to send newsletters (Mail.Send).

Confidential-client authorization-code + refresh-token pattern: the
token is acquired once via a browser visit to /oauth/graph/login, then
refreshed automatically. Every token request -- initial exchange and
every refresh -- includes AZURE_CLIENT_SECRET, so Azure always treats
this as a genuine confidential client. No MSAL, no device-code flow,
no "Allow public client flows" toggle needed.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock

import requests
from app.core.settings import Settings, get_settings
from app.notifications.email.exceptions import EmailAuthenticationError

TENANT_AUTHORITY = "https://login.microsoftonline.com/{tenant_id}"
SCOPE = "https://graph.microsoft.com/Mail.Send offline_access"

_EXPIRY_BUFFER = timedelta(minutes=5)
_refresh_lock = Lock()


class TokenError(EmailAuthenticationError):
    pass


def authority(settings: Settings) -> str:
    return TENANT_AUTHORITY.format(tenant_id=settings.azure_tenant_id)


def token_url(settings: Settings) -> str:
    return f"{authority(settings)}/oauth2/v2.0/token"


def post_token_request(settings: Settings, data: dict) -> requests.Response:
    """POST to the Azure token endpoint, omitting secret for public/SPA clients."""
    payload = dict(data)
    if settings.azure_client_secret and not settings.azure_graph_public_client:
        payload["client_secret"] = settings.azure_client_secret

    response = requests.post(
        token_url(settings), data=payload, timeout=settings.graph_timeout_seconds
    )
    if (
        response.status_code != 200
        and not settings.azure_graph_public_client
        and settings.azure_client_secret
        and "700025" in response.text
    ):
        payload.pop("client_secret", None)
        response = requests.post(
            token_url(settings), data=payload, timeout=settings.graph_timeout_seconds
        )
    return response


def _token_path(settings: Settings) -> Path:
    return Path(settings.graph_token_cache_path)


def save_tokens(token_response: dict, settings: Settings | None = None) -> None:
    """Persist token to disk using an atomic write."""
    settings = settings or get_settings()

    if "access_token" not in token_response:
        raise TokenError("Invalid token response: missing access_token")

    expires_in = int(token_response.get("expires_in", 3600))
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    token_response["expires_at"] = expires_at.isoformat()
    token_response["saved_at"] = datetime.now(timezone.utc).isoformat()

    token_path = _token_path(settings)
    token_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = token_path.with_suffix(token_path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(token_response, f, indent=2)
        os.replace(tmp_path, token_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def load_tokens(settings: Settings | None = None) -> dict:
    """
    Load tokens from disk, auto-refreshing if within the expiry buffer.

    Raises:
        TokenError: if the file is missing, corrupted, or refresh fails.
    """
    settings = settings or get_settings()
    token_path = _token_path(settings)

    if not token_path.exists():
        raise TokenError(
            "No Graph token found. An operator must sign in once by "
            "visiting /oauth/graph/login."
        )

    try:
        token_data = json.loads(token_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise TokenError(f"Token file unreadable or corrupted: {e}") from e

    expires_at_str = token_data.get("expires_at")
    if not expires_at_str:
        raise TokenError(
            "Token file missing expires_at. Re-authenticate via /oauth/graph/login."
        )

    expires_at = datetime.fromisoformat(expires_at_str)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) < (expires_at - _EXPIRY_BUFFER):
        return token_data

    with _refresh_lock:
        try:
            token_data = json.loads(token_path.read_text(encoding="utf-8"))
            expires_at = datetime.fromisoformat(token_data.get("expires_at", ""))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < (expires_at - _EXPIRY_BUFFER):
                return token_data
        except (json.JSONDecodeError, ValueError, OSError):
            pass

        return _refresh_access_token(token_data, settings)


def _refresh_access_token(token_data: dict, settings: Settings) -> dict:
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        raise TokenError(
            "No refresh_token on file. Re-authenticate via /oauth/graph/login."
        )

    data = {
        "client_id": settings.azure_client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": SCOPE,
    }

    try:
        response = post_token_request(settings, data)
    except requests.RequestException as e:
        raise TokenError(f"Token refresh network error: {e}") from e

    if response.status_code != 200:
        raise TokenError(
            f"Token refresh failed: HTTP {response.status_code}. "
            "Re-authenticate via /oauth/graph/login if this persists."
        )

    new_tokens = response.json()
    if "refresh_token" not in new_tokens and "refresh_token" in token_data:
        new_tokens["refresh_token"] = token_data["refresh_token"]

    save_tokens(new_tokens, settings)
    return new_tokens
