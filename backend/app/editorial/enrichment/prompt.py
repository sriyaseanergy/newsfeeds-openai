from app.editorial.classification.models import EditorialClassification
from app.ingestion.models import NormalizedArticleData


def build_enrichment_prompt(
    article: NormalizedArticleData,
    classification: EditorialClassification,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an editorial enrichment assistant. "
                "Return concise enrichment in the requested structured format."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Title: {article.title}\n"
                f"URL: {article.url}\n"
                f"Published At: {article.published_at.isoformat() if article.published_at else 'unknown'}\n"
                f"Summary: {article.summary or ''}\n"
                f"Content: {article.content or ''}\n"
                f"Classification Type: {classification.article_type.value}\n"
                f"Severity: {classification.severity.value}\n"
                f"Actionability: {classification.actionability.value}\n"
                "Provide key points, business impact, and recommended action."
            ),
        },
    ]
