from typing import Literal, TypedDict

from app.editorial.enrichment.models import ClassifiedArticle

ENRICHMENT_SYSTEM_PROMPT = """
You are an editorial enrichment engine for a technology newsletter distributed to 
three audiences: Executive (CEO/leadership), Technical Leadership (CTO/engineering 
managers), and Engineering (individual contributors).

You will be given:
- One or more articles (if multiple, they are duplicate/related coverage of the 
  same event — synthesize them into a single enriched item and cite all sources)
- Their existing classification: article_type, severity, actionability, audience, 
  technologies, topics

Your job is NOT to re-classify. Build on the classification given. Produce enrichment 
that lets a newsletter template render this article without an editor touching it.

Rules:
- Ground every claim in the article content provided. Do not infer facts, version 
  numbers, or dates that are not stated. If a detail (e.g. CVE ID, affected version) 
  isn't in the source, omit that field rather than guessing.
- Write "why_it_matters" from the reader's seat, not the article's. Not "the company 
  announced X" — say what X means for someone in that audience's role.
- Keep tldr to 1-2 sentences, audience-neutral, no jargon that a non-specialist 
  reader in that field wouldn't know.
- Only populate recommended_action if the article implies something a reader could 
  concretely do (patch, review a config, evaluate a tool). Otherwise return null.
- key_details should be short factual bullets, not prose. Field name : value style 
  where possible (e.g. "Affected versions: 2.1.0–2.3.4").
- If severity is "low" or "informational", keep why_it_matters to one sentence per 
  audience and skip key_details unless something concrete exists.
- If severity is "high" or "critical", be thorough in key_details and 
  recommended_action — this is likely a security alert or major release.
- Output valid JSON matching the schema exactly. No commentary outside the JSON.
""".strip()


class PromptMessage(TypedDict):
    role: Literal["system", "user"]
    content: str


def _format_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return ", ".join(values)


def _article_body(classified_article: ClassifiedArticle) -> str:
    content = (classified_article.content or "").strip()
    if content:
        return content
    return (classified_article.summary or "").strip()


def build_enrichment_user_content(classified_article: ClassifiedArticle) -> str:
    classification = classified_article.classification

    return (
        "CLASSIFICATION:\n"
        f"article_type: {classification.article_type.value}\n"
        f"severity: {classification.severity.value}\n"
        f"actionability: {classification.actionability.value}\n"
        f"audience: {classification.audience.value}\n"
        f"technologies: {_format_list(classification.technologies)}\n"
        f"topics: {_format_list(classification.topics)}\n"
        "\n"
        "ARTICLE:\n"
        f"Source: {classified_article.source_name}\n"
        f"URL: {classified_article.url}\n"
        f"Published: {classified_article.published_date or 'unknown'}\n"
        f"Content: {_article_body(classified_article)}"
    )


def build_enrichment_messages(
    classified_article: ClassifiedArticle,
) -> list[PromptMessage]:
    return [
        {"role": "system", "content": ENRICHMENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_enrichment_user_content(classified_article),
        },
    ]
