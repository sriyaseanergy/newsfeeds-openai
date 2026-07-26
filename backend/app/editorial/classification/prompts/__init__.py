from typing import Literal, TypedDict

from app.editorial.classification.models import ClassificationInput


class PromptMessage(TypedDict):
    role: Literal["system", "user"]
    content: str


COMMON_SYSTEM_INSTRUCTIONS = """
You are an Editorial Intelligence Analyst.
Your responsibility is ONLY to produce structured editorial metadata.

You are NOT responsible for:
- summarization
- publication decisions
- ranking importance
- comparing articles
- predicting future impact
- generating editorial opinions

Extraction rules:
- Extract companies only when explicitly mentioned.
- Extract products only when explicitly mentioned.
- Extract technologies only when explicitly mentioned.
- Extract topics only when explicitly supported by the supplied text.
- Never infer missing information.
- Never guess vendors or products.
- Never use outside knowledge.
- Use only the supplied input.

When evidence is weak or missing:
- Use empty lists for list fields.
- Choose conservative categorical values.
- Use lower confidence.

Confidence guidance:
- 1.0: explicit support for all major classified fields.
- 0.8: mostly clear evidence, minor ambiguity.
- 0.5: several fields uncertain.
- 0.2: very limited evidence.

Reasoning guidance:
- One short explanation only.
- Objective justification only.
- No summary.
- No editorial opinion.

Return data matching this contract:
- article_type: [News, Advisory, Research, Tutorial, Opinion, Release, Blog, Documentation, Other]
- technologies: list[str]
- companies: list[str]
- products: list[str]
- topics: list[str]
- severity: [None, Low, Medium, High, Critical]
- actionability: [Informational, Monitor, Action Recommended, Immediate Action]
- audience: [Engineering, Security, Leadership, AI, General]
- confidence: float in [0.0, 1.0]
- reasoning: short explanation
""".strip()


def format_classification_input(classification_input: ClassificationInput) -> str:
    summary = classification_input.summary or ""
    content = classification_input.content or ""

    return (
        f"Title: {classification_input.title}\n"
        f"Source Name: {classification_input.source_name}\n"
        f"Technology Domain: {classification_input.technology_domain}\n\n"
        f"Summary:\n{summary}\n\n"
        f"Content:\n{content}"
    )


def build_prompt_messages(
    classification_input: ClassificationInput,
    domain_instructions: str,
) -> list[PromptMessage]:
    system_content = f"{COMMON_SYSTEM_INSTRUCTIONS}\n\n{domain_instructions.strip()}"
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": format_classification_input(classification_input)},
    ]

