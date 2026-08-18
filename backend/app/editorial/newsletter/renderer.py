from __future__ import annotations

import html
import math
import re
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from app.editorial.classification.enums import (
    Actionability,
    ArticleType,
    Severity,
)
from app.editorial.enrichment.models import EnrichedArticle
from app.editorial.newsletter.models import (
    NewsletterArticle,
    NewsletterRenderConfig,
    NewsletterRenderInput,
)

_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / "templates" / "sample_email_preview.html"
)

_SECTIONS_START = "<!-- Sections -->"
_SECTIONS_END = "<!-- CTA Buttons -->"

_WORDS_PER_MINUTE = 200
_URGENCY_BADGE_LABEL = "Action Needed"
_PINNED_SECTION_TITLE = "NEEDS YOUR ATTENTION"


class _SectionKind(str, Enum):
    CRITICAL = "critical"
    RELEASES = "releases"
    RESEARCH = "research"
    NOTABLE_READS = "notable_reads"


_SECTION_ORDER: tuple[_SectionKind, ...] = (
    _SectionKind.CRITICAL,
    _SectionKind.RELEASES,
    _SectionKind.RESEARCH,
    _SectionKind.NOTABLE_READS,
)

_SECTION_META: dict[_SectionKind, dict[str, str]] = {
    _SectionKind.CRITICAL: {
        "icon_text": "!!",
        "title": _PINNED_SECTION_TITLE,
        "panel_heading": "Priority Alerts",
        "placeholder_alt": "Critical alert",
    },
    _SectionKind.RELEASES: {
        "icon_text": "RE",
        "title": "RELEASES",
        "panel_heading": "Top Sources & Intel",
        "placeholder_alt": "Release announcement",
    },
    _SectionKind.RESEARCH: {
        "icon_text": "RS",
        "title": "RESEARCH",
        "panel_heading": "Top Sources & Intel",
        "placeholder_alt": "Research paper",
    },
    _SectionKind.NOTABLE_READS: {
        "icon_text": "NR",
        "title": "NOTABLE READS",
        "panel_heading": "Top Sources & Intel",
        "placeholder_alt": "Article",
    },
}


class NewsletterRenderer:
    def __init__(self, template_path: Path | None = None) -> None:
        self.template_path = template_path or _TEMPLATE_PATH
        self._placeholder_image_src = ""

    def render(self, render_input: NewsletterRenderInput) -> str:
        template = self.template_path.read_text(encoding="utf-8")
        self._placeholder_image_src = _extract_placeholder_image(template)

        grouped = _group_articles(render_input.articles)
        sections_html = self._render_all_sections(grouped)

        config = render_input.config
        generated_at = config.generated_at or datetime.now(UTC)
        stats = _compute_stats(render_input.articles, grouped)

        output = _replace_between(
            template,
            _SECTIONS_START,
            _SECTIONS_END,
            f"{_SECTIONS_START}\n{sections_html}\n          ",
        )

        output = _replace_greeting_paragraph(
            output,
            _build_greeting_body(render_input.articles),
        )
        output = _insert_after_greeting(
            output,
            _build_summary_paragraph(stats, config.summary_signature),
        )
        formatted_date = _format_header_date(generated_at)
        output = output.replace("06-Jul-2026", formatted_date)
        output = output.replace(
            "http://localhost:5173/feed-alerts/",
            config.dashboard_url,
        )
        output = re.sub(
            r"<title>.*?</title>",
            f"<title>Executive Intelligence Briefing | {_format_header_date(generated_at)}</title>",
            output,
            count=1,
        )

        for stale_marker in (
            "FRONTIER AI",
            "EXPERT CONTEXT",
            "ENGINEERING",
            "curated highlights across frontier AI",
        ):
            if stale_marker in output:
                msg = f"Rendered output still contains stale sample marker: {stale_marker}"
                raise RuntimeError(msg)

        return output

    def _render_all_sections(
        self,
        grouped: dict[_SectionKind, list[NewsletterArticle]],
    ) -> str:
        rendered: list[str] = []
        for kind in _SECTION_ORDER:
            articles = grouped[kind]
            if not articles:
                continue
            rendered.append(self._render_section(kind, articles))
        if not rendered:
            return ""
        body = "\n".join(rendered)
        return f"""          <tr>
            <td bgcolor="#ffffff" class="td-override" style="background-color:#ffffff;padding:0 32px 32px 32px;">
{body}
            </td>
          </tr>"""

    def _render_section(
        self,
        kind: _SectionKind,
        articles: list[NewsletterArticle],
    ) -> str:
        meta = _SECTION_META[kind]
        cards_html = "".join(self._render_card(article, kind) for article in articles)
        return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" class="content-table" bgcolor="#ffffff" style="background-color:#ffffff;margin-top:8px;">
      <tr>
        <td bgcolor="#ffffff" class="td-override" style="background-color:#ffffff;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" class="content-table" bgcolor="#ffffff" style="background-color:#ffffff;">
      <tr>
        <td bgcolor="#ffffff" class="td-override" style="background-color:#ffffff;padding-top:36px;padding-bottom:0;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff">
            <tr>
              <td width="48" valign="top" style="padding-right:12px;">
                <div style="width:40px;height:40px;background-color:#f0f0f0;border-radius:50%;text-align:center;line-height:40px;font-size:12px;font-weight:700;color:#000000;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{_escape(meta["icon_text"])}</div>
              </td>
              <td valign="top">
                <span style="font-size:24px;font-weight:700;color:#1a1a1a;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;letter-spacing:-0.01em;line-height:1.2;display:block;">{_escape(meta["title"])}</span>
                <div style="font-size:13px;font-weight:500;color:#555555;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;padding-top:4px;">{len(articles)} Insights</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td bgcolor="#ffffff" style="background-color:#ffffff;height:28px;line-height:28px;font-size:1px;">&nbsp;</td>
      </tr>
    </table>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" class="content-table"
      bgcolor="#f9f9f9" style="background-color:#f9f9f9;margin-top:0;margin-bottom:8px;border:1px solid #e0e0e0;border-radius:8px;">
      <tr>
        <td bgcolor="#f9f9f9" class="td-override" style="background-color:#f9f9f9;padding:18px 18px 12px 18px;border-radius:8px 8px 0 0;">
          <div style="font-size:9px;font-weight:600;color:#666666;
            font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;letter-spacing:0.12em;text-transform:uppercase;">
            {_escape(meta["panel_heading"])}
          </div>
        </td>
      </tr>
      <tr>
        <td bgcolor="#f9f9f9" class="td-override" style="background-color:#f9f9f9;padding:0 18px 8px 18px;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0" class="content-table" bgcolor="#f9f9f9" style="background-color:#f9f9f9;">
            {cards_html}
          </table>
        </td>
      </tr>
    </table>
        </td>
      </tr>
    </table>"""

    def _render_card(
        self,
        article: NewsletterArticle,
        kind: _SectionKind,
    ) -> str:
        meta = _SECTION_META[kind]
        enrichment_html = _render_enrichment_body(article.enrichment)
        read_url = _primary_read_url(article)
        image_block = ""
        if article.image_url:
            image_block = (
                f'<img src="{_escape(article.image_url)}" alt="{_escape(article.title)}" '
                'width="240" style="display:block;border:0;outline:none;margin-bottom:12px;'
                'height:auto;max-width:240px;width:45%;" />'
            )
        divider_class = "td-override divider-rule"
        divider_style = (
            "background-color:#f9f9f9;padding:14px 0;border-bottom:1px solid #edebe9;vertical-align:middle;"
        )
        urgency_badge = ""
        if _needs_urgency_badge(article):
            urgency_badge = (
                '<span style="display:inline-block;margin-left:8px;background-color:#fff4e5;'
                'color:#8a4b00;font-size:9px;font-weight:700;letter-spacing:0.08em;'
                "text-transform:uppercase;padding:3px 8px;border-radius:2px;"
                'border:1px solid #f0c987;font-family:\'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif;">'
                f"{_escape(_URGENCY_BADGE_LABEL)}</span>"
            )
        domain_tag = ""
        if article.technology_domain.strip():
            domain_tag = (
                '<span style="display:inline-block;margin-left:8px;color:#999999;font-size:9px;'
                "font-weight:600;letter-spacing:0.06em;text-transform:uppercase;"
                'font-family:\'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif;">'
                f"{_escape(article.technology_domain.strip())}</span>"
            )

        return f"""
            <tr>
              <td bgcolor="#f9f9f9" class="{divider_class}" style="{divider_style}">
                <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f9f9f9" style="background-color:#f9f9f9;">
                  <tr>
                    <td style="vertical-align:middle;padding:0 8px 0 0;">
                      {image_block}
                      <a href="{_escape(read_url)}" target="_blank" rel="noopener noreferrer" class="blue-link" style="font-size:15px;color:#000000;text-decoration:none;font-weight:600;line-height:1.4;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{_escape(article.title)}</a>{urgency_badge}
                      <div style="font-size:10px;color:#888888;line-height:1.4;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;margin-top:3px;">{_escape(_format_source_line(article))}{domain_tag}</div>
                      <div style="font-size:12px;color:#555555;line-height:1.55;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;margin-top:6px;">{enrichment_html}</div>
                      <div style="margin-top:10px;">
                        <a href="{_escape(read_url)}" target="_blank" rel="noopener noreferrer" style="font-size:13px;color:#000000;text-decoration:none;font-weight:600;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">Read article &#8594;</a>
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>"""


def _primary_read_url(article: NewsletterArticle) -> str:
    article_url = article.url.strip()
    if article_url:
        return article_url
    for source_url in article.enrichment.source_urls:
        candidate = source_url.strip()
        if candidate:
            return candidate
    return article.url


def _render_enrichment_body(enrichment: EnrichedArticle) -> str:
    parts: list[str] = [
        (
            '<div style="font-size:13px;color:#333333;line-height:1.55;'
            "font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
            f"{_escape(enrichment.tldr)}</div>"
        )
    ]

    why = enrichment.why_it_matters
    audience_blocks = [
        ("Executive", why.executive),
        ("Technical Leadership", why.technical_leadership),
        ("Engineering", why.engineering),
    ]
    audience_html = "".join(
        (
            '<div style="margin-top:6px;font-size:11px;color:#555555;line-height:1.5;'
            "font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
            f'<span style="font-weight:600;color:#444444;">{_escape(label)}:</span> '
            f"{_escape(text)}</div>"
        )
        for label, text in audience_blocks
    )
    parts.append(
        '<div style="margin-top:10px;padding-top:8px;border-top:1px solid #edebe9;">'
        '<div style="font-size:9px;font-weight:600;color:#666666;letter-spacing:0.1em;'
        "text-transform:uppercase;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;"
        'margin-bottom:4px;">Why it matters</div>'
        f"{audience_html}</div>"
    )

    if enrichment.key_details:
        detail_items = "".join(
            (
                "<li style=\"margin:0 0 4px 0;font-size:11px;color:#555555;line-height:1.45;"
                "font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
                f"<strong>{_escape(detail.label)}:</strong> {_escape(detail.value)}</li>"
            )
            for detail in enrichment.key_details
        )
        parts.append(
            '<div style="margin-top:10px;">'
            '<div style="font-size:9px;font-weight:600;color:#666666;letter-spacing:0.1em;'
            "text-transform:uppercase;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;"
            'margin-bottom:4px;">Key details</div>'
            f'<ul style="margin:0;padding-left:16px;">{detail_items}</ul></div>'
        )

    if enrichment.recommended_action:
        parts.append(
            '<div style="margin-top:10px;padding:8px 10px;background-color:#fff4e5;'
            "border:1px solid #f0c987;border-radius:4px;font-size:11px;color:#5c3b00;"
            "line-height:1.45;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
            '<span style="font-weight:700;text-transform:uppercase;letter-spacing:0.06em;">'
            "Recommended action:</span> "
            f"{_escape(enrichment.recommended_action)}</div>"
        )

    if enrichment.tags:
        tag_spans = "".join(
            (
                '<span style="display:inline-block;margin:0 6px 4px 0;padding:2px 7px;'
                "background-color:#eeeeee;color:#555555;font-size:9px;font-weight:600;"
                "letter-spacing:0.04em;border-radius:2px;"
                "font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
                f"{_escape(tag)}</span>"
            )
            for tag in enrichment.tags
        )
        parts.append(f'<div style="margin-top:10px;">{tag_spans}</div>')

    return "".join(parts)


def _group_articles(
    articles: list[NewsletterArticle],
) -> dict[_SectionKind, list[NewsletterArticle]]:
    grouped: dict[_SectionKind, list[NewsletterArticle]] = {
        kind: [] for kind in _SECTION_ORDER
    }
    pinned_ids: set[str] = set()

    for article in articles:
        if _is_pinned_security_article(article):
            grouped[_SectionKind.CRITICAL].append(article)
            pinned_ids.add(article.url)

    for article in articles:
        if article.url in pinned_ids:
            continue
        grouped[_section_kind_for_article(article)].append(article)

    return grouped


def _is_pinned_security_article(article: NewsletterArticle) -> bool:
    if article.severity == Severity.CRITICAL:
        return True
    if article.technology_domain.strip().upper() != "SECURITY":
        return False
    return article.severity in {
        Severity.MEDIUM,
        Severity.HIGH,
        Severity.CRITICAL,
    } or article.actionability in {
        Actionability.ACTION_RECOMMENDED,
        Actionability.IMMEDIATE_ACTION,
    }


def _section_kind_for_article(article: NewsletterArticle) -> _SectionKind:
    if article.article_type == ArticleType.RELEASE:
        return _SectionKind.RELEASES
    if article.article_type == ArticleType.RESEARCH:
        return _SectionKind.RESEARCH
    return _SectionKind.NOTABLE_READS


def _needs_urgency_badge(article: NewsletterArticle) -> bool:
    high_severity = article.severity in {Severity.HIGH, Severity.CRITICAL}
    actionable = article.actionability in {
        Actionability.ACTION_RECOMMENDED,
        Actionability.IMMEDIATE_ACTION,
    }
    return high_severity or actionable


class _NewsletterStats:
    def __init__(
        self,
        *,
        total_articles: int,
        distinct_sources: int,
        release_count: int,
        notable_read_count: int,
        critical_count: int,
    ) -> None:
        self.total_articles = total_articles
        self.distinct_sources = distinct_sources
        self.release_count = release_count
        self.notable_read_count = notable_read_count
        self.critical_count = critical_count


def _compute_stats(
    articles: list[NewsletterArticle],
    grouped: dict[_SectionKind, list[NewsletterArticle]],
) -> _NewsletterStats:
    return _NewsletterStats(
        total_articles=len(articles),
        distinct_sources=len({article.source_name for article in articles}),
        release_count=len(grouped[_SectionKind.RELEASES]),
        notable_read_count=len(grouped[_SectionKind.NOTABLE_READS]),
        critical_count=len(grouped[_SectionKind.CRITICAL]),
    )


def _build_summary(stats: _NewsletterStats) -> str:
    base = (
        f"This edition covers {stats.total_articles} updates across "
        f"{stats.distinct_sources} sources"
    )
    if stats.release_count > 0 and stats.notable_read_count > 0:
        detail = (
            f"including {stats.release_count} new releases and "
            f"{stats.notable_read_count} notable reads on AI and security."
        )
    elif stats.release_count > 0:
        detail = f"including {stats.release_count} new releases on AI and security."
    elif stats.notable_read_count > 0:
        detail = (
            f"including {stats.notable_read_count} notable reads on AI and security."
        )
    else:
        detail = "on AI and security."
    return f"{base} — {detail}"


def _build_summary_paragraph(stats: _NewsletterStats, signature: str) -> str:
    summary = _build_summary(stats)
    return (
        '<p style="margin:12px 0 0 0;font-size:13px;color:#555555;line-height:1.7;'
        "font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
        f"{_escape(summary)}<br />"
        f'<span style="color:#777777;">{_escape(signature)}</span>'
        "</p>"
    )


def _build_greeting_body(articles: list[NewsletterArticle]) -> str:
    domains = sorted(
        {
            article.technology_domain.strip()
            for article in articles
            if article.technology_domain.strip()
        },
        key=str.lower,
    )
    if not domains:
        return "Here is your latest executive intelligence briefing."
    if len(domains) == 1:
        domain_phrase = domains[0]
    elif len(domains) == 2:
        domain_phrase = f"{domains[0]} and {domains[1]}"
    else:
        domain_phrase = ", ".join(domains[:-1]) + f", and {domains[-1]}"
    return (
        f"Here's what moved across {domain_phrase} this week — "
        "grouped by security alerts, releases, research, and notable reads."
    )


def _format_header_date(value: datetime) -> str:
    if value.tzinfo is None:
        localized = value.replace(tzinfo=UTC).astimezone()
    else:
        localized = value.astimezone()
    return localized.strftime("%d-%b-%Y")


def _format_source_line(article: NewsletterArticle) -> str:
    published = (
        article.published_at.strftime("%Y-%m-%d")
        if article.published_at is not None
        else "unknown"
    )
    return f"{article.source_name} / {published}"


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _extract_placeholder_image(template: str) -> str:
    match = re.search(r'<img src="(data:image/[^"]+)" alt="New Update"', template)
    if match:
        return match.group(1)
    return ""


def _replace_between(
    template: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
) -> str:
    start_index = template.index(start_marker)
    end_index = template.index(end_marker)
    return template[:start_index] + replacement + template[end_index:]


def _replace_greeting_paragraph(template: str, greeting_body: str) -> str:
    pattern = re.compile(
        r'(<p style="margin:10px 0 0 0;[^"]*">)(.*?)(</p>)',
        re.DOTALL,
    )
    return pattern.sub(
        rf"\1{_escape(greeting_body)}\3",
        template,
        count=1,
    )


def _insert_after_greeting(template: str, summary_paragraph: str) -> str:
    marker = '</p>\n            </td>\n          </tr>\n\n          <!-- Sections -->'
    if marker not in template:
        msg = "Could not locate greeting block for summary insertion."
        raise RuntimeError(msg)
    return template.replace(
        marker,
        f"</p>\n              {summary_paragraph}\n            </td>\n          </tr>\n\n          <!-- Sections -->",
        1,
    )
