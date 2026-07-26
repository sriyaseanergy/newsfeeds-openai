import logging
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from app.core.errors import (
    ConfigurationError,
    ExternalServiceAuthenticationError,
    ExternalServiceError,
    ExternalServiceRateLimitError,
    ExternalServiceTimeoutError,
)
from app.core.settings import Settings, get_settings

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

logger = logging.getLogger(__name__)


@lru_cache
def _build_openai_sdk_client(api_key: str, base_url: str | None) -> OpenAI:
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


class OpenAIClient:
    """
    Reusable infrastructure wrapper for OpenAI Responses API access.

    This client exists to centralize SDK initialization, auth/config handling,
    request execution, and exception translation into application-level errors.

    Responsibilities here:
    - Configure and own OpenAI SDK usage
    - Send generic Responses API requests
    - Map SDK failures to application exceptions

    Explicitly NOT responsible for:
    - prompt construction
    - business/domain logic
    - classification/enrichment decisions
    - parsing business models
    """

    def __init__(self, settings: Settings | None = None, client: OpenAI | None = None):
        self.settings = settings or get_settings()

        if not self.settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is not configured.")

        self.classification_model = self.settings.openai_classification_model
        self.enrichment_model = self.settings.openai_enrichment_model
        self.default_model = self.classification_model
        self._client = client or _build_openai_sdk_client(
            self.settings.openai_api_key,
            self.settings.openai_base_url,
        )

    def create_response(
        self,
        *,
        input: str | list[dict[str, Any]],
        model: str | None = None,
        instructions: str | None = None,
        metadata: Mapping[str, str] | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Any:
        resolved_model = model or self.default_model
        request_model = "configured_default" if model is None else "override"
        logger.info(
            "OpenAI response request started (model_source=%s).",
            request_model,
        )

        request_kwargs: dict[str, Any] = {
            "model": resolved_model,
            "input": input,
        }
        if instructions is not None:
            request_kwargs["instructions"] = instructions
        if metadata is not None:
            request_kwargs["metadata"] = dict(metadata)
        if max_output_tokens is not None:
            request_kwargs["max_output_tokens"] = max_output_tokens
        if temperature is not None:
            request_kwargs["temperature"] = temperature

        try:
            response = self._client.responses.create(**request_kwargs)
            logger.info("OpenAI response request completed.")
            return response
        except APITimeoutError as exc:
            logger.warning("OpenAI response request timed out.")
            raise ExternalServiceTimeoutError("OpenAI request timed out.") from exc
        except AuthenticationError as exc:
            logger.warning("OpenAI authentication failed.")
            raise ExternalServiceAuthenticationError(
                "OpenAI authentication failed."
            ) from exc
        except RateLimitError as exc:
            logger.warning("OpenAI rate limit encountered.")
            raise ExternalServiceRateLimitError("OpenAI rate limit exceeded.") from exc
        except APIConnectionError as exc:
            logger.warning("OpenAI connection error encountered.")
            raise ExternalServiceError("OpenAI connection error.") from exc
        except APIError as exc:
            logger.warning("OpenAI API error encountered.")
            raise ExternalServiceError("OpenAI API request failed.") from exc
        except Exception as exc:
            logger.exception("Unexpected OpenAI client failure.")
            raise ExternalServiceError("Unexpected OpenAI client failure.") from exc
