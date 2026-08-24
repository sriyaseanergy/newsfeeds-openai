from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.catalog.feed.model import Feed
from app.ingestion.image_url import extract_image_url_from_html
from app.ingestion.models import NormalizedArticleData


class JsonArticleMapper:
    _TITLE_KEYS = ("title", "summary", "name", "headline")
    _URL_KEYS = ("html_url", "link", "web_url", "permalink", "url")
    _SUMMARY_KEYS = ("summary", "description", "subtitle", "excerpt")
    _CONTENT_KEYS = ("description", "content", "body", "content_html", "text")
    _AUTHOR_KEYS = ("author", "publisher", "creator", "vendor")
    _ID_KEYS = ("ghsa_id", "id", "guid", "uuid", "cve_id")
    _DATE_KEYS = (
        "published_at",
        "published",
        "pub_date",
        "updated_at",
        "updated",
        "created_at",
        "created",
    )

    def map_item_to_article_data(
        self,
        feed: Feed,
        item: dict[str, Any],
    ) -> NormalizedArticleData:
        title = self._first_non_empty_str(item, self._TITLE_KEYS)
        url = self._resolve_url(item)
        if not title:
            raise ValueError("JSON item title is missing.")
        if not url:
            raise ValueError("JSON item URL is missing.")

        summary = self._first_non_empty_str(item, self._SUMMARY_KEYS)
        content = self._first_non_empty_str(item, self._CONTENT_KEYS)
        if summary and content and summary == content:
            summary = None
        if summary and len(summary) > 500 and content:
            summary = summary[:497].rstrip() + "..."

        author = self._first_non_empty_str(item, self._AUTHOR_KEYS)
        published_at = self._extract_published_at(item)
        source_identifier = self._first_non_empty_str(item, self._ID_KEYS)
        image_url = self._extract_image_url(item, url, summary, content)

        return NormalizedArticleData(
            feed_id=feed.id,
            title=title,
            url=url,
            author=author,
            published_at=published_at,
            summary=summary,
            content=content,
            source_identifier=source_identifier,
            image_url=image_url,
            is_processed=False,
        )

    def _resolve_url(self, item: dict[str, Any]) -> str | None:
        for key in self._URL_KEYS:
            value = item.get(key)
            if not isinstance(value, str):
                continue
            candidate = value.strip()
            if not candidate:
                continue
            if key == "url" and "api.github.com/advisories/" in candidate:
                html_url = item.get("html_url")
                if isinstance(html_url, str) and html_url.strip():
                    return html_url.strip()
            return candidate
        return None

    @staticmethod
    def _first_non_empty_str(item: dict[str, Any], keys: tuple[str, ...]) -> str | None:
        for key in keys:
            value = item.get(key)
            if isinstance(value, str):
                normalized = value.strip()
                if normalized:
                    return normalized
        return None

    @staticmethod
    def _extract_published_at(item: dict[str, Any]) -> datetime | None:
        for key in JsonArticleMapper._DATE_KEYS:
            value = item.get(key)
            parsed = JsonArticleMapper._parse_datetime(value)
            if parsed is not None:
                return parsed
        return None

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=UTC)
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _extract_image_url(
        item: dict[str, Any],
        article_url: str,
        summary: str | None,
        content: str | None,
    ) -> str | None:
        for key in ("image_url", "image", "thumbnail", "thumbnail_url"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for text in (content, summary):
            if text:
                image_url = extract_image_url_from_html(text, base_url=article_url)
                if image_url:
                    return image_url
        return None
