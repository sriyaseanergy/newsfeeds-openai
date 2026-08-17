from datetime import UTC, datetime
from typing import Any

from app.catalog.feed.model import Feed
from app.ingestion.image_url import extract_image_url_from_rss_entry
from app.ingestion.models import NormalizedArticleData


class ArticleMapper:
    def map_entry_to_article_data(
        self, feed: Feed, entry: dict[str, Any]
    ) -> NormalizedArticleData:
        title = str(entry.get("title", "")).strip()
        url = str(entry.get("link", "")).strip()

        if not title:
            raise ValueError("Entry title is missing.")
        if not url:
            raise ValueError("Entry URL is missing.")

        summary = entry.get("summary")
        content_text = self._extract_content(entry)
        author = entry.get("author")
        published_at = self._extract_published_at(entry)
        source_identifier = self._extract_source_identifier(entry)
        image_url = extract_image_url_from_rss_entry(entry, base_url=url)

        return NormalizedArticleData(
            feed_id=feed.id,
            title=title,
            url=url,
            author=str(author).strip() if author else None,
            published_at=published_at,
            summary=str(summary).strip() if summary else None,
            content=content_text,
            source_identifier=source_identifier,
            image_url=image_url,
            is_processed=False,
        )

    @staticmethod
    def _extract_content(entry: dict[str, Any]) -> str | None:
        content = entry.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict):
                value = first.get("value")
                if isinstance(value, str) and value.strip():
                    return value.strip()

        description = entry.get("description")
        if isinstance(description, str) and description.strip():
            return description.strip()

        return None

    @staticmethod
    def _extract_published_at(entry: dict[str, Any]) -> datetime | None:
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed is None:
            return None

        return datetime(
            year=parsed.tm_year,
            month=parsed.tm_mon,
            day=parsed.tm_mday,
            hour=parsed.tm_hour,
            minute=parsed.tm_min,
            second=parsed.tm_sec,
            tzinfo=UTC,
        )

    @staticmethod
    def _extract_source_identifier(entry: dict[str, Any]) -> str | None:
        guid = entry.get("id") or entry.get("guid")
        if isinstance(guid, str):
            value = guid.strip()
            return value or None
        return None
