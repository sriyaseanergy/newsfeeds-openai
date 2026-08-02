import asyncio
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

from app.catalog.feed.model import Feed
from app.ingestion.acquisition import FeedAcquirer, FeedAcquisitionResult
from app.ingestion.models import NormalizedArticleData
from crawl4ai import AsyncWebCrawler


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._active_href: str | None = None
        self._active_text_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = {key.lower(): value for key, value in attrs}
        href = attr_map.get("href")
        if isinstance(href, str) and href.strip():
            self._active_href = href.strip()
            self._active_text_chunks = []

    def handle_data(self, data: str) -> None:
        if self._active_href is not None:
            self._active_text_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._active_href is None:
            return
        text = " ".join(chunk.strip() for chunk in self._active_text_chunks).strip()
        self.links.append({"href": self._active_href, "text": text})
        self._active_href = None
        self._active_text_chunks = []


class Crawl4AIFetcher(FeedAcquirer):
    def acquire(self, feed: Feed) -> FeedAcquisitionResult:
        crawl_result = self._crawl(feed.url)
        discovered_links = self._extract_links(feed.url, crawl_result)
        return self._to_normalized_articles(feed, discovered_links)

    def _crawl(self, url: str) -> Any:
        return asyncio.run(self._crawl_async(url))

    async def _crawl_async(self, url: str) -> Any:
        async with AsyncWebCrawler() as crawler:
            return await crawler.arun(url=url)

    def _extract_links(
        self,
        base_url: str,
        crawl_result: Any,
    ) -> list[dict[str, str | datetime | None]]:
        links: list[dict[str, str | datetime | None]] = []

        raw_links = getattr(crawl_result, "links", None)
        if isinstance(raw_links, dict):
            candidate_groups = raw_links.values()
        elif isinstance(raw_links, list):
            candidate_groups = [raw_links]
        else:
            candidate_groups = []

        for group in candidate_groups:
            if not isinstance(group, list):
                continue
            for item in group:
                if not isinstance(item, dict):
                    continue
                href = str(item.get("href") or "").strip()
                if not href:
                    continue
                title = str(item.get("title") or item.get("text") or "").strip()
                summary = str(item.get("description") or item.get("snippet") or "").strip()
                published_at = self._parse_datetime(
                    item.get("published_at") or item.get("published") or item.get("date")
                )
                links.append(
                    {
                        "url": urljoin(base_url, href),
                        "title": title or self._title_from_url(href),
                        "summary": summary or None,
                        "published_at": published_at,
                    }
                )

        if links:
            return self._dedupe_article_links(links)

        html = str(getattr(crawl_result, "html", "") or "")
        if not html:
            return []

        parser = _AnchorParser()
        parser.feed(html)
        for item in parser.links:
            href = item.get("href", "")
            if not href:
                continue
            links.append(
                {
                    "url": urljoin(base_url, href),
                    "title": item.get("text") or self._title_from_url(href),
                    "summary": None,
                    "published_at": None,
                }
            )
        return self._dedupe_article_links(links)

    def _to_normalized_articles(
        self,
        feed: Feed,
        discovered_links: list[dict[str, str | datetime | None]],
    ) -> FeedAcquisitionResult:
        result = FeedAcquisitionResult(fetched_count=len(discovered_links))
        for item in discovered_links:
            url = str(item.get("url") or "").strip()
            if not self._is_article_url(url):
                continue
            title = str(item.get("title") or "").strip() or self._title_from_url(url)
            if not title:
                result.errors.append("Entry skipped: Entry title is missing.")
                continue
            if not url:
                result.errors.append("Entry skipped: Entry URL is missing.")
                continue
            result.articles.append(
                NormalizedArticleData(
                    feed_id=feed.id,
                    title=title,
                    url=url,
                    published_at=item.get("published_at"),
                    summary=item.get("summary"),
                    is_processed=False,
                )
            )
        return result

    @staticmethod
    def _dedupe_article_links(
        links: list[dict[str, str | datetime | None]],
    ) -> list[dict[str, str | datetime | None]]:
        deduped: list[dict[str, str | datetime | None]] = []
        seen: set[str] = set()
        for item in links:
            url = str(item.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            deduped.append(item)
        return deduped

    @staticmethod
    def _is_article_url(url: str) -> bool:
        if not url:
            return False
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        path = parsed.path.lower()
        if not path or path == "/":
            return False
        non_article_tokens = ["/tag/", "/tags/", "/category/", "/categories/", "/author/", "/about", "/contact"]
        if any(token in path for token in non_article_tokens):
            return False
        article_tokens = ["article", "blog", "post", "news", "insight", "story"]
        if any(token in path for token in article_tokens):
            return True
        parts = [part for part in path.split("/") if part]
        if len(parts) >= 3 and all(part.isdigit() for part in parts[:3]):
            return True
        return len(parts) >= 2

    @staticmethod
    def _title_from_url(url: str) -> str:
        parsed = urlparse(url)
        slug = parsed.path.rstrip("/").split("/")[-1] if parsed.path else ""
        if not slug:
            return ""
        return slug.replace("-", " ").replace("_", " ").strip().title()

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value
        as_text = str(value).strip()
        if not as_text:
            return None
        try:
            parsed = datetime.fromisoformat(as_text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed
        except ValueError:
            pass
        try:
            parsed_rfc = parsedate_to_datetime(as_text)
            if parsed_rfc.tzinfo is None:
                return parsed_rfc.replace(tzinfo=UTC)
            return parsed_rfc
        except (TypeError, ValueError):
            return None
