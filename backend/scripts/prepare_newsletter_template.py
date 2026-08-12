"""
One-time helper to inject renderer markers into base_template.html.

Run from backend/: python -m scripts.prepare_newsletter_template
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "editorial"
    / "newsletter"
    / "templates"
    / "base_template.html"
)

SECTION_TEMPLATE = """
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" class="content-table"
                                bgcolor="#ffffff" style="background-color:#ffffff;margin-top:8px;">
                                <tr>
                                    <td bgcolor="#ffffff" class="td-override" style="background-color:#ffffff;">

                                        <table width="100%" cellpadding="0" cellspacing="0" border="0"
                                            class="content-table" bgcolor="#ffffff" style="background-color:#ffffff;">
                                            <tr>
                                                <td bgcolor="#ffffff" class="td-override"
                                                    style="background-color:#ffffff;padding-top:36px;padding-bottom:0;">
                                                    <table width="100%" cellpadding="0" cellspacing="0" border="0"
                                                        bgcolor="#ffffff">
                                                        <tr>
                                                            <td width="48" valign="top" style="padding-right:12px;">
                                                                <div
                                                                    style="width:40px;height:40px;background-color:#f0f0f0;border-radius:50%;text-align:center;line-height:40px;font-size:12px;font-weight:700;color:#000000;font-family:Arial, 'Helvetica Neue', Helvetica, sans-serif;">
                                                                    {{SECTION_ICON_TEXT}}</div>
                                                            </td>
                                                            <td valign="top">
                                                                <span
                                                                    style="font-size:32px;font-weight:400;color:#333333;font-family:Georgia, 'Times New Roman', serif;letter-spacing:-0.01em;line-height:1.2;display:block;">{{SECTION_TITLE}}</span>
                                                                <div
                                                                    style="font-size:13px;font-weight:400;color:#555555;font-family:Arial, 'Helvetica Neue', Helvetica, sans-serif;padding-top:4px;">
                                                                    {{SECTION_INSIGHTS}}</div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td bgcolor="#ffffff"
                                                    style="background-color:#ffffff;height:28px;line-height:28px;font-size:1px;">
                                                    &nbsp;</td>
                                            </tr>
                                        </table>

                                        <table width="100%" cellpadding="0" cellspacing="0" border="0"
                                            class="content-table" bgcolor="#ffffff"
                                            style="background-color:#ffffff;margin-top:0;margin-bottom:8px;">
                                            <tr>
                                                <td bgcolor="#ffffff" class="td-override"
                                                    style="background-color:#ffffff;padding:18px 18px 12px 18px;">
                                                    <div
                                                        style="font-size:9px;font-weight:600;color:#888888;font-family:Arial, 'Helvetica Neue', Helvetica, sans-serif;letter-spacing:0.12em;text-transform:uppercase;">
                                                        Top Sources &amp; Intel
                                                    </div>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td bgcolor="#ffffff" class="td-override"
                                                    style="background-color:#ffffff;padding:0 18px 8px 18px;">
                                                    <table width="100%" cellpadding="0" cellspacing="0" border="0"
                                                        class="content-table" bgcolor="#ffffff"
                                                        style="background-color:#ffffff;">
                                                        {{SECTION_CARDS}}
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>

                                    </td>
                                </tr>
                            </table>
""".strip()

CARD_TEMPLATE = """
                                                        <tr>
                                                            <td bgcolor="#ffffff"
                                                                style="background-color:#ffffff;padding:14px 0;vertical-align:middle;">
                                                                <table width="100%" cellpadding="0" cellspacing="0"
                                                                    border="0" bgcolor="#ffffff"
                                                                    style="background-color:#ffffff;">
                                                                    <tr>
                                                                        <td
                                                                            style="vertical-align:middle;padding:0 8px 0 0;">
                                                                            <img src="{{CARD_IMAGE_SRC}}"
                                                                                alt="{{CARD_IMAGE_ALT}}" width="240"
                                                                                style="display:block;border:0;outline:none;margin-bottom:12px;height:auto;max-width:240px;width:45%;" />
                                                                            <a href="{{CARD_HEADLINE_URL}}"
                                                                                class="blue-link"
                                                                                style="font-size:15px;color:#333333;text-decoration:none;font-weight:600;line-height:1.4;font-family:Georgia, 'Times New Roman', serif;">{{CARD_HEADLINE}}</a>
                                                                            <div
                                                                                style="font-size:10px;color:#888888;line-height:1.4;font-family:Arial, 'Helvetica Neue', Helvetica, sans-serif;margin-top:3px;">
                                                                                {{CARD_SOURCE_LINE}}</div>
                                                                            <div
                                                                                style="font-size:12px;color:#555555;line-height:1.55;font-family:Arial, 'Helvetica Neue', Helvetica, sans-serif;margin-top:6px;">
                                                                                {{CARD_DESCRIPTION}}</div>
                                                                            <div style="margin-top:10px;">
                                                                                <a href="{{CARD_READ_MORE_URL}}"
                                                                                    style="font-size:13px;color:#333333;text-decoration:none;font-weight:600;font-family:Arial, 'Helvetica Neue', Helvetica, sans-serif;">Read
                                                                                    article &#8594;</a>
                                                                            </div>
                                                                        </td>
                                                                    </tr>
                                                                </table>
                                                            </td>
                                                        </tr>
""".strip()


def main() -> None:
    content = TEMPLATE_PATH.read_text(encoding="utf-8")

    content = content.replace("INTELLIGENCE BRIEF", "{{HEADER_TITLE}}")
    content = content.replace(
        "Seanergy Intelligence Brief",
        "{{HEADER_SUBTITLE}}",
    )
    content = content.replace("06-Jul-2026", "{{HEADER_DATE}}")
    content = re.sub(
        r"(<span\s+style=\"color:#000000;font-size:14px;vertical-align:middle;\">&#9719;</span>&nbsp;)\d+",
        r"\1{{HEADER_READ_TIME_MINUTES}}",
        content,
        count=1,
    )

    content = content.replace(
        "20 SECURITY<br />UPDATES",
        "{{STAT_LEFT_TOP}}<br />{{STAT_LEFT_BOTTOM}}",
    )
    content = content.replace(
        "11 ENGINEERING<br />UPDATES",
        "{{STAT_MIDDLE_TOP}}<br />{{STAT_MIDDLE_BOTTOM}}",
    )
    content = content.replace(
        "1 AI RESEARCH<br />HIGHLIGHT",
        "{{STAT_RIGHT_TOP}}<br />{{STAT_RIGHT_BOTTOM}}",
    )

    content = re.sub(
        r"(<p\s+style=\"margin:0 0 16px 0;[^\"]+\">)(.*?)(</p>)",
        r"\1{{SUMMARY_BLOCK}}\3",
        content,
        count=1,
        flags=re.DOTALL,
    )
    content = content.replace(
        "The Seanergy Intelligence Team",
        "{{SUMMARY_SIGNATURE}}",
    )

    sections_start = content.index("<!-- Sections -->")
    footer_start = content.index("<!-- Dark footer -->")
    sample_sections = content[sections_start:footer_start]
    sample_sections = sample_sections.replace(
        "<!-- Sections -->",
        "<!-- STATIC_SAMPLE_SECTIONS_START -->\n                    <!-- Sections -->",
        1,
    )
    sample_sections = (
        sample_sections.rstrip()
        + "\n\n                            <!-- STATIC_SAMPLE_SECTIONS_END -->\n\n"
    )

    template_suffix = (
        "<!-- RENDER_SECTION_TEMPLATE_START -->\n"
        f"{SECTION_TEMPLATE}\n"
        "<!-- RENDER_SECTION_TEMPLATE_END -->\n\n"
        "<!-- RENDER_CARD_TEMPLATE_START -->\n"
        f"{CARD_TEMPLATE}\n"
        "<!-- RENDER_CARD_TEMPLATE_END -->\n\n"
    )

    content = (
        content[:sections_start]
        + sample_sections
        + template_suffix
        + content[footer_start:]
    )

    TEMPLATE_PATH.write_text(content, encoding="utf-8")
    print(f"Updated template: {TEMPLATE_PATH}")


if __name__ == "__main__":
    main()
