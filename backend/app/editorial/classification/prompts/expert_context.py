from app.editorial.classification.models import ClassificationInput
from app.editorial.classification.prompts import (
    PromptMessage,
    build_prompt_messages,
)

EXPERT_CONTEXT_DOMAIN_INSTRUCTIONS = """
Domain focus: Expert Context editorial classification.

Recognize and classify content such as:
- expert commentary and independent technical analysis
- architectural guidance and implementation tradeoffs
- evidence-backed perspectives from trusted practitioners
- interpretation of industry moves through technical context
- synthesis that adds original insight beyond source announcements

When classifying this domain, weigh:
- author credibility signals present in the provided text
- depth of technical analysis versus surface-level reporting
- whether the piece adds independent reasoning or mainly relays another party's announcement
- practical guidance, caveats, and decision-support value for technical readers

Remember:
- classify only
- no summarization
- no publication decision
""".strip()


def build_expert_context_prompt_messages(
    classification_input: ClassificationInput,
) -> list[PromptMessage]:
    return build_prompt_messages(
        classification_input,
        EXPERT_CONTEXT_DOMAIN_INSTRUCTIONS,
    )
