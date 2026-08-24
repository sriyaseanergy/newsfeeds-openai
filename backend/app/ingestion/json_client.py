from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx
from app.catalog.feed.model import Feed
from app.core.settings import Settings, get_settings


class JsonFeedClient:
    _GITHUB_ADVISORIES_PATH = "/advisories"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def fetch_feed_items(self, feed: Feed) -> Sequence[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        next_url = self._prepare_initial_url(feed.url)
        pages_fetched = 0

        with httpx.Client(timeout=self._settings.json_api_timeout_seconds) as client:
            while next_url and pages_fetched < self._settings.json_api_max_pages:
                response = client.get(next_url, headers=self._build_headers(next_url))
                response.raise_for_status()
                payload = response.json()
                page_items = extract_json_items(payload)
                if not page_items:
                    break
                items.extend(page_items)
                pages_fetched += 1
                next_url = self._parse_next_link(response.headers.get("Link"))
                if next_url is None and self._is_github_advisories_url(feed.url):
                    page_size = self._page_size_from_url(next_url or feed.url)
                    if len(page_items) >= page_size:
                        next_url = self._github_page_fallback_url(feed.url, pages_fetched + 1)

        return items

    def _build_headers(self, url: str) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "newsfeeds-openai-ingestion",
        }
        if self._is_github_api_url(url):
            headers["Accept"] = "application/vnd.github+json"
            headers["X-GitHub-Api-Version"] = "2022-11-28"
            token = self._settings.github_api_token.strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        return headers

    def _prepare_initial_url(self, url: str) -> str:
        if not self._is_github_advisories_url(url):
            return url
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        query.setdefault("per_page", ["100"])
        flat_query = {key: values[-1] for key, values in query.items() if values}
        return urlunparse(parsed._replace(query=urlencode(flat_query)))

    @staticmethod
    def _is_github_api_url(url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return host == "api.github.com"

    def _is_github_advisories_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return (
            self._is_github_api_url(url)
            and parsed.path.rstrip("/") == self._GITHUB_ADVISORIES_PATH
        )

    @staticmethod
    def _parse_next_link(link_header: str | None) -> str | None:
        if not link_header:
            return None
        for part in link_header.split(","):
            if 'rel="next"' not in part and "rel=next" not in part:
                continue
            match = re.search(r"<([^>]+)>", part)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _page_size_from_url(url: str) -> int:
        query = parse_qs(urlparse(url).query)
        raw_values = query.get("per_page") or query.get("limit") or ["100"]
        try:
            return max(1, int(raw_values[-1]))
        except ValueError:
            return 100

    @staticmethod
    def _github_page_fallback_url(base_url: str, page: int) -> str:
        parsed = urlparse(base_url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        query["page"] = [str(page)]
        query.setdefault("per_page", ["100"])
        flat_query = {key: values[-1] for key, values in query.items() if values}
        return urlunparse(parsed._replace(query=urlencode(flat_query)))


def extract_json_items(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "results", "entries", "advisories"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []
