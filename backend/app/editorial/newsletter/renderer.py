from __future__ import annotations

import html
import math
from datetime import UTC, datetime
from pathlib import Path

from app.editorial.classification.enums import ArticleType
from app.editorial.newsletter.models import (
    NewsletterArticle,
    NewsletterRenderConfig,
    NewsletterRenderInput,
    NewsletterSectionKind,
)

_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "base_template.html"

_STATIC_SAMPLE_START = "<!-- STATIC_SAMPLE_SECTIONS_START -->"
_STATIC_SAMPLE_END = "<!-- STATIC_SAMPLE_SECTIONS_END -->"
_SECTION_TEMPLATE_START = "<!-- RENDER_SECTION_TEMPLATE_START -->"
_SECTION_TEMPLATE_END = "<!-- RENDER_SECTION_TEMPLATE_END -->"
_CARD_TEMPLATE_START = "<!-- RENDER_CARD_TEMPLATE_START -->"
_CARD_TEMPLATE_END = "<!-- RENDER_CARD_TEMPLATE_END -->"

_SECTION_ORDER: tuple[NewsletterSectionKind, ...] = (
    NewsletterSectionKind.RELEASES,
    NewsletterSectionKind.RESEARCH,
    NewsletterSectionKind.NOTABLE_READS,
)

_SECTION_META: dict[NewsletterSectionKind, dict[str, str]] = {
    NewsletterSectionKind.RELEASES: {
        "icon_text": "RE",
        "title": "RELEASES",
        "placeholder_image": "sample_email_assets/placeholder-releases.png",
        "placeholder_alt": "Release announcement",
    },
    NewsletterSectionKind.RESEARCH: {
        "icon_text": "RS",
        "title": "RESEARCH",
        "placeholder_image": "sample_email_assets/placeholder-research.png",
        "placeholder_alt": "Research paper",
    },
    NewsletterSectionKind.NOTABLE_READS: {
        "icon_text": "NR",
        "title": "NOTABLE READS",
        "placeholder_image": "sample_email_assets/placeholder-notable-reads.png",
        "placeholder_alt": "Article",
    },
}

_WORDS_PER_MINUTE = 200


class NewsletterRenderer:
    def __init__(self, template_path: Path | None = None) -> None:
        self.template_path = template_path or _TEMPLATE_PATH

    def render(self, render_input: NewsletterRenderInput) -> str:
        template = self.template_path.read_text(encoding="utf-8")
        section_template = self._extract_block(
            template,
            _SECTION_TEMPLATE_START,
            _SECTION_TEMPLATE_END,
        )
        card_template = self._extract_block(
            template,
            _CARD_TEMPLATE_START,
            _CARD_TEMPLATE_END,
        )

        grouped = self._group_articles(render_input.articles)
        sections_html = self._render_sections(
            grouped=grouped,
            section_template=section_template,
            card_template=card_template,
        )

        stats = self._compute_stats(render_input.articles, grouped)
        config = render_input.config
        generated_at = config.generated_at or datetime.now(UTC)

        output = self._remove_block(
            template,
            _SECTION_TEMPLATE_START,
            _SECTION_TEMPLATE_END,
        )
        output = self._remove_block(
            output,
            _CARD_TEMPLATE_START,
            _CARD_TEMPLATE_END,
        )
        output = self._replace_block(
            output,
            _STATIC_SAMPLE_START,
            _STATIC_SAMPLE_END,
            sections_html,
        )

        replacements = {
            "{{HEADER_TITLE}}": self._escape(config.header_title),
            "{{HEADER_SUBTITLE}}": self._escape(config.header_subtitle),
            "{{HEADER_DATE}}": self._escape(self._format_header_date(generated_at)),
            "{{HEADER_READ_TIME_MINUTES}}": str(
                self._estimate_read_minutes(render_input.articles)
            ),
            "{{STAT_LEFT_TOP}}": str(stats.total_articles),
            "{{STAT_LEFT_BOTTOM}}": "Updates",
            "{{STAT_MIDDLE_TOP}}": str(stats.distinct_sources),
            "{{STAT_MIDDLE_BOTTOM}}": "Sources",
            "{{STAT_RIGHT_TOP}}": str(stats.release_count),
            "{{STAT_RIGHT_BOTTOM}}": "Releases",
            "{{SUMMARY_BLOCK}}": self._escape(self._build_summary(stats)),
            "{{SUMMARY_SIGNATURE}}": self._escape(config.summary_signature),
        }
        for token, value in replacements.items():
            output = output.replace(token, value)

        if _STATIC_SAMPLE_START in output or _STATIC_SAMPLE_END in output:
            msg = "Rendered output still contains STATIC_SAMPLE_SECTIONS markers."
            raise RuntimeError(msg)

        return output

    @staticmethod
    def _escape(value: str) -> str:
        return html.escape(value, quote=True)

    @staticmethod
    def _extract_block(template: str, start_marker: str, end_marker: str) -> str:
        start_index = template.index(start_marker) + len(start_marker)
        end_index = template.index(end_marker)
        return template[start_index:end_index].strip()

    @staticmethod
    def _remove_block(template: str, start_marker: str, end_marker: str) -> str:
        start_index = template.index(start_marker)
        end_index = template.index(end_marker) + len(end_marker)
        return template[:start_index] + template[end_index:]

    @staticmethod
    def _replace_block(
        template: str,
        start_marker: str,
        end_marker: str,
        replacement: str,
    ) -> str:
        start_index = template.index(start_marker)
        end_index = template.index(end_marker) + len(end_marker)
        return template[:start_index] + replacement + template[end_index:]

    @staticmethod
    def _group_articles(
        articles: list[NewsletterArticle],
    ) -> dict[NewsletterSectionKind, list[NewsletterArticle]]:
        grouped: dict[NewsletterSectionKind, list[NewsletterArticle]] = {
            kind: [] for kind in _SECTION_ORDER
        }
        for article in articles:
            grouped[_section_kind_for_article(article)].append(article)
        return grouped

    def _render_sections(
        self,
        *,
        grouped: dict[NewsletterSectionKind, list[NewsletterArticle]],
        section_template: str,
        card_template: str,
    ) -> str:
        rendered_sections: list[str] = []
        for kind in _SECTION_ORDER:
            articles = grouped[kind]
            if not articles:
                continue
            meta = _SECTION_META[kind]
            cards_html = "".join(
                self._render_card(
                    article=article,
                    card_template=card_template,
                    section_kind=kind,
                )
                for article in articles
            )
            section_html = section_template
            section_html = section_html.replace(
                "{{SECTION_ICON_TEXT}}",
                self._escape(meta["icon_text"]),
            )
            section_html = section_html.replace(
                "{{SECTION_TITLE}}",
                self._escape(meta["title"]),
            )
            section_html = section_html.replace(
                "{{SECTION_INSIGHTS}}",
                self._escape(f"{len(articles)} Insights"),
            )
            section_html = section_html.replace("{{SECTION_CARDS}}", cards_html)
            rendered_sections.append(section_html)
        return "".join(rendered_sections)

    def _render_card(
        self,
        *,
        article: NewsletterArticle,
        card_template: str,
        section_kind: NewsletterSectionKind,
    ) -> str:
        meta = _SECTION_META[section_kind]
        description = article.enrichment.key_points[0]
        using_real_image = bool(article.image_url)
        image_src = article.image_url or meta["placeholder_image"]
        image_alt = article.title if using_real_image else meta["placeholder_alt"]

        card_html = card_template
        card_html = card_html.replace(
            "{{CARD_HEADLINE}}",
            self._escape(article.title),
        )
        card_html = card_html.replace(
            "{{CARD_HEADLINE_URL}}",
            self._escape(article.url),
        )
        card_html = card_html.replace(
            "{{CARD_READ_MORE_URL}}",
            self._escape(article.url),
        )
        card_html = card_html.replace(
            "{{CARD_SOURCE_LINE}}",
            self._escape(self._format_source_line(article)),
        )
        card_html = card_html.replace(
            "{{CARD_DESCRIPTION}}",
            self._escape(description),
        )
        card_html = card_html.replace(
            "{{CARD_IMAGE_SRC}}",
            self._escape(image_src),
        )
        card_html = card_html.replace(
            "{{CARD_IMAGE_ALT}}",
            self._escape(image_alt),
        )
        return card_html

    @staticmethod
    def _format_header_date(value: datetime) -> str:
        localized = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        return localized.strftime("%B %d, %Y").replace(" 0", " ")

    @staticmethod
    def _format_source_line(article: NewsletterArticle) -> str:
        published = (
            article.published_at.strftime("%Y-%m-%d")
            if article.published_at is not None
            else "unknown"
        )
        return f"{article.source_name} / {published}"

    @staticmethod
    def _estimate_read_minutes(articles: list[NewsletterArticle]) -> int:
        total_words = 0
        for article in articles:
            if not article.enrichment.key_points:
                continue
            total_words += len(article.enrichment.key_points[0].split())
        if total_words == 0:
            return 1
        return max(1, math.ceil(total_words / _WORDS_PER_MINUTE))

    @staticmethod
    def _compute_stats(
        articles: list[NewsletterArticle],
        grouped: dict[NewsletterSectionKind, list[NewsletterArticle]],
    ) -> _NewsletterStats:
        return _NewsletterStats(
            total_articles=len(articles),
            distinct_sources=len({article.source_name for article in articles}),
            release_count=len(grouped[NewsletterSectionKind.RELEASES]),
            notable_read_count=len(grouped[NewsletterSectionKind.NOTABLE_READS]),
        )

    @staticmethod
    def _build_summary(stats: _NewsletterStats) -> str:
        base = (
            f"This edition covers {stats.total_articles} updates across "
            f"{stats.distinct_sources} sources"
        )
        release_label = (
            f"{stats.release_count} new "
            f"release{'s' if stats.release_count != 1 else ''}"
        )
        notable_label = (
            f"{stats.notable_read_count} notable "
            f"read{'s' if stats.notable_read_count != 1 else ''}"
        )
        if stats.release_count > 0 and stats.notable_read_count > 0:
            detail = f"including {release_label} and {notable_label} on AI and security."
        elif stats.release_count > 0:
            detail = f"including {release_label} on AI and security."
        elif stats.notable_read_count > 0:
            detail = f"including {notable_label} on AI and security."
        else:
            detail = "on AI and security."
        return f"{base} — {detail}"


class _NewsletterStats:
    def __init__(
        self,
        *,
        total_articles: int,
        distinct_sources: int,
        release_count: int,
        notable_read_count: int,
    ) -> None:
        self.total_articles = total_articles
        self.distinct_sources = distinct_sources
        self.release_count = release_count
        self.notable_read_count = notable_read_count


def _section_kind_for_article(article: NewsletterArticle) -> NewsletterSectionKind:
    if article.article_type == ArticleType.RELEASE:
        return NewsletterSectionKind.RELEASES
    if article.article_type == ArticleType.RESEARCH:
        return NewsletterSectionKind.RESEARCH
    return NewsletterSectionKind.NOTABLE_READS
