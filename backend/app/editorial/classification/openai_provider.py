import logging
from dataclasses import dataclass

from app.ai.openai.client import OpenAIClient
from app.core.errors import ExternalServiceError
from app.core.settings import Settings, get_settings
from app.editorial.classification.models import (
    ClassificationInput,
    EditorialClassification,
)
from app.editorial.classification.prompt_factory import PromptFactory
from app.editorial.classification.provider import ClassificationProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _PromptTechnologyDomain:
    """
    Minimal domain context used only for prompt selection.

    Keeps prompt orchestration independent from ORM instances.
    """

    name: str
    description: str | None = None


class OpenAIClassificationProvider(ClassificationProvider):
    """
    Provider implementation that orchestrates classification via OpenAI.

    Flow:
        ClassificationInput
            ↓
        PromptFactory
            ↓
        OpenAIClient
            ↓
        EditorialClassification
    """

    def __init__(
        self,
        openai_client: OpenAIClient | None = None,
        prompt_factory: PromptFactory | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.openai_client = openai_client or OpenAIClient(settings=self.settings)
        self.prompt_factory = prompt_factory or PromptFactory()

    def classify(
        self,
        classification_input: ClassificationInput,
    ) -> EditorialClassification:
        """Classify an article using the configured OpenAI model."""

        logger.info("OpenAI classification request started.")

        domain_context = _PromptTechnologyDomain(
            name=classification_input.technology_domain,
        )

        messages = self.prompt_factory.build_messages(
            domain_context,
            classification_input,
        )

        try:
            classification = self.openai_client.parse_response(
                model=self.settings.openai_classification_model,
                input=messages,
                text_format=EditorialClassification,
            )

            logger.info("OpenAI classification request completed.")
            return classification

        except ExternalServiceError:
            logger.exception("OpenAI classification request failed.")
            raise
