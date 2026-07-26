from app.editorial.classification.models import ClassificationInput
from app.editorial.classification.prompts import (
    PromptMessage,
    build_prompt_messages,
)


def build_ml_prompt_messages(classification_input: ClassificationInput) -> list[PromptMessage]:
    domain_instructions = """
Domain focus: Machine Learning editorial classification.

Recognize and classify concepts such as:
- new algorithms and model architectures
- datasets, benchmarks, and evaluation methods
- training techniques and optimization strategies
- production ML systems, MLOps, and data pipelines
- deployment patterns and practical research contributions

Remember:
- classify only
- no summarization
- no publication decision
""".strip()

    return build_prompt_messages(classification_input, domain_instructions)

