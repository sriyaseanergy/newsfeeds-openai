from app.editorial.classification.models import ClassificationInput
from app.editorial.classification.prompts import (
    PromptMessage,
    build_batch_prompt_messages,
    build_prompt_messages,
)


class PromptFactory:
    def build_messages(
        self,
        classification_input: ClassificationInput,
    ) -> list[PromptMessage]:
        return build_prompt_messages(classification_input)

    def build_batch_messages(
        self,
        articles: list[tuple[str, ClassificationInput]],
    ) -> list[PromptMessage]:
        return build_batch_prompt_messages(articles)
