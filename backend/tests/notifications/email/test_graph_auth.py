from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.notifications.email.exceptions import EmailAuthenticationError
from app.notifications.email.graph_auth import GRAPH_MAIL_SEND_SCOPE, GraphDelegatedAuth
from tests.notifications.email.helpers import make_graph_settings
import pytest


def _auth(
    tmp_path,
    *,
    msal_app: MagicMock,
    device_flow_app: MagicMock | None = None,
    token_cache: MagicMock | None = None,
    settings=None,
) -> GraphDelegatedAuth:
    cache = token_cache or MagicMock()
    cache.has_state_changed = False
    cache.serialize.return_value = '{"cache": "state"}'
    flow_app = device_flow_app or msal_app
    return GraphDelegatedAuth(
        settings=settings or make_graph_settings(
            graph_token_cache_path=str(tmp_path / "graph_msal_token_cache.bin"),
        ),
        msal_app=msal_app,
        device_flow_app=flow_app,
        token_cache=cache,
    )


def _mock_token_response(access_token: str) -> MagicMock:
    response = MagicMock()
    response.json.return_value = {
        "access_token": access_token,
        "scope": "https://graph.microsoft.com/Mail.Send",
    }
    return response


def test_init_loads_cache_without_authenticating(tmp_path) -> None:
    msal_app = MagicMock()
    _auth(tmp_path, msal_app=msal_app)

    msal_app.get_accounts.assert_not_called()
    msal_app.acquire_token_silent.assert_not_called()
    msal_app.initiate_device_flow.assert_not_called()
    msal_app.acquire_token_by_device_flow.assert_not_called()


def test_missing_graph_tenant_id_raises() -> None:
    settings = make_graph_settings(azure_tenant_id="")
    with pytest.raises(EmailAuthenticationError, match="AZURE_TENANT_ID"):
        GraphDelegatedAuth(settings=settings)


def test_missing_graph_client_id_raises() -> None:
    settings = make_graph_settings(azure_client_id="")
    with pytest.raises(EmailAuthenticationError, match="AZURE_CLIENT_ID"):
        GraphDelegatedAuth(settings=settings)


def test_missing_graph_client_secret_raises() -> None:
    settings = make_graph_settings(azure_client_secret="")
    with pytest.raises(EmailAuthenticationError, match="AZURE_CLIENT_SECRET"):
        GraphDelegatedAuth(settings=settings)


def test_secret_id_guid_raises() -> None:
    settings = make_graph_settings(
        azure_client_secret="1f1060ff-b83f-41d1-8744-f7f699078c50"
    )
    with pytest.raises(EmailAuthenticationError, match="Secret ID"):
        GraphDelegatedAuth(settings=settings)


def test_acquire_token_silently_from_cached_account(tmp_path) -> None:
    msal_app = MagicMock()
    msal_app.get_accounts.return_value = [{"username": "operator@seanergy.ai"}]
    msal_app.acquire_token_silent.return_value = {"access_token": "silent-token"}

    auth = _auth(tmp_path, msal_app=msal_app)
    token = auth.acquire_access_token()

    assert token == "silent-token"
    msal_app.acquire_token_silent.assert_called_once_with(
        scopes=GRAPH_MAIL_SEND_SCOPE,
        account={"username": "operator@seanergy.ai"},
    )
    msal_app.initiate_device_flow.assert_not_called()
    msal_app.acquire_token_by_device_flow.assert_not_called()
    msal_app.acquire_token_interactive.assert_not_called()


def test_device_flow_fallback_when_no_cached_account(tmp_path) -> None:
    silent_app = MagicMock()
    device_app = MagicMock()
    silent_app.get_accounts.return_value = []
    flow = {
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://microsoft.com/devicelogin",
        "device_code": "device-code-123",
        "expires_at": 9999999999,
        "message": "Complete device login",
    }
    device_app.initiate_device_flow.return_value = flow

    auth = _auth(tmp_path, msal_app=silent_app, device_flow_app=device_app)
    with patch(
        "app.notifications.email.graph_auth.requests.post",
        return_value=_mock_token_response("device-token"),
    ) as post:
        token = auth.acquire_access_token()

    assert token == "device-token"
    silent_app.acquire_token_silent.assert_not_called()
    device_app.initiate_device_flow.assert_called_once_with(
        scopes=GRAPH_MAIL_SEND_SCOPE
    )
    post.assert_called_once()
    assert post.call_args.kwargs["data"]["client_secret"] == "graph-client-secret-value"


def test_device_flow_fallback_when_silent_acquisition_fails(tmp_path) -> None:
    silent_app = MagicMock()
    device_app = MagicMock()
    cached_account = {"username": "operator@seanergy.ai"}
    silent_app.get_accounts.return_value = [cached_account]
    silent_app.acquire_token_silent.return_value = {
        "error": "invalid_grant",
        "error_description": "Token expired",
    }
    flow = {
        "user_code": "WXYZ-1234",
        "verification_uri": "https://microsoft.com/devicelogin",
        "device_code": "device-code-456",
        "expires_at": 9999999999,
        "message": "Complete device login",
    }
    device_app.initiate_device_flow.return_value = flow

    auth = _auth(tmp_path, msal_app=silent_app, device_flow_app=device_app)
    with patch(
        "app.notifications.email.graph_auth.requests.post",
        return_value=_mock_token_response("refreshed-device-token"),
    ):
        token = auth.acquire_access_token()

    assert token == "refreshed-device-token"
    silent_app.acquire_token_silent.assert_called_once()


def test_device_flow_failure_raises_authentication_error(tmp_path) -> None:
    silent_app = MagicMock()
    device_app = MagicMock()
    silent_app.get_accounts.return_value = []
    device_app.initiate_device_flow.return_value = {
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://microsoft.com/devicelogin",
        "device_code": "device-code-789",
        "expires_at": 9999999999,
        "message": "Complete device login",
    }
    error_response = MagicMock()
    error_response.json.return_value = {
        "error": "invalid_client",
        "error_description": "Device code expired",
    }

    auth = _auth(tmp_path, msal_app=silent_app, device_flow_app=device_app)
    with patch(
        "app.notifications.email.graph_auth.requests.post",
        return_value=error_response,
    ):
        with pytest.raises(EmailAuthenticationError, match="Device code expired"):
            auth.acquire_access_token()


def test_loads_existing_token_cache_on_init(tmp_path) -> None:
    cache_path = tmp_path / "graph_msal_token_cache.bin"
    cache_path.write_text('{"existing": "cache"}', encoding="utf-8")
    token_cache = MagicMock()
    token_cache.has_state_changed = False
    msal_app = MagicMock()

    GraphDelegatedAuth(
        settings=make_graph_settings(graph_token_cache_path=str(cache_path)),
        msal_app=msal_app,
        device_flow_app=msal_app,
        token_cache=token_cache,
    )

    token_cache.deserialize.assert_called_once_with('{"existing": "cache"}')


def test_saves_token_cache_when_state_changes(tmp_path) -> None:
    cache_path = tmp_path / "config" / "graph_msal_token_cache.bin"
    token_cache = MagicMock()
    token_cache.has_state_changed = True
    token_cache.serialize.return_value = '{"updated": "cache"}'
    msal_app = MagicMock()
    msal_app.get_accounts.return_value = [{"username": "operator@seanergy.ai"}]
    msal_app.acquire_token_silent.return_value = {"access_token": "silent-token"}

    auth = GraphDelegatedAuth(
        settings=make_graph_settings(graph_token_cache_path=str(cache_path)),
        msal_app=msal_app,
        device_flow_app=msal_app,
        token_cache=token_cache,
    )
    auth.acquire_access_token()

    assert cache_path.read_text(encoding="utf-8") == '{"updated": "cache"}'


def test_uses_confidential_client_when_secret_is_present(tmp_path, monkeypatch) -> None:
    public_captured: dict[str, object] = {}
    confidential_captured: dict[str, object] = {}

    class FakePublicClient:
        def __init__(self, **kwargs):
            public_captured.update(kwargs)

        def get_accounts(self):
            return []

    class FakeConfidentialClient:
        def __init__(self, **kwargs):
            confidential_captured.update(kwargs)

        def get_accounts(self):
            return []

    monkeypatch.setattr(
        "app.notifications.email.graph_auth.msal.PublicClientApplication",
        FakePublicClient,
    )
    monkeypatch.setattr(
        "app.notifications.email.graph_auth.msal.ConfidentialClientApplication",
        FakeConfidentialClient,
    )
    monkeypatch.setattr(
        "app.notifications.email.graph_auth.msal.SerializableTokenCache",
        MagicMock,
    )

    GraphDelegatedAuth(
        settings=make_graph_settings(
            azure_client_secret="graph-client-secret",
            graph_token_cache_path=str(tmp_path / "cache.bin"),
        )
    )

    assert public_captured["client_id"] == "graph-public-client-id"
    assert "client_credential" not in public_captured
    assert confidential_captured["client_id"] == "graph-public-client-id"
    assert confidential_captured["client_credential"] == "graph-client-secret"
    assert public_captured["authority"].endswith("/graph-tenant-id")


def test_device_flow_passes_client_secret_during_token_exchange(tmp_path) -> None:
    device_app = MagicMock()
    silent_app = MagicMock()
    token_cache = MagicMock()
    token_cache.has_state_changed = False
    device_app.initiate_device_flow.return_value = {
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://microsoft.com/devicelogin",
        "device_code": "device-code-999",
        "expires_at": 9999999999,
        "message": "Complete device login",
    }
    silent_app.get_accounts.return_value = []

    auth = GraphDelegatedAuth(
        settings=make_graph_settings(
            azure_client_secret="graph-client-secret",
            graph_token_cache_path=str(tmp_path / "cache.bin"),
        ),
        msal_app=silent_app,
        device_flow_app=device_app,
        token_cache=token_cache,
    )
    with patch(
        "app.notifications.email.graph_auth.requests.post",
        return_value=_mock_token_response("device-token"),
    ) as post:
        token = auth.acquire_access_token()

    assert token == "device-token"
    assert post.call_args.kwargs["data"]["client_secret"] == "graph-client-secret"
    token_cache.add.assert_called_once()


def test_ensure_graph_delegated_auth_acquires_token_at_startup(
    tmp_path, monkeypatch
) -> None:
    from app.notifications.email.graph_auth import ensure_graph_delegated_auth

    instance = MagicMock()
    monkeypatch.setattr(
        "app.notifications.email.graph_auth.GraphDelegatedAuth",
        lambda settings: instance,
    )

    ensure_graph_delegated_auth(
        make_graph_settings(graph_token_cache_path=str(tmp_path / "cache.bin"))
    )

    instance.acquire_access_token.assert_called_once_with()


def test_ensure_graph_delegated_auth_skips_when_graph_settings_missing(
    monkeypatch,
) -> None:
    from app.notifications.email.graph_auth import ensure_graph_delegated_auth

    constructed = MagicMock()
    monkeypatch.setattr(
        "app.notifications.email.graph_auth.GraphDelegatedAuth",
        constructed,
    )

    ensure_graph_delegated_auth(
        make_graph_settings(azure_tenant_id="", azure_client_id="")
    )

    constructed.assert_not_called()

