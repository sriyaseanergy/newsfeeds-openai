from collections.abc import Callable

from app.catalog.technology_domain.model import TechnologyDomain
from app.editorial.classification.models import ClassificationInput
from app.editorial.classification.prompts import (
    PromptMessage,
    build_batch_prompt_messages,
)
from app.editorial.classification.prompts.ai import (
    AI_DOMAIN_INSTRUCTIONS,
    build_ai_prompt_messages,
)
from app.editorial.classification.prompts.expert_context import (
    EXPERT_CONTEXT_DOMAIN_INSTRUCTIONS,
    build_expert_context_prompt_messages,
)
from app.editorial.classification.prompts.ml import (
    ML_DOMAIN_INSTRUCTIONS,
    build_ml_prompt_messages,
)
from app.editorial.classification.prompts.security import (
    SECURITY_DOMAIN_INSTRUCTIONS,
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
    _DOMAIN_INSTRUCTIONS: dict[str, str] = {
        "AI": AI_DOMAIN_INSTRUCTIONS,
        "SECURITY": SECURITY_DOMAIN_INSTRUCTIONS,
        "ML": ML_DOMAIN_INSTRUCTIONS,
        "EXPERT_CONTEXT": EXPERT_CONTEXT_DOMAIN_INSTRUCTIONS,
    }

    def build_messages(
        self,
        technology_domain: TechnologyDomain,
        classification_input: ClassificationInput,
    ) -> list[PromptMessage]:
        builder = self._select_prompt_builder(technology_domain)
        return builder(classification_input)

    def build_batch_messages(
        self,
        technology_domain: TechnologyDomain,
        articles: list[tuple[str, ClassificationInput]],
    ) -> list[PromptMessage]:
        domain_instructions = self._select_domain_instructions(technology_domain)
        return build_batch_prompt_messages(articles, domain_instructions)

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

    @classmethod
    def _select_domain_instructions(
        cls,
        technology_domain: TechnologyDomain,
    ) -> str:
        domain_name = technology_domain.name.strip().upper()
        instructions = cls._DOMAIN_INSTRUCTIONS.get(domain_name)
        if instructions is not None:
            return instructions

        logger.warning(
            "No domain instructions found for domain '%s'. Falling back to AI instructions.",
            technology_domain.name,
        )
        return cls._DOMAIN_INSTRUCTIONS["AI"]
