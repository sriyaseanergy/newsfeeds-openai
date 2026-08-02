import asyncio
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from app.catalog.feed.model import Feed
from app.ingestion.acquisition import FeedAcquirer, FeedAcquisitionResult
from app.ingestion.models import NormalizedArticleData
from crawl4ai import AsyncWebCrawler
from pydantic import BaseModel, ConfigDict, Field


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[dict[str, str | None]] = []
        self._active_href: str | None = None
        self._active_text_chunks: list[str] = []
        self._active_attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = {key.lower(): value for key, value in attrs}
        href = attr_map.get("href")
        if isinstance(href, str) and href.strip():
            self._active_href = href.strip()
            self._active_text_chunks = []
            self._active_attrs = {
                "rel": str(attr_map.get("rel") or "").strip(),
                "class_name": str(attr_map.get("class") or "").strip(),
                "aria_label": str(attr_map.get("aria-label") or "").strip(),
                "title": str(attr_map.get("title") or "").strip(),
            }

    def handle_data(self, data: str) -> None:
        if self._active_href is not None:
            self._active_text_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._active_href is None:
            return
        text = " ".join(chunk.strip() for chunk in self._active_text_chunks).strip()
        self.links.append(
            {
                "href": self._active_href,
                "text": text,
                "rel": self._active_attrs.get("rel"),
                "class_name": self._active_attrs.get("class_name"),
                "aria_label": self._active_attrs.get("aria_label"),
                "title": self._active_attrs.get("title"),
            }
        )
        self._active_href = None
        self._active_text_chunks = []
        self._active_attrs = {}


class CrawlFetchConfig(BaseModel):
    """
    Crawl controls for acquisition. Keep this object as the extension point
    for future crawl options (timeouts, domain allowlists, etc.).
    """

    model_config = ConfigDict(extra="forbid")

    depth: int = Field(default=1, ge=1)

    @classmethod
    def from_feed(cls, feed: Feed) -> "CrawlFetchConfig":
        return cls(depth=feed.crawl_depth or 1)


class Crawl4AIFetcher(FeedAcquirer):
    # Path segments that are never articles, even when same-host and
    # 2+ segments deep. Extend this list as new false positives show up.
    _NON_ARTICLE_PATH_TOKENS = [
        "/tag/",
        "/tags/",
        "/category/",
        "/categories/",
        "/author/",
        "/about",
        "/contact",
        "/careers",
        "/pricing",
        "/privacy",
        "/terms",
        "/login",
        "/signup",
        "/docs/",
    ]

    _ARTICLE_PATH_TOKENS = ["article", "blog", "post", "news", "insight", "story"]

    _PAGINATION_QUERY_KEYS = {"page", "paged", "p", "offset", "start", "cursor"}

    def acquire(self, feed: Feed) -> FeedAcquisitionResult:
        config = CrawlFetchConfig.from_feed(feed)
        seed_host = urlparse(feed.url).netloc.lower()
        discovered_links = self._discover_links(feed.url, config)
        return self._to_normalized_articles(feed, discovered_links, seed_host)

    def _discover_links(
        self,
        seed_url: str,
        config: CrawlFetchConfig,
    ) -> list[dict[str, str | datetime | None]]:
        discovered_links: list[dict[str, str | datetime | None]] = []
        frontier: list[str] = [seed_url]
        visited_listing_pages: set[str] = set()

        for _ in range(config.depth):
            if not frontier:
                break

            next_frontier: list[str] = []
            for page_url in frontier:
                normalized_page_url = str(page_url).strip()
                if (
                    not normalized_page_url
                    or normalized_page_url in visited_listing_pages
                ):
                    continue

                visited_listing_pages.add(normalized_page_url)
                crawl_result = self._crawl(normalized_page_url)
                page_links = self._extract_links(normalized_page_url, crawl_result)
                discovered_links.extend(page_links)

                pagination_urls = self._extract_pagination_urls(
                    seed_url=seed_url,
                    current_page_url=normalized_page_url,
                    crawl_result=crawl_result,
                )
                for candidate_url in pagination_urls:
                    if candidate_url in visited_listing_pages:
                        continue
                    next_frontier.append(candidate_url)

            frontier = self._dedupe_urls(next_frontier)

        return self._dedupe_article_links(discovered_links)

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
        candidates = self._extract_link_candidates(base_url, crawl_result)

        for item in candidates:
            url = str(item.get("url") or "").strip()
            if not url:
                continue
            title = str(item.get("title") or item.get("text") or "").strip()
            summary = str(item.get("description") or item.get("snippet") or "").strip()
            published_at = self._parse_datetime(
                item.get("published_at") or item.get("published") or item.get("date")
            )
            links.append(
                {
                    "url": url,
                    "title": title or self._title_from_url(url),
                    "summary": summary or None,
                    "published_at": published_at,
                }
            )
        return self._dedupe_article_links(links)

    def _extract_pagination_urls(
        self,
        seed_url: str,
        current_page_url: str,
        crawl_result: Any,
    ) -> list[str]:
        candidates = self._extract_link_candidates(current_page_url, crawl_result)
        pagination_urls: list[str] = []

        for item in candidates:
            candidate_url = str(item.get("url") or "").strip()
            if not candidate_url:
                continue
            if not self._is_same_host(seed_url, candidate_url):
                continue
            if candidate_url == current_page_url:
                continue
            if self._looks_like_listing_page(item, current_page_url):
                pagination_urls.append(candidate_url)

        return self._dedupe_urls(pagination_urls)

    def _extract_link_candidates(self, base_url: str, crawl_result: Any) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
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
                candidates.append({**item, "url": urljoin(base_url, href)})

        if candidates:
            return candidates

        html = str(getattr(crawl_result, "html", "") or "")
        if not html:
            return []

        parser = _AnchorParser()
        parser.feed(html)
        for item in parser.links:
            href = str(item.get("href") or "").strip()
            if not href:
                continue
            candidates.append(
                {
                    "url": urljoin(base_url, href),
                    "text": item.get("text"),
                    "title": item.get("title"),
                    "rel": item.get("rel"),
                    "class_name": item.get("class_name"),
                    "aria_label": item.get("aria_label"),
                }
            )
        return candidates

    def _to_normalized_articles(
        self,
        feed: Feed,
        discovered_links: list[dict[str, str | datetime | None]],
        seed_host: str,
    ) -> FeedAcquisitionResult:
        result = FeedAcquisitionResult(fetched_count=len(discovered_links))
        for item in discovered_links:
            url = str(item.get("url") or "").strip()
            if not self._is_article_url(url, seed_host):
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
    def _dedupe_urls(urls: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for url in urls:
            normalized = str(url).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped

    @staticmethod
    def _is_same_host(base_url: str, candidate_url: str) -> bool:
        base = urlparse(base_url).netloc.lower()
        candidate = urlparse(candidate_url).netloc.lower()
        return bool(base and candidate and base == candidate)

    def _looks_like_listing_page(
        self,
        item: dict[str, Any],
        current_page_url: str,
    ) -> bool:
        candidate_url = str(item.get("url") or "").strip()
        if not candidate_url:
            return False

        rel = str(item.get("rel") or "").lower()
        class_name = str(item.get("class_name") or item.get("class") or "").lower()
        text = str(item.get("text") or item.get("title") or "").strip().lower()
        aria_label = str(item.get("aria_label") or "").strip().lower()

        if any(token in rel for token in ("next", "prev", "pagination")):
            return True
        if "pagination" in class_name or "pager" in class_name:
            return True
        if any(token in aria_label for token in ("next", "previous", "page", "pagination")):
            return True
        if text in {"next", "previous", "prev", "older", "older posts", "newer", "newer posts"}:
            return True
        if re.fullmatch(r"\d{1,4}", text):
            return True
        if self._looks_like_pagination_url(candidate_url, current_page_url):
            return True
        return False

    @classmethod
    def _looks_like_pagination_url(cls, candidate_url: str, current_page_url: str) -> bool:
        parsed = urlparse(candidate_url)
        current = urlparse(current_page_url)

        query = parse_qs(parsed.query)
        # Substring match, not exact match: platforms like Webflow emit
        # hashed/prefixed pagination params (e.g. "8457a1db_page") that
        # never equal "page" exactly but clearly still mean pagination.
        if any(
            any(pagination_key in query_key.lower() for pagination_key in cls._PAGINATION_QUERY_KEYS)
            for query_key in query
        ):
            return True

        path = parsed.path.lower()
        if parsed.path == current.path and parsed.query == current.query:
            return False
        if re.search(r"/page/\d+/?$", path):
            return True
        if re.search(r"/p/\d+/?$", path):
            return True
        return False

    @classmethod
    def _is_article_url(cls, url: str, seed_host: str | None = None) -> bool:
        if not url:
            return False
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False

        # Reject anything off the feed's own domain outright — nav links,
        # social icons, external partner/asset links (LinkedIn, Google
        # Drive, etc.) should never be treated as articles.
        if seed_host and parsed.netloc.lower() != seed_host:
            return False

        # Reject anything that looks like a pagination/listing URL before
        # falling through to path-based heuristics.
        if cls._looks_like_pagination_url(url, url):
            return False

        path = parsed.path.lower()
        if not path or path == "/":
            return False
        if any(token in path for token in cls._NON_ARTICLE_PATH_TOKENS):
            return False
        if any(token in path for token in cls._ARTICLE_PATH_TOKENS):
            return True

        parts = [part for part in path.split("/") if part]
        if len(parts) >= 3 and all(part.isdigit() for part in parts[:3]):
            return True

        # Removed the old "any same-host URL with 2+ path segments counts
        # as an article" fallback — it was the main source of false
        # positives (product pages, nav sections, etc.). Anything that
        # doesn't match an article token or a dated-path pattern above is
        # now excluded by default; add specific per-source tokens to
        # _ARTICLE_PATH_TOKENS if a legitimate source needs a wider net.
        return False

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