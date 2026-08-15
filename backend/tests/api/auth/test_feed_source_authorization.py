from __future__ import annotations

from app.api.auth.authorization import (
    can_manage_feed_sources,
    require_feed_source_manager,
)
from app.api.auth.dependencies import get_current_employee
from app.api.auth.models import AuthenticatedUser
from app.core.settings import Settings
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _user(email: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        email=email,
        name="Test User",
        designation="Employee",
        emp_no=None,
    )


def _settings(admin_emails: str) -> Settings:
    return Settings(
        azure_tenant_id="647119b9-2120-453d-ab27-e02884c15a1b",
        azure_auth_client_id="6442ff78-2021-4ee3-8dd3-b0b04cae8066",
        feed_source_admin_emails=admin_emails,
    )


@pytest.mark.parametrize("email", ["admin@example.com", "ADMIN@example.com"])
def test_can_manage_feed_sources_allows_configured_admin_email(email: str) -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        assert can_manage_feed_sources(_user(email)) is True


@pytest.mark.parametrize("email", ["other@example.com"])
def test_can_manage_feed_sources_denies_non_admin_email(email: str) -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        assert can_manage_feed_sources(_user(email if "@" in email else "other@example.com")) is False


def _build_test_client(user: AuthenticatedUser) -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    def protected_route(
        authenticated_user: AuthenticatedUser = Depends(require_feed_source_manager),
    ) -> dict[str, str | None]:
        return {"email": authenticated_user.email, "emp_no": authenticated_user.emp_no}

    app.dependency_overrides[get_current_employee] = lambda: user
    return TestClient(app)


def test_require_feed_source_manager_allows_admin_email() -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        client = _build_test_client(_user("admin@example.com"))
        response = client.get("/protected")
    assert response.status_code == 200
    assert response.json() == {"email": "admin@example.com", "emp_no": None}


def test_require_feed_source_manager_returns_403_for_other_email() -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        client = _build_test_client(_user("other@example.com"))
        response = client.get("/protected")
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to manage feed sources.",
    }
