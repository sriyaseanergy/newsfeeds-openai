from __future__ import annotations

from unittest.mock import patch

import pytest
from app.api.auth.admin_emails import is_feed_source_admin, parse_feed_source_admin_emails
from app.api.auth.authorization import can_manage_feed_sources, require_feed_source_manager
from app.api.auth.dependencies import get_current_employee
from app.api.auth.exceptions import InvalidIdTokenError, MissingEmailClaimError
from app.api.auth.models import AuthenticatedUser
from app.api.auth.router import router as auth_router
from app.core.settings import Settings
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

TENANT_ID = "647119b9-2120-453d-ab27-e02884c15a1b"
CLIENT_ID = "6442ff78-2021-4ee3-8dd3-b0b04cae8066"


def _settings(admin_emails: str = "admin@example.com") -> Settings:
    return Settings(
        azure_tenant_id=TENANT_ID,
        azure_auth_client_id=CLIENT_ID,
        feed_source_admin_emails=admin_emails,
    )


def _user(email: str = "admin@example.com", name: str = "Admin User") -> AuthenticatedUser:
    return AuthenticatedUser(email=email, name=name, designation="Employee", emp_no=None)


def _claims(
    *,
    email: str | None = "user@example.com",
    preferred_username: str | None = None,
    upn: str | None = None,
    name: str = "Jane Doe",
    expired: bool = False,
) -> dict[str, object]:
    import time

    now = int(time.time())
    payload: dict[str, object] = {
        "iss": f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
        "aud": CLIENT_ID,
        "exp": now - 3600 if expired else now + 3600,
        "name": name,
    }
    if email is not None:
        payload["email"] = email
    if preferred_username is not None:
        payload["preferred_username"] = preferred_username
    if upn is not None:
        payload["upn"] = upn
    return payload


@pytest.fixture
def auth_client() -> TestClient:
    app = FastAPI()
    app.include_router(auth_router)
    return TestClient(app)


def test_parse_feed_source_admin_emails_normalizes_and_ignores_empty() -> None:
    parsed = parse_feed_source_admin_emails(
        " admin@Example.com , , kiran@seanergy.ai , "
    )
    assert parsed == frozenset({"admin@example.com", "kiran@seanergy.ai"})


def test_is_feed_source_admin_is_case_insensitive() -> None:
    settings = _settings("sriya@Seanergy.ai")
    assert is_feed_source_admin("sriya@seanergy.ai", settings) is True
    assert is_feed_source_admin("other@seanergy.ai", settings) is False


def test_empty_admin_configuration_grants_no_permissions() -> None:
    settings = _settings("")
    assert can_manage_feed_sources(_user("anyone@example.com"), settings) is False


@pytest.mark.parametrize(
    ("raw", "email", "expected"),
    [
        ("admin@example.com", "admin@example.com", True),
        ("admin@example.com", "other@example.com", False),
    ],
)
def test_can_manage_feed_sources_uses_email_allowlist(
    raw: str,
    email: str,
    expected: bool,
) -> None:
    settings = _settings(raw)
    assert can_manage_feed_sources(_user(email), settings) is expected


def _build_protected_client(user: AuthenticatedUser | None) -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    def protected_route(
        authenticated_user: AuthenticatedUser = Depends(require_feed_source_manager),
    ) -> dict[str, str]:
        return {"email": authenticated_user.email}

    if user is not None:
        app.dependency_overrides[get_current_employee] = lambda: user
    return TestClient(app)


def test_require_feed_source_manager_allows_configured_admin() -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        client = _build_protected_client(_user("admin@example.com"))
        response = client.get("/protected")
    assert response.status_code == 200
    assert response.json() == {"email": "admin@example.com"}


def test_require_feed_source_manager_returns_403_for_non_admin() -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        client = _build_protected_client(_user("other@example.com"))
        response = client.get("/protected")
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to manage feed sources.",
    }


def test_create_session_success_with_email_claim(auth_client: TestClient) -> None:
    claims = _claims(email="jane@example.com", name="Jane Doe")
    with patch("app.api.auth.service.get_settings", return_value=_settings("jane@example.com")):
        with patch(
            "app.api.auth.authenticator.AzureAdIdTokenValidator.validate",
            return_value=claims,
        ):
            response = auth_client.post("/auth/session", json={"id_token": "token"})
    assert response.status_code == 200
    body = response.json()
    assert body["employee"]["email"] == "jane@example.com"
    assert body["employee"]["name"] == "Jane Doe"
    assert body["employee"]["designation"] == "Employee"
    assert body["employee"]["emp_no"] is None
    assert body["employee"]["can_manage_feed_sources"] is True


def test_create_session_success_with_preferred_username_fallback(
    auth_client: TestClient,
) -> None:
    claims = _claims(email=None, preferred_username="User@Example.com", name="Fallback User")
    with patch("app.api.auth.service.get_settings", return_value=_settings("")):
        with patch(
            "app.api.auth.authenticator.AzureAdIdTokenValidator.validate",
            return_value=claims,
        ):
            response = auth_client.post("/auth/session", json={"id_token": "token"})
    assert response.status_code == 200
    assert response.json()["employee"]["email"] == "user@example.com"


def test_create_session_success_with_upn_fallback(auth_client: TestClient) -> None:
    claims = _claims(email=None, preferred_username=None, upn="UPN@Example.com", name="UPN User")
    with patch("app.api.auth.service.get_settings", return_value=_settings("")):
        with patch(
            "app.api.auth.authenticator.AzureAdIdTokenValidator.validate",
            return_value=claims,
        ):
            response = auth_client.post("/auth/session", json={"id_token": "token"})
    assert response.status_code == 200
    assert response.json()["employee"]["email"] == "upn@example.com"


def test_create_session_invalid_token_returns_401(auth_client: TestClient) -> None:
    with patch("app.api.auth.service.get_settings", return_value=_settings("")):
        with patch(
            "app.api.auth.authenticator.AzureAdIdTokenValidator.validate",
            side_effect=InvalidIdTokenError("bad token"),
        ):
            response = auth_client.post("/auth/session", json={"id_token": "bad"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Azure AD ID token."


def test_create_session_expired_token_returns_401(auth_client: TestClient) -> None:
    with patch("app.api.auth.service.get_settings", return_value=_settings("")):
        with patch(
            "app.api.auth.authenticator.AzureAdIdTokenValidator.validate",
            side_effect=InvalidIdTokenError("Signature has expired"),
        ):
            response = auth_client.post("/auth/session", json={"id_token": "expired"})
    assert response.status_code == 401


def test_create_session_missing_email_claim_returns_401(auth_client: TestClient) -> None:
    claims = _claims(email=None, preferred_username=None, upn=None)
    with patch("app.api.auth.service.get_settings", return_value=_settings("")):
        with patch(
            "app.api.auth.authenticator.AzureAdIdTokenValidator.validate",
            return_value=claims,
        ):
            response = auth_client.post("/auth/session", json={"id_token": "token"})
    assert response.status_code == 401
    assert "email" in response.json()["detail"].lower()


def test_auth_me_returns_can_manage_flag(auth_client: TestClient) -> None:
    with patch("app.api.auth.router.get_settings", return_value=_settings("me@example.com")):
        auth_client.app.dependency_overrides[get_current_employee] = lambda: _user(
            "me@example.com",
            name="Me User",
        )
        response = auth_client.get("/auth/me", headers={"Authorization": "Bearer token"})
    auth_client.app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["can_manage_feed_sources"] is True


def test_authorization_does_not_query_mywork(auth_client: TestClient) -> None:
    with patch("app.api.auth.service.get_settings", return_value=_settings("")):
        with patch(
            "app.api.auth.authenticator.AzureAdIdTokenValidator.validate",
            return_value=_claims(email="user@example.com"),
        ):
            with patch(
                "app.infrastructure.employee_database.session.open_employee_session",
                side_effect=AssertionError("MyWork must not be queried"),
            ):
                response = auth_client.post("/auth/session", json={"id_token": "token"})
    assert response.status_code == 200
