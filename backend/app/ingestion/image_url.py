from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

_IMG_SRC_RE = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.IGNORECASE)


def resolve_image_url(url: str | None, *, base_url: str | None = None) -> str | None:
    if not url:
        return None
    candidate = url.strip()
    if not candidate or candidate.startswith("data:"):
        return None
    if candidate.startswith(("http://", "https://")):
        return candidate
    if base_url:
        return urljoin(base_url, candidate)
    return None


def extract_image_url_from_html(html: str | None, *, base_url: str | None = None) -> str | None:
    if not html:
        return None
    match = _IMG_SRC_RE.search(html)
    if match is None:
        return None
    return resolve_image_url(match.group(1), base_url=base_url)


def extract_image_url_from_rss_entry(
    entry: dict[str, Any],
    *,
    base_url: str | None = None,
) -> str | None:
    article_url = str(entry.get("link") or base_url or "").strip() or None

    image = entry.get("image")
    if isinstance(image, dict):
        resolved = resolve_image_url(
            str(image.get("href") or image.get("url") or ""),
            base_url=article_url,
        )
        if resolved:
            return resolved

    for key in ("media_content", "media_thumbnail"):
        for item in entry.get(key) or []:
            if not isinstance(item, dict):
                continue
            medium = str(item.get("medium") or "").lower()
            mime = str(item.get("type") or "").lower()
            if key == "media_thumbnail" or medium == "image" or mime.startswith("image/"):
                resolved = resolve_image_url(
                    str(item.get("url") or item.get("href") or ""),
                    base_url=article_url,
                )
                if resolved:
                    return resolved

    for link in entry.get("links") or []:
        if not isinstance(link, dict):
            continue
        mime = str(link.get("type") or "").lower()
        rel = str(link.get("rel") or "").lower()
        if mime.startswith("image/") or rel == "enclosure" and mime.startswith("image/"):
            resolved = resolve_image_url(str(link.get("href") or ""), base_url=article_url)
            if resolved:
                return resolved

    for html_key in ("content", "summary", "description"):
        html_value = entry.get(html_key)
        if isinstance(html_value, list) and html_value:
            first = html_value[0]
            if isinstance(first, dict):
                html_value = first.get("value")
        if isinstance(html_value, str):
            resolved = extract_image_url_from_html(html_value, base_url=article_url)
            if resolved:
                return resolved

    return None


def extract_image_url_from_metadata(
    metadata: dict[str, Any],
    html: str | None = None,
    *,
    base_url: str | None = None,
) -> str | None:
    for key in ("og:image", "twitter:image", "twitter:image:src", "image"):
        resolved = resolve_image_url(str(metadata.get(key) or ""), base_url=base_url)
        if resolved:
            return resolved
    return extract_image_url_from_html(html, base_url=base_url)
