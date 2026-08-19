from __future__ import annotations

import pytest
from app.api.auth.exceptions import MissingOidClaimError, MissingTidClaimError
from app.api.auth.token_validator import AzureAdIdTokenValidator
from app.core.settings import Settings

TENANT_ID = "647119b9-2120-453d-ab27-e02884c15a1b"
CLIENT_ID = "6442ff78-2021-4ee3-8dd3-b0b04cae8066"
OBJECT_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def _validator() -> AzureAdIdTokenValidator:
    return AzureAdIdTokenValidator(
        Settings(
            azure_tenant_id=TENANT_ID,
            azure_auth_client_id=CLIENT_ID,
        )
    )


def test_extract_oid_returns_trimmed_object_id() -> None:
    validator = _validator()
    claims = {"oid": f"  {OBJECT_ID}  "}

    assert validator.extract_oid(claims) == OBJECT_ID


def test_extract_oid_raises_when_claim_missing() -> None:
    validator = _validator()

    with pytest.raises(MissingOidClaimError, match="oid"):
        validator.extract_oid({})


@pytest.mark.parametrize("raw_oid", ["", "   ", 123, None])
def test_extract_oid_raises_when_claim_not_usable(raw_oid: object) -> None:
    validator = _validator()

    with pytest.raises(MissingOidClaimError, match="oid"):
        validator.extract_oid({"oid": raw_oid})


def test_extract_tid_returns_trimmed_tenant_id() -> None:
    validator = _validator()
    claims = {"tid": f"  {TENANT_ID}  "}

    assert validator.extract_tid(claims) == TENANT_ID


def test_extract_tid_raises_when_claim_missing() -> None:
    validator = _validator()

    with pytest.raises(MissingTidClaimError, match="tid"):
        validator.extract_tid({})


@pytest.mark.parametrize("raw_tid", ["", "   ", 123, None])
def test_extract_tid_raises_when_claim_not_usable(raw_tid: object) -> None:
    validator = _validator()

    with pytest.raises(MissingTidClaimError, match="tid"):
        validator.extract_tid({"tid": raw_tid})
