from app.editorial.classification.models import ClassificationInput
from app.editorial.classification.prompts import (
    PromptMessage,
    build_prompt_messages,
)


def build_ai_prompt_messages(classification_input: ClassificationInput) -> list[PromptMessage]:
    domain_instructions = """
Domain focus: AI and Machine Learning editorial classification.

Recognize and classify concepts such as:
- model announcements and releases
- research breakthroughs and evaluations
- API releases and developer tooling
- agent frameworks and prompt-engineering patterns
- inference infrastructure and deployment patterns
- benchmarking and performance claims

Remember:
- classify only
- no summarization
- no publication decision
""".strip()

    return build_prompt_messages(classification_input, domain_instructions)

