from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from app.api.auth.dependencies import get_current_employee
from app.api.auth.models import AuthenticatedUser
from app.catalog.feed.model import FetchKind
from app.catalog.feed.router import get_feed_service, router as feed_router
from app.catalog.feed.schemas import FeedCreate, FeedResponse, FeedUpdate
from app.core.settings import Settings
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

FEED_ID = UUID("11111111-1111-1111-1111-111111111111")
DOMAIN_ID = UUID("22222222-2222-2222-2222-222222222222")
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _settings(admin_emails: str) -> Settings:
    return Settings(
        azure_tenant_id="647119b9-2120-453d-ab27-e02884c15a1b",
        azure_auth_client_id="6442ff78-2021-4ee3-8dd3-b0b04cae8066",
        feed_source_admin_emails=admin_emails,
    )


def _user(email: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        email=email,
        name="Test User",
        designation="Employee",
        emp_no=None,
    )


def _sample_feed_response() -> FeedResponse:
    return FeedResponse(
        id=FEED_ID,
        technology_domain_id=DOMAIN_ID,
        name="Example Feed",
        description=None,
        url="https://example.com/rss",
        is_enabled=True,
        fetch_kind=FetchKind.RSS,
        crawl_depth=1,
        max_new_articles_per_crawl=20,
        created_at=NOW,
        updated_at=NOW,
    )


def _create_payload() -> dict[str, object]:
    return {
        "technology_domain_id": str(DOMAIN_ID),
        "name": "Example Feed",
        "url": "https://example.com/rss",
    }


def _update_payload() -> dict[str, object]:
    return {"name": "Updated Feed"}


@pytest.fixture
def mock_feed_service() -> MagicMock:
    service = MagicMock()
    service.create.return_value = _sample_feed_response()
    service.update.return_value = _sample_feed_response()
    service.delete.return_value = None
    service.list.return_value = [_sample_feed_response()]
    return service


@pytest.fixture
def client(mock_feed_service: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(feed_router)
    app.dependency_overrides[get_feed_service] = lambda: mock_feed_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def _set_user(client: TestClient, user: AuthenticatedUser | None) -> None:
    app = client.app
    if user is None:
        app.dependency_overrides.pop(get_current_employee, None)
        return
    app.dependency_overrides[get_current_employee] = lambda: user


@pytest.mark.parametrize("email", ["admin@example.com", "ADMIN@example.com"])
def test_admin_email_can_create_feed(
    client: TestClient,
    mock_feed_service: MagicMock,
    email: str,
) -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        _set_user(client, _user(email))
        response = client.post("/feeds", json=_create_payload())
    assert response.status_code == 201
    mock_feed_service.create.assert_called_once()


@pytest.mark.parametrize("email", ["admin@example.com"])
def test_admin_email_can_update_feed(
    client: TestClient,
    mock_feed_service: MagicMock,
    email: str,
) -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        _set_user(client, _user(email))
        response = client.put(f"/feeds/{FEED_ID}", json=_update_payload())
    assert response.status_code == 200
    mock_feed_service.update.assert_called_once()


@pytest.mark.parametrize("email", ["admin@example.com"])
def test_admin_email_can_delete_feed(
    client: TestClient,
    mock_feed_service: MagicMock,
    email: str,
) -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        _set_user(client, _user(email))
        response = client.delete(f"/feeds/{FEED_ID}")
    assert response.status_code == 204
    mock_feed_service.delete.assert_called_once()


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_non_admin_authenticated_user_receives_403(
    client: TestClient,
    mock_feed_service: MagicMock,
    method: str,
) -> None:
    with patch("app.api.auth.authorization.get_settings", return_value=_settings("admin@example.com")):
        _set_user(client, _user("other@example.com"))
        if method == "post":
            response = client.post("/feeds", json=_create_payload())
        elif method == "put":
            response = client.put(f"/feeds/{FEED_ID}", json=_update_payload())
        else:
            response = client.delete(f"/feeds/{FEED_ID}")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to manage feed sources.",
    }
    mock_feed_service.create.assert_not_called()
    mock_feed_service.update.assert_not_called()
    mock_feed_service.delete.assert_not_called()


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_unauthenticated_request_receives_401(
    client: TestClient,
    mock_feed_service: MagicMock,
    method: str,
) -> None:
    _set_user(client, None)
    if method == "post":
        response = client.post("/feeds", json=_create_payload())
    elif method == "put":
        response = client.put(f"/feeds/{FEED_ID}", json=_update_payload())
    else:
        response = client.delete(f"/feeds/{FEED_ID}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid authentication."}
    mock_feed_service.create.assert_not_called()
    mock_feed_service.update.assert_not_called()
    mock_feed_service.delete.assert_not_called()


def test_list_feeds_remains_unauthenticated(
    client: TestClient,
    mock_feed_service: MagicMock,
) -> None:
    _set_user(client, None)
    response = client.get("/feeds")
    assert response.status_code == 200
    mock_feed_service.list.assert_called_once()
