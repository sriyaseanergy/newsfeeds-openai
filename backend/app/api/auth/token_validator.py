from __future__ import annotations

import jwt
from app.api.auth.exceptions import (
    InvalidIdTokenError,
    MissingEmailClaimError,
    MissingOidClaimError,
    MissingTidClaimError,
)
from app.core.settings import Settings
from app.infrastructure.logging import get_logger
from jwt import PyJWKClient

logger = get_logger(__name__)


class AzureAdIdTokenValidator:
    _EMAIL_CLAIMS = ("email", "preferred_username", "upn")

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._tenant_id = settings.azure_tenant_id.strip()
        self._client_id = settings.azure_auth_client_id.strip()
        if not self._tenant_id:
            msg = "AZURE_TENANT_ID is not configured."
            raise ValueError(msg)
        if not self._client_id:
            msg = "AZURE_AUTH_CLIENT_ID is not configured."
            raise ValueError(msg)

        jwks_url = (
            f"https://login.microsoftonline.com/{self._tenant_id}"
            "/discovery/v2.0/keys"
        )
        self._jwks_client = PyJWKClient(jwks_url)

    @property
    def _issuers(self) -> tuple[str, ...]:
        return (
            f"https://login.microsoftonline.com/{self._tenant_id}/v2.0",
            f"https://sts.windows.net/{self._tenant_id}/",
        )

    def validate(self, id_token: str) -> dict[str, object]:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(id_token)
            return jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=self._issuers,
                options={"require": ["exp", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            try:
                unverified = jwt.decode(
                    id_token,
                    options={"verify_signature": False},
                )
                logger.warning(
                    "Azure AD ID token validation failed (%s). "
                    "token aud=%r iss=%r expected_aud=%r expected_iss=%s",
                    exc,
                    unverified.get("aud"),
                    unverified.get("iss"),
                    self._client_id,
                    self._issuers,
                )
            except jwt.PyJWTError:
                logger.warning("Azure AD ID token validation failed (%s).", exc)
            raise InvalidIdTokenError(str(exc)) from exc

    def extract_email(self, claims: dict[str, object]) -> str:
        for claim_name in self._EMAIL_CLAIMS:
            raw_value = claims.get(claim_name)
            if not isinstance(raw_value, str):
                continue
            email = raw_value.strip()
            if email:
                return email.lower()
        raise MissingEmailClaimError(
            "ID token does not contain email, preferred_username, or upn."
        )

    def extract_name(self, claims: dict[str, object], email: str) -> str:
        raw_name = claims.get("name")
        if isinstance(raw_name, str):
            name = raw_name.strip()
            if name:
                return name

        given_name = claims.get("given_name")
        family_name = claims.get("family_name")
        if isinstance(given_name, str) and given_name.strip():
            given = given_name.strip()
            if isinstance(family_name, str) and family_name.strip():
                return f"{given} {family_name.strip()}"
            return given

        local_part = email.split("@", 1)[0].strip()
        if local_part:
            return local_part
        return email

    def extract_oid(self, claims: dict[str, object]) -> str:
        raw_value = claims.get("oid")
        if isinstance(raw_value, str):
            oid = raw_value.strip()
            if oid:
                return oid
        raise MissingOidClaimError("ID token does not contain oid.")

    def extract_tid(self, claims: dict[str, object]) -> str:
        raw_value = claims.get("tid")
        if isinstance(raw_value, str):
            tid = raw_value.strip()
            if tid:
                return tid
        raise MissingTidClaimError("ID token does not contain tid.")
