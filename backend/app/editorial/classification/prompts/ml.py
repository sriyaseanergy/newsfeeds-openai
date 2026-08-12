from app.editorial.classification.models import ClassificationInput
from app.editorial.classification.prompts import (
    PromptMessage,
    build_prompt_messages,
)

ML_DOMAIN_INSTRUCTIONS = """
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


def build_ml_prompt_messages(classification_input: ClassificationInput) -> list[PromptMessage]:
    return build_prompt_messages(classification_input, ML_DOMAIN_INSTRUCTIONS)
