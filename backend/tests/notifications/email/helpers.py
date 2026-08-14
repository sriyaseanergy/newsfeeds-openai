from __future__ import annotations

from app.core.settings import Settings


def make_graph_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "azure_tenant_id": "graph-tenant-id",
        "azure_client_id": "graph-public-client-id",
        "azure_client_secret": "graph-client-secret-value",
        "azure_auth_client_id": "spa-client-id",
        "graph_sender_email": "broadcast@seanergy.ai",
        "graph_timeout_seconds": 15,
        "graph_token_cache_path": "data/config/graph_msal_token_cache.bin",
    }
    values.update(overrides)
    return Settings(**values)
