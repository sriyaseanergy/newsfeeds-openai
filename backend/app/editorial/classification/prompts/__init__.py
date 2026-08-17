from typing import Literal, TypedDict

from app.editorial.classification.models import ClassificationInput

CLASSIFICATION_CONTENT_MAX_CHARS = 2200


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


BATCH_SYSTEM_ADDENDUM = """
Batch classification mode:
- You will receive multiple articles in one request.
- Classify each article independently using only that article's supplied text.
- Do not compare articles or transfer evidence across articles.
- Return one classification object for every provided article_id.
- Every returned object must include article_id exactly as provided.
- Do not omit any article_id from the response.
""".strip()


def _truncate_content(content: str | None, max_chars: int = CLASSIFICATION_CONTENT_MAX_CHARS) -> str:
    if not content:
        return ""
    text = content.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[Content truncated for classification]"


def _format_domain_lines(classification_input: ClassificationInput) -> str:
    lines = [f"Technology Domain: {classification_input.technology_domain}"]
    description = (classification_input.technology_domain_description or "").strip()
    if description:
        lines.append(f"Technology Domain Description: {description}")
    return "\n".join(lines)


def format_classification_input(classification_input: ClassificationInput) -> str:
    summary = classification_input.summary or ""
    content = _truncate_content(classification_input.content)

    return (
        f"Title: {classification_input.title}\n"
        f"Source Name: {classification_input.source_name}\n"
        f"{_format_domain_lines(classification_input)}\n\n"
        f"Summary:\n{summary}\n\n"
        f"Content:\n{content}"
    )


def format_batch_classification_input(
    articles: list[tuple[str, ClassificationInput]],
) -> str:
    sections: list[str] = [
        f"Classify the following {len(articles)} articles.",
        "Return one classification for each article_id listed below.",
        "",
    ]
    for article_id, classification_input in articles:
        sections.append(f"=== Article ID: {article_id} ===")
        sections.append(format_classification_input(classification_input))
        sections.append("")
    return "\n".join(sections).strip()


def build_prompt_messages(classification_input: ClassificationInput) -> list[PromptMessage]:
    return [
        {"role": "system", "content": COMMON_SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": format_classification_input(classification_input)},
    ]


def build_batch_prompt_messages(
    articles: list[tuple[str, ClassificationInput]],
) -> list[PromptMessage]:
    system_content = f"{COMMON_SYSTEM_INSTRUCTIONS}\n\n{BATCH_SYSTEM_ADDENDUM}"
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": format_batch_classification_input(articles)},
    ]
