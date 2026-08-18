"""
One-time browser sign-in for the Microsoft Graph delegated token used to
send newsletters. Visit /login once, sign in as the account that sends
from GRAPH_SENDER_EMAIL, and token_store.py takes over refreshing it
automatically from then on.

When REDIRECT_URI is registered under Azure "Single-page application",
the authorization code must be redeemed from the browser (cross-origin),
not from this server. Set AZURE_GRAPH_PUBLIC_CLIENT=true or the callback
will auto-fallback to browser redemption on AADSTS9002327.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from urllib.parse import urlencode

import requests
from app.core.settings import Settings, get_settings
from app.infrastructure.logging import get_logger
from app.notifications.email.graph_auth import graph_login_url, graph_token_status
from app.notifications.email.token_store import (
    SCOPE,
    authority,
    post_token_request,
    save_tokens,
    token_url,
)
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

router = APIRouter(tags=["graph-oauth"])
logger = get_logger(__name__)

# In-memory CSRF + PKCE store -- fine for a single-instance, admin-only flow.
_pending_auth: dict[str, str] = {}

_SPA_CALLBACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Completing Microsoft Graph sign-in</title>
</head>
<body>
  <p id="status">Completing Microsoft Graph sign-in...</p>
  <script>
    const config = __CONFIG_JSON__;
    async function run() {
      const status = document.getElementById("status");
      try {
        const body = new URLSearchParams({
          client_id: config.client_id,
          grant_type: "authorization_code",
          code: config.code,
          redirect_uri: config.redirect_uri,
          scope: config.scope,
          code_verifier: config.code_verifier,
        });
        const tokenRes = await fetch(config.token_url, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body,
        });
        const tokens = await tokenRes.json();
        if (!tokenRes.ok) {
          status.textContent =
            "Token exchange failed: " + (tokens.error_description || JSON.stringify(tokens));
          return;
        }
        const saveRes = await fetch(config.complete_url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ state: config.state, tokens }),
        });
        const saved = await saveRes.json();
        if (!saveRes.ok) {
          status.textContent =
            "Could not save token: " + (saved.detail || JSON.stringify(saved));
          return;
        }
        status.textContent = saved.message || "Sign-in complete. You can close this tab.";
      } catch (err) {
        status.textContent = "Sign-in failed: " + err;
      }
    }
    run();
  </script>
</body>
</html>
"""


class GraphCallbackCompleteRequest(BaseModel):
    state: str
    tokens: dict


def _generate_pkce_pair() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def _spa_callback_page(
    settings: Settings,
    *,
    state: str,
    code: str,
    code_verifier: str,
    request: Request,
) -> HTMLResponse:
    config = {
        "client_id": settings.azure_client_id,
        "redirect_uri": settings.redirect_uri,
        "scope": SCOPE,
        "code": code,
        "code_verifier": code_verifier,
        "state": state,
        "token_url": token_url(settings),
        "complete_url": str(request.url_for("graph_callback_complete")),
    }
    html = _SPA_CALLBACK_HTML.replace("__CONFIG_JSON__", json.dumps(config))
    return HTMLResponse(content=html)


def _exchange_on_server(
    settings: Settings,
    *,
    code: str,
    code_verifier: str,
) -> requests.Response:
    data = {
        "client_id": settings.azure_client_id,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.redirect_uri,
        "scope": SCOPE,
        "code_verifier": code_verifier,
    }
    return post_token_request(settings, data)


@router.get("/login/status")
def graph_login_status():
    """Check which Microsoft account the cached Graph mail token belongs to."""
    return graph_token_status(get_settings())


@router.get("/login", name="graph_login")
def graph_login(request: Request):
    settings = get_settings()
    if request.query_params.get("force") != "1":
        status = graph_token_status(settings)
        if status.get("authenticated"):
            signed_in_as = status.get("signed_in_as") or "(unknown)"
            configured_sender = status.get("configured_sender") or "(not set)"
            mismatch = (
                signed_in_as != "(unknown)"
                and configured_sender
                and signed_in_as.lower() != configured_sender.lower()
            )
            return HTMLResponse(
                content=(
                    "<p>Microsoft Graph mail token is already on file.</p>"
                    f"<p><strong>Signed in as:</strong> {signed_in_as}</p>"
                    f"<p><strong>Configured sender (GRAPH_SENDER_EMAIL):</strong> "
                    f"{configured_sender}</p>"
                    + (
                        "<p><strong>Warning:</strong> These differ — email send may fail "
                        "with 404 unless Send As permission is granted. Delete the token "
                        "file on the server and sign in again as the sender account.</p>"
                        if mismatch
                        else "<p>To replace the token, delete "
                        "<code>data/config/graph_msal_token_cache.bin</code> on the server "
                        "and open this page again.</p>"
                    )
                    + f'<p><a href="{graph_login_url(settings)}?force=1">Force new sign-in</a></p>'
                )
            )

    return _start_graph_login(settings)


def _start_graph_login(settings: Settings) -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    code_verifier, code_challenge = _generate_pkce_pair()
    _pending_auth[state] = code_verifier

    params = {
        "client_id": settings.azure_client_id,
        "response_type": "code",
        "redirect_uri": settings.redirect_uri,
        "response_mode": "query",
        "scope": SCOPE,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return RedirectResponse(
        f"{authority(settings)}/oauth2/v2.0/authorize?{urlencode(params)}"
    )


@router.get("/callback")
def graph_callback(request: Request):
    settings = get_settings()

    error = request.query_params.get("error")
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Microsoft sign-in failed: {error} — "
            f"{request.query_params.get('error_description', '')}",
        )

    state = request.query_params.get("state")
    code_verifier = _pending_auth.get(state or "") if state else None
    if not state or code_verifier is None:
        return HTMLResponse(
            content=(
                "<p>This sign-in link is no longer valid (expired or already used).</p>"
                "<p>If you saw “Sign-in complete” in another tab, you are done — "
                "close this tab.</p>"
                "<p>Otherwise, start again from "
                f'<a href="{request.url_for("graph_login")}">/login</a>.</p>'
            ),
            status_code=200,
        )

    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code returned.")

    if settings.azure_graph_public_client:
        return _spa_callback_page(
            settings,
            state=state,
            code=code,
            code_verifier=code_verifier,
            request=request,
        )

    try:
        response = _exchange_on_server(
            settings, code=code, code_verifier=code_verifier
        )
    except requests.RequestException as e:
        logger.error("Graph token exchange network error: %s", e)
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {e}") from e

    if response.status_code != 200 and "9002327" in response.text:
        logger.warning(
            "Azure requires browser token redemption for this redirect URI (SPA). "
            "Set AZURE_GRAPH_PUBLIC_CLIENT=true to skip the server attempt."
        )
        return _spa_callback_page(
            settings,
            state=state,
            code=code,
            code_verifier=code_verifier,
            request=request,
        )

    if response.status_code != 200:
        logger.error(
            "Graph token exchange failed: HTTP %s — %s",
            response.status_code,
            response.text[:1000],
        )
        raise HTTPException(
            status_code=502,
            detail=f"Token exchange failed: HTTP {response.status_code} — {response.text[:500]}",
        )

    _pending_auth.pop(state, None)
    save_tokens(response.json(), settings)
    return {
        "status": "ok",
        "message": "Microsoft Graph sign-in complete. You can close this tab.",
    }


@router.post("/callback/complete", name="graph_callback_complete")
def graph_callback_complete(body: GraphCallbackCompleteRequest):
    settings = get_settings()
    if body.state not in _pending_auth:
        raise HTTPException(
            status_code=400, detail="Invalid or expired state parameter."
        )

    if "access_token" not in body.tokens:
        raise HTTPException(
            status_code=400,
            detail="Invalid token response from Microsoft sign-in.",
        )

    _pending_auth.pop(body.state, None)
    save_tokens(body.tokens, settings)
    return {
        "status": "ok",
        "message": "Microsoft Graph sign-in complete. You can close this tab.",
    }
