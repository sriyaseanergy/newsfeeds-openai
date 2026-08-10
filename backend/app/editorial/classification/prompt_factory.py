from collections.abc import Callable

from app.catalog.technology_domain.model import TechnologyDomain
from app.editorial.classification.models import ClassificationInput
from app.editorial.classification.prompts import PromptMessage
from app.editorial.classification.prompts.ai import build_ai_prompt_messages
from app.editorial.classification.prompts.expert_context import (
    build_expert_context_prompt_messages,
)
from app.editorial.classification.prompts.ml import build_ml_prompt_messages
from app.editorial.classification.prompts.security import (
    build_security_prompt_messages,
)
from app.infrastructure.logging import get_logger

PromptBuilder = Callable[[ClassificationInput], list[PromptMessage]]
logger = get_logger(__name__)


class PromptFactory:
    _PROMPT_BUILDERS: dict[str, PromptBuilder] = {
        "AI": build_ai_prompt_messages,
        "SECURITY": build_security_prompt_messages,
        "ML": build_ml_prompt_messages,
        "EXPERT_CONTEXT": build_expert_context_prompt_messages,
    }

    def build_messages(
        self,
        technology_domain: TechnologyDomain,
        classification_input: ClassificationInput,
    ) -> list[PromptMessage]:
        builder = self._select_prompt_builder(technology_domain)
        return builder(classification_input)

    @classmethod
    def _select_prompt_builder(
        cls,
        technology_domain: TechnologyDomain,
    ) -> PromptBuilder:
        domain_name = technology_domain.name.strip().upper()
        builder = cls._PROMPT_BUILDERS.get(domain_name)
        if builder is not None:
            return builder

        logger.warning(
            "No prompt builder found for domain '%s'. Falling back to AI prompt builder.",
            technology_domain.name,
        )
        return cls._PROMPT_BUILDERS["AI"]