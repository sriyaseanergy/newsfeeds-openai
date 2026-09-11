from __future__ import annotations

import html
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
from app.editorial.newsletter.logo_attachment import apply_logo_sources, resolve_logo_src

_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / "templates" / "sample_email_preview.html"
)

_DASHBOARD_URL_PLACEHOLDER = "__DASHBOARD_URL__"
_SECTIONS_START = "<!-- Sections -->"
_SECTIONS_END = "<!-- CTA Buttons -->"
_URGENCY_BADGE_LABEL = "Action Needed"
_PINNED_SECTION_TITLE = "NEEDS YOUR ATTENTION"
_MAX_SIGNAL_BULLETS = 5
_MAX_KEY_POINTS = 3


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
        "title": _PINNED_SECTION_TITLE,
    },
    _SectionKind.RELEASES: {
        "title": "RELEASES",
    },
    _SectionKind.RESEARCH: {
        "title": "RESEARCH",
    },
    _SectionKind.NOTABLE_READS: {
        "title": "NOTABLE READS",
    },
}


class NewsletterRenderer:
    def __init__(self, template_path: Path | None = None) -> None:
        self.template_path = template_path or _TEMPLATE_PATH

    def render(self, render_input: NewsletterRenderInput) -> str:
        template = self.template_path.read_text(encoding="utf-8")
        grouped = _group_articles(render_input.articles)
        sections_html = self._render_all_sections(grouped)
        signal_html = _render_todays_signal(render_input.articles)

        config = render_input.config
        generated_at = config.generated_at or datetime.now(UTC)

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
        output = _insert_after_greeting(output, signal_html)
        formatted_date = _format_header_date(generated_at)
        output = output.replace("06-Jul-2026", formatted_date)
        output = output.replace(
            _DASHBOARD_URL_PLACEHOLDER,
            _escape(config.dashboard_url),
        )
        output = re.sub(
            r"<title>.*?</title>",
            f"<title>Executive Intelligence Briefing | {_format_header_date(generated_at)}</title>",
            output,
            count=1,
        )
        output = apply_logo_sources(
            output,
            light_src=resolve_logo_src(
                embed_for_preview=config.embed_logo_for_preview,
                variant="light",
            ),
            dark_src=resolve_logo_src(
                embed_for_preview=config.embed_logo_for_preview,
                variant="dark",
            ),
        )

        if "localhost" in output.lower():
            msg = "Rendered output still contains a localhost reference."
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
    <table width="100%" cellpadding="0" cellspacing="0" border="0" class="content-table" bgcolor="#ffffff" style="background-color:#ffffff;margin-top:28px;">
      <tr>
        <td bgcolor="#ffffff" class="td-override" style="background-color:#ffffff;padding:0 0 12px 0;border-bottom:2px solid #000000;">
          <span style="font-size:18px;font-weight:700;color:#1a1a1a;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;letter-spacing:-0.01em;line-height:1.3;">
            {_escape(meta["title"])} &middot; {len(articles)}
          </span>
        </td>
      </tr>
      <tr>
        <td bgcolor="#ffffff" class="td-override" style="background-color:#ffffff;padding:16px 0 0 0;">
          <table width="100%" cellpadding="0" cellspacing="0" border="0" class="content-table" bgcolor="#ffffff" style="background-color:#ffffff;">
            {cards_html}
          </table>
        </td>
      </tr>
    </table>"""

    def _render_card(
        self,
        article: NewsletterArticle,
        kind: _SectionKind,
    ) -> str:
        enrichment_html = _render_enrichment_body(article)
        read_url = _primary_read_url(article)
        meta_line = _format_meta_line(article)
        urgency_badge = ""
        if kind is _SectionKind.CRITICAL and _needs_urgency_badge(article):
            urgency_badge = (
                '<span style="display:inline-block;margin-left:8px;background-color:#fff4e5;'
                'color:#8a4b00;font-size:9px;font-weight:700;letter-spacing:0.08em;'
                "text-transform:uppercase;padding:3px 8px;border-radius:2px;"
                'border:1px solid #f0c987;font-family:\'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif;">'
                f"{_escape(_URGENCY_BADGE_LABEL)}</span>"
            )

        image_url = (article.image_url or "").strip()
        image_cell = ""
        if image_url:
            image_cell = (
                '<td width="88" valign="top" style="vertical-align:top;padding-right:12px;">'
                f'<img src="{_escape(image_url)}" alt="" width="76" height="76" '
                'style="display:block;width:76px;height:76px;object-fit:cover;border-radius:4px;border:0;" />'
                "</td>"
            )

        body_html = f"""
                <div style="font-size:16px;color:#000000;font-weight:700;line-height:1.35;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;margin-bottom:6px;">
                  {_escape(article.title)}{urgency_badge}
                </div>
                <div style="font-size:11px;color:#777777;line-height:1.4;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;margin-bottom:10px;">
                  {_escape(meta_line)}
                </div>
                {enrichment_html}
                <div style="margin-top:12px;">
                  <a href="{_escape(read_url)}" target="_blank" rel="noopener noreferrer" style="font-size:13px;color:#000000;text-decoration:none;font-weight:600;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">Read more &#8594;</a>
                </div>"""

        if image_cell:
            content_html = f"""
                <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="background-color:#ffffff;">
                  <tr>
                    {image_cell}
                    <td valign="top" style="vertical-align:top;">
                      {body_html}
                    </td>
                  </tr>
                </table>"""
        else:
            content_html = body_html

        return f"""
            <tr>
              <td bgcolor="#ffffff" class="td-override" style="background-color:#ffffff;padding:0 0 24px 0;border-bottom:1px solid #e8e8e8;vertical-align:top;">
                {content_html}
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


def _render_enrichment_body(article: NewsletterArticle) -> str:
    enrichment = article.enrichment
    parts: list[str] = [
        (
            '<div style="font-size:13px;color:#333333;line-height:1.55;'
            "font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
            f"{_escape(enrichment.tldr)}</div>"
        )
    ]

    why_text = _single_why_it_matters(enrichment)
    if why_text:
        parts.append(
            '<div style="margin-top:10px;">'
            '<div style="font-size:10px;font-weight:700;color:#666666;letter-spacing:0.08em;'
            "text-transform:uppercase;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;"
            'margin-bottom:4px;">Why it matters</div>'
            '<div style="font-size:12px;color:#444444;line-height:1.5;'
            "font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
            f"{_escape(why_text)}</div></div>"
        )

    key_points = _key_point_bullets(enrichment)
    if key_points:
        items = "".join(
            (
                "<li style=\"margin:0 0 4px 0;font-size:12px;color:#444444;line-height:1.45;"
                "font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
                f"{_escape(point)}</li>"
            )
            for point in key_points
        )
        parts.append(
            '<div style="margin-top:10px;">'
            '<div style="font-size:10px;font-weight:700;color:#666666;letter-spacing:0.08em;'
            "text-transform:uppercase;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;"
            'margin-bottom:4px;">Key points</div>'
            f'<ul style="margin:0;padding-left:18px;">{items}</ul></div>'
        )

    if _should_show_suggested_action(article, enrichment):
        parts.append(
            '<div style="margin-top:10px;padding:8px 10px;background-color:#f7f7f7;'
            "border-left:3px solid #000000;font-size:12px;color:#333333;"
            "line-height:1.45;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
            '<span style="font-weight:700;">Suggested action:</span> '
            f"{_escape(enrichment.recommended_action.strip())}</div>"
        )

    return "".join(parts)


def _single_why_it_matters(enrichment: EnrichedArticle) -> str:
    why = enrichment.why_it_matters
    for candidate in (why.executive, why.technical_leadership, why.engineering):
        text = candidate.strip()
        if text:
            return text
    return ""


def _key_point_bullets(enrichment: EnrichedArticle) -> list[str]:
    bullets: list[str] = []
    for detail in enrichment.key_details:
        label = detail.label.strip()
        value = detail.value.strip()
        if label and value:
            bullets.append(f"{label}: {value}")
        elif value:
            bullets.append(value)
        if len(bullets) >= _MAX_KEY_POINTS:
            break
    return bullets


def _should_show_suggested_action(
    article: NewsletterArticle,
    enrichment: EnrichedArticle,
) -> bool:
    action = (enrichment.recommended_action or "").strip()
    if not action:
        return False
    return article.actionability in {
        Actionability.ACTION_RECOMMENDED,
        Actionability.IMMEDIATE_ACTION,
    }


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


def _section_kind_for_article(article: NewsletterArticle) -> _SectionKind:
    if article.article_type == ArticleType.RELEASE:
        return _SectionKind.RELEASES
    if article.article_type == ArticleType.RESEARCH:
        return _SectionKind.RESEARCH
    return _SectionKind.NOTABLE_READS


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


def _needs_urgency_badge(article: NewsletterArticle) -> bool:
    high_severity = article.severity in {Severity.HIGH, Severity.CRITICAL}
    actionable = article.actionability in {
        Actionability.ACTION_RECOMMENDED,
        Actionability.IMMEDIATE_ACTION,
    }
    return high_severity or actionable


def _article_signal_score(article: NewsletterArticle) -> int:
    score = 0
    if _is_pinned_security_article(article):
        score += 1000
    if article.severity == Severity.CRITICAL:
        score += 500
    elif article.severity == Severity.HIGH:
        score += 250
    elif article.severity == Severity.MEDIUM:
        score += 80
    if article.actionability == Actionability.IMMEDIATE_ACTION:
        score += 300
    elif article.actionability == Actionability.ACTION_RECOMMENDED:
        score += 150
    if article.article_type == ArticleType.RELEASE:
        score += 90
    elif article.article_type == ArticleType.RESEARCH:
        score += 60
    return score


def _render_todays_signal(articles: list[NewsletterArticle]) -> str:
    if not articles:
        return ""

    ranked = sorted(
        articles,
        key=lambda article: (_article_signal_score(article), article.title.lower()),
        reverse=True,
    )
    bullets: list[str] = []
    for article in ranked:
        bullet = _signal_bullet(article)
        if bullet and bullet not in bullets:
            bullets.append(bullet)
        if len(bullets) >= _MAX_SIGNAL_BULLETS:
            break

    if not bullets:
        return ""

    items = "".join(
        (
            "<li style=\"margin:0 0 6px 0;font-size:13px;color:#333333;line-height:1.5;"
            "font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\">"
            f"{_escape(bullet)}</li>"
        )
        for bullet in bullets
    )
    return (
        '<div style="margin:14px 0 0 0;padding:14px 16px;background-color:#f9f9f9;'
        "border:1px solid #e8e8e8;border-radius:4px;\">"
        '<div style="font-size:11px;font-weight:700;color:#000000;letter-spacing:0.08em;'
        "text-transform:uppercase;font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;"
        'margin-bottom:8px;">Today&rsquo;s signal</div>'
        f'<ul style="margin:0;padding-left:18px;">{items}</ul></div>'
    )


def _signal_bullet(article: NewsletterArticle) -> str:
    tldr = article.enrichment.tldr.strip()
    if not tldr:
        return article.title.strip()
    first_sentence = re.split(r"(?<=[.!?])\s+", tldr, maxsplit=1)[0].strip()
    if len(first_sentence) <= 180:
        return first_sentence
    return first_sentence[:177].rstrip() + "..."


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
        return (
            "Here's your latest executive intelligence briefing — "
            "security alerts, releases, research, and notable reads."
        )
    if len(domains) == 1:
        domain_phrase = domains[0]
    elif len(domains) == 2:
        domain_phrase = f"{domains[0]} and {domains[1]}"
    else:
        domain_phrase = ", ".join(domains[:-1]) + f", and {domains[-1]}"
    return (
        f"Here's what moved across {domain_phrase} — "
        "grouped by security alerts, releases, research, and notable reads."
    )


def _format_header_date(value: datetime) -> str:
    if value.tzinfo is None:
        localized = value.replace(tzinfo=UTC).astimezone()
    else:
        localized = value.astimezone()
    return localized.strftime("%d-%b-%Y")


def _format_meta_line(article: NewsletterArticle) -> str:
    source = article.source_name.strip() or "Unknown source"
    published = (
        _format_card_date(article.published_at)
        if article.published_at is not None
        else "Date unknown"
    )
    category = _format_category(article.technology_domain)
    return f"{source} · {published} · {category}"


def _format_card_date(value: datetime) -> str:
    if value.tzinfo is None:
        localized = value.replace(tzinfo=UTC).astimezone()
    else:
        localized = value.astimezone()
    return localized.strftime("%d %b %Y").lstrip("0")


def _format_category(technology_domain: str) -> str:
    domain = technology_domain.strip()
    if not domain:
        return "General"
    return domain.replace("_", " / ").replace("-", " / ")


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


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
        r'(<p style="margin:0;font-size:14px;color:#555555;line-height:1\.7;[^"]*">)(.*?)(</p>)',
        re.DOTALL,
    )
    return pattern.sub(
        rf"\1{_escape(greeting_body)}\3",
        template,
        count=1,
    )


def _insert_after_greeting(template: str, signal_block: str) -> str:
    marker = '</p>\n            </td>\n          </tr>\n\n          <!-- Sections -->'
    if marker not in template:
        msg = "Could not locate briefing intro block for signal insertion."
        raise RuntimeError(msg)
    if not signal_block.strip():
        return template
    insertion = f"</p>\n              {signal_block}\n            </td>\n          </tr>\n\n          <!-- Sections -->"
    return template.replace(marker, insertion, 1)
