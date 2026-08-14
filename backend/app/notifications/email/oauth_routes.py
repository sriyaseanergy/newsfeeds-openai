"""
One-time browser sign-in for the Microsoft Graph delegated token used to
send newsletters. Visit /oauth/graph/login once, sign in as the account
that sends from GRAPH_SENDER_EMAIL, and token_store.py takes over
refreshing it automatically from then on.
"""

import secrets
from urllib.parse import urlencode

import requests
from app.core.settings import get_settings
from app.notifications.email.token_store import SCOPE, authority, save_tokens, token_url
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["graph-oauth"])

# In-memory CSRF state store -- fine for a single-instance, admin-only flow.
_pending_states: set[str] = set()


@router.get("/login")
def graph_login():
    settings = get_settings()
    state = secrets.token_urlsafe(24)
    _pending_states.add(state)

    params = {
        "client_id": settings.azure_client_id,
        "response_type": "code",
        "redirect_uri": settings.redirect_uri,
        "response_mode": "query",
        "scope": SCOPE,
        "state": state,
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
    if not state or state not in _pending_states:
        raise HTTPException(
            status_code=400, detail="Invalid or expired state parameter."
        )
    _pending_states.discard(state)

    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code returned.")

    data = {
        "client_id": settings.azure_client_id,
        "client_secret": settings.azure_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.redirect_uri,
        "scope": SCOPE,
    }
    response = requests.post(
        token_url(settings), data=data, timeout=settings.graph_timeout_seconds
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Token exchange failed: HTTP {response.status_code} — {response.text[:500]}",
        )

    save_tokens(response.json(), settings)
    return {
        "status": "ok",
        "message": "Microsoft Graph sign-in complete. You can close this tab.",
    }
