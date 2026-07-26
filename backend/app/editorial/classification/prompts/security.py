from app.editorial.classification.models import ClassificationInput
from app.editorial.classification.prompts import (
    PromptMessage,
    build_prompt_messages,
)


def build_security_prompt_messages(
    classification_input: ClassificationInput,
) -> list[PromptMessage]:
    domain_instructions = """
Domain focus: Security editorial classification.

Recognize and classify concepts such as:
- vulnerability disclosures and CVEs
- exploit techniques and active attacks
- mitigations, remediations, and patches
- affected products, components, and dependency risks
- threat actors, campaigns, and threat intelligence
- defensive guidance, controls, and security tooling

Remember:
- classify only
- no summarization
- no publication decision
""".strip()

    return build_prompt_messages(classification_input, domain_instructions)

