import asyncio
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from statistics import mean
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from app.catalog.feed.model import Feed
from app.ingestion.acquisition import FeedAcquirer, FeedAcquisitionResult
from app.ingestion.models import NormalizedArticleData
from app.infrastructure.logging import get_logger
from crawl4ai import AsyncWebCrawler
from pydantic import BaseModel, ConfigDict, Field

logger = get_logger(__name__)


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


class _HeadMetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title_chunks: list[str] = []
        self.h1_chunks: list[str] = []
        self.in_h1 = False
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        lower_tag = tag.lower()

        if lower_tag == "title":
            self.in_title = True
            return
        if lower_tag == "h1":
            self.in_h1 = True
            return
        if lower_tag == "meta":
            key = attr_map.get("property") or attr_map.get("name")
            value = attr_map.get("content", "")
            if key and value:
                self.meta[key.lower()] = value.strip()
            return
        if lower_tag == "time":
            datetime_attr = attr_map.get("datetime", "").strip()
            if datetime_attr:
                self.meta.setdefault("time:datetime", datetime_attr)

    def handle_endtag(self, tag: str) -> None:
        lower_tag = tag.lower()
        if lower_tag == "title":
            self.in_title = False
        elif lower_tag == "h1":
            self.in_h1 = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_chunks.append(data)
        if self.in_h1:
            self.h1_chunks.append(data)

    @property
    def title_text(self) -> str:
        return " ".join(chunk.strip() for chunk in self.title_chunks).strip()

    @property
    def h1_text(self) -> str:
        return " ".join(chunk.strip() for chunk in self.h1_chunks).strip()


class _ArticleBodyParser(HTMLParser):
    _SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header", "aside", "form"}
    _BLOCK_TAGS = {"p", "div", "article", "section", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br"}
    _SKIP_HINTS = {
        "cookie",
        "comment",
        "share",
        "related",
        "sidebar",
        "advert",
        "promo",
        "social",
        "newsletter",
        "header",
        "footer",
        "nav",
        "breadcrumb",
    }

    def __init__(self):
        super().__init__()
        self._skip_stack: list[bool] = []
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower_tag = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        class_id_blob = f"{attr_map.get('class', '')} {attr_map.get('id', '')}".lower()

        if (
            lower_tag in self._SKIP_TAGS
            or any(hint in class_id_blob for hint in self._SKIP_HINTS)
        ):
            self._skip_stack.append(True)
            return

        self._skip_stack.append(False)
        if any(self._skip_stack):
            return

        if lower_tag in self._BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if not self._skip_stack:
            return
        was_skipped = self._skip_stack.pop()
        if was_skipped or any(self._skip_stack):
            return

        lower_tag = tag.lower()

        if lower_tag in self._BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if any(self._skip_stack):
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def as_text(self) -> str:
        return "\n".join(self._chunks)


class CrawlFetchConfig(BaseModel):
    """
    Crawl controls for acquisition. Keep this object as the extension point
    for future crawl options (timeouts, domain allowlists, etc.).
    """

    model_config = ConfigDict(extra="forbid")

    depth: int = Field(default=1, ge=1)
    max_new_articles_per_crawl: int = Field(default=20, ge=1)
    article_concurrency: int = Field(default=2, ge=1, le=3)
    article_delay_seconds: float = Field(default=0.25, ge=0.0)
    article_timeout_seconds: float = Field(default=25.0, gt=1.0)
    min_content_characters: int = Field(default=200, ge=1)

    @classmethod
    def from_feed(cls, feed: Feed) -> "CrawlFetchConfig":
        return cls(
            depth=feed.crawl_depth or 1,
            max_new_articles_per_crawl=feed.max_new_articles_per_crawl or 20,
        )


class Crawl4AIFetcher(FeedAcquirer):
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

    def acquire(
        self,
        feed: Feed,
        known_urls: set[str] | None = None,
    ) -> FeedAcquisitionResult:
        config = CrawlFetchConfig.from_feed(feed)
        seed_host = urlparse(feed.url).netloc.lower()
        known_urls_normalized = self._normalize_url_set(known_urls)

        discovered_links, listing_pages_crawled = self._discover_links(feed.url, config)
        discovered_article_candidates = self._prepare_article_candidates(
            discovered_links=discovered_links,
            seed_host=seed_host,
        )
        discovered_count = len(discovered_article_candidates)

        new_candidates, skipped_existing = self._filter_known_urls(
            discovered_article_candidates,
            known_urls_normalized,
        )
        selected_candidates = self._select_recent_candidates(
            candidates=new_candidates,
            limit=config.max_new_articles_per_crawl,
        )

        article_results = self._crawl_article_pages(selected_candidates, config)

        result = FeedAcquisitionResult(fetched_count=discovered_count)
        content_lengths: list[int] = []
        failed_extractions = 0
        for candidate, crawl_result, error in article_results:
            if error is not None:
                failed_extractions += 1
                result.errors.append(
                    f"Article crawl failed ({candidate['url']}): {error}"
                )
                logger.info(
                    "Crawl article skipped due to crawl failure (url=%s error=%s).",
                    candidate["url"],
                    error,
                )
                continue
            if crawl_result is None:
                failed_extractions += 1
                result.errors.append(
                    f"Article crawl failed ({candidate['url']}): empty response"
                )
                logger.info(
                    "Crawl article skipped due to empty response (url=%s).",
                    candidate["url"],
                )
                continue

            article_data = self._build_article_data(
                feed=feed,
                listing_candidate=candidate,
                crawl_result=crawl_result,
                config=config,
            )
            if article_data is None:
                failed_extractions += 1
                continue
            result.articles.append(article_data)
            content_lengths.append(len(article_data.content or ""))

        article_pages_crawled = len(selected_candidates)
        successful_extractions = len(result.articles)
        result.metrics = {
            "listing_pages_crawled": float(listing_pages_crawled),
            "article_links_discovered": float(discovered_count),
            "existing_urls_skipped": float(skipped_existing),
            "article_pages_crawled": float(article_pages_crawled),
            "successful_article_extractions": float(successful_extractions),
            "failed_article_extractions": float(failed_extractions),
            "average_content_length": float(mean(content_lengths)) if content_lengths else 0.0,
        }
        return result

    def _discover_links(
        self,
        seed_url: str,
        config: CrawlFetchConfig,
    ) -> tuple[list[dict[str, str | datetime | None]], int]:
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
        return self._dedupe_article_links(discovered_links), len(visited_listing_pages)

    def _crawl(self, url: str) -> Any:
        return asyncio.run(self._crawl_async(url))

    async def _crawl_async(self, url: str) -> Any:
        async with AsyncWebCrawler() as crawler:
            return await crawler.arun(url=url)

    def _crawl_article_pages(
        self,
        candidates: list[dict[str, str | datetime | None]],
        config: CrawlFetchConfig,
    ) -> list[tuple[dict[str, str | datetime | None], Any | None, str | None]]:
        if not candidates:
            return []
        return asyncio.run(self._crawl_article_pages_async(candidates, config))

    async def _crawl_article_pages_async(
        self,
        candidates: list[dict[str, str | datetime | None]],
        config: CrawlFetchConfig,
    ) -> list[tuple[dict[str, str | datetime | None], Any | None, str | None]]:
        semaphore = asyncio.Semaphore(config.article_concurrency)

        async with AsyncWebCrawler() as crawler:
            async def _fetch_candidate(
                candidate: dict[str, str | datetime | None],
            ) -> tuple[dict[str, str | datetime | None], Any | None, str | None]:
                url = str(candidate.get("url") or "").strip()
                if not url:
                    return candidate, None, "missing_url"
                async with semaphore:
                    if config.article_delay_seconds > 0:
                        await asyncio.sleep(config.article_delay_seconds)
                    try:
                        crawl_result = await asyncio.wait_for(
                            crawler.arun(url=url),
                            timeout=config.article_timeout_seconds,
                        )
                        return candidate, crawl_result, None
                    except TimeoutError:
                        return candidate, None, "timeout"
                    except Exception as exc:
                        return candidate, None, str(exc)

            tasks = [_fetch_candidate(candidate) for candidate in candidates]
            return list(await asyncio.gather(*tasks))

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

    def _extract_link_candidates(
        self,
        base_url: str,
        crawl_result: Any,
    ) -> list[dict[str, Any]]:
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

    def _prepare_article_candidates(
        self,
        discovered_links: list[dict[str, str | datetime | None]],
        seed_host: str,
    ) -> list[dict[str, str | datetime | None]]:
        candidates: list[dict[str, str | datetime | None]] = []
        for item in discovered_links:
            url = str(item.get("url") or "").strip()
            if not self._is_article_url(url, seed_host):
                continue
            title = self._clean_card_title(str(item.get("title") or "").strip())
            fallback = self._title_from_url(url)
            candidates.append(
                {
                    "url": url,
                    "title": title or fallback,
                    "summary": item.get("summary"),
                    "published_at": item.get("published_at"),
                }
            )
        return self._dedupe_article_links(candidates)

    @staticmethod
    def _normalize_url_set(urls: set[str] | None) -> set[str]:
        if not urls:
            return set()
        return {str(url).strip().lower() for url in urls if str(url).strip()}

    def _filter_known_urls(
        self,
        candidates: list[dict[str, str | datetime | None]],
        known_urls: set[str],
    ) -> tuple[list[dict[str, str | datetime | None]], int]:
        if not known_urls:
            return candidates, 0
        filtered: list[dict[str, str | datetime | None]] = []
        skipped = 0
        for item in candidates:
            normalized = str(item.get("url") or "").strip().lower()
            if normalized in known_urls:
                skipped += 1
                continue
            filtered.append(item)
        return filtered, skipped

    @staticmethod
    def _select_recent_candidates(
        candidates: list[dict[str, str | datetime | None]],
        limit: int,
    ) -> list[dict[str, str | datetime | None]]:
        indexed = list(enumerate(candidates))
        indexed.sort(
            key=lambda pair: (
                0 if isinstance(pair[1].get("published_at"), datetime) else 1,
                -pair[1]["published_at"].timestamp() if isinstance(pair[1].get("published_at"), datetime) else pair[0],
            )
        )
        return [item for _, item in indexed[:limit]]

    def _build_article_data(
        self,
        *,
        feed: Feed,
        listing_candidate: dict[str, str | datetime | None],
        crawl_result: Any,
        config: CrawlFetchConfig,
    ) -> NormalizedArticleData | None:
        url = str(listing_candidate.get("url") or "").strip()
        if not url:
            return None

        html = str(getattr(crawl_result, "html", "") or "")
        metadata = self._extract_article_metadata(crawl_result, html)

        page_title = self._clean_card_title(metadata.get("title", ""))
        listing_title = self._clean_card_title(str(listing_candidate.get("title") or ""))
        title = page_title or listing_title or self._title_from_url(url)
        if not title:
            logger.info("Crawl article skipped: missing title (url=%s).", url)
            return None

        summary = metadata.get("summary") or str(listing_candidate.get("summary") or "").strip() or None
        published_at = metadata.get("published_at")
        if published_at is None and isinstance(listing_candidate.get("published_at"), datetime):
            published_at = listing_candidate.get("published_at")

        content = self._extract_article_content(crawl_result, html)
        content = self._normalize_text(content)
        if len(re.sub(r"\s+", "", content)) < config.min_content_characters:
            logger.info(
                "Crawl article skipped: content below threshold (url=%s length=%s).",
                url,
                len(content),
            )
            return None

        return NormalizedArticleData(
            feed_id=feed.id,
            title=title,
            url=url,
            published_at=published_at,
            summary=self._normalize_text(summary) if summary else None,
            content=content,
            is_processed=False,
        )

    def _extract_article_metadata(self, crawl_result: Any, html: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {}

        result_title = self._clean_card_title(str(getattr(crawl_result, "title", "") or ""))
        if result_title:
            metadata["title"] = result_title

        result_meta = getattr(crawl_result, "metadata", None)
        if isinstance(result_meta, dict):
            for key in ("title", "og:title", "twitter:title"):
                value = str(result_meta.get(key) or "").strip()
                if value and "title" not in metadata:
                    metadata["title"] = value
            for key in ("description", "og:description", "twitter:description", "summary"):
                value = str(result_meta.get(key) or "").strip()
                if value and "summary" not in metadata:
                    metadata["summary"] = value
            for key in ("published_at", "published", "date", "article:published_time"):
                parsed = self._parse_datetime(result_meta.get(key))
                if parsed is not None and "published_at" not in metadata:
                    metadata["published_at"] = parsed

        if html:
            parser = _HeadMetadataParser()
            parser.feed(html)
            if "title" not in metadata:
                page_title = parser.meta.get("og:title") or parser.meta.get("twitter:title") or parser.title_text or parser.h1_text
                if page_title:
                    metadata["title"] = page_title
            if "summary" not in metadata:
                page_summary = parser.meta.get("description") or parser.meta.get("og:description") or parser.meta.get("twitter:description")
                if page_summary:
                    metadata["summary"] = page_summary
            if "published_at" not in metadata:
                date_candidate = parser.meta.get("article:published_time") or parser.meta.get("time:datetime")
                parsed = self._parse_datetime(date_candidate)
                if parsed is not None:
                    metadata["published_at"] = parsed

        return metadata

    def _extract_article_content(self, crawl_result: Any, html: str) -> str:
        structured = self._extract_structured_content(crawl_result)
        if structured:
            return structured
        if not html:
            return ""
        parser = _ArticleBodyParser()
        parser.feed(html)
        return parser.as_text()

    def _extract_structured_content(self, crawl_result: Any) -> str:
        for attr in ("extracted_content", "fit_markdown", "markdown", "cleaned_text"):
            value = getattr(crawl_result, attr, None)
            text = self._to_text(value)
            if text:
                return text
        return ""

    def _to_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts: list[str] = []
            for item in value:
                text = self._to_text(item)
                if text:
                    parts.append(text)
            return "\n".join(parts)
        if isinstance(value, dict):
            preferred_keys = ("content", "text", "markdown", "body", "article")
            parts: list[str] = []
            for key in preferred_keys:
                if key in value:
                    text = self._to_text(value[key])
                    if text:
                        parts.append(text)
            if parts:
                return "\n".join(parts)
            fallback_parts: list[str] = []
            for nested in value.values():
                nested_text = self._to_text(nested)
                if nested_text:
                    fallback_parts.append(nested_text)
            return "\n".join(fallback_parts)
        return str(value)

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

    @staticmethod
    def _clean_card_title(title: str) -> str:
        cleaned = str(title or "").strip()
        if not cleaned:
            return ""
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip(" -|:")

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
        if seed_host and parsed.netloc.lower() != seed_host:
            return False
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