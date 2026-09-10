"""Patch sample_email_preview.html: logo CID, theme CSS, wider body."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "app/editorial/newsletter/templates/sample_email_preview.html"
NEW_HEAD_STYLE = """  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  <style>
    :root {
      color-scheme: light dark;
      supported-color-schemes: light dark;
    }
    html, body, .body-wrapper, .outer-canvas, .email-card, .email-card-inner, .content-table {
      background-color: #ffffff !important;
      background: #ffffff !important;
      color: #000000 !important;
    }
    .brand-logo {
      display: block;
      border: 0;
      outline: none;
      text-decoration: none;
      height: 32px;
      width: auto;
      max-width: 180px;
      filter: invert(1) !important;
    }
    .cta-button,
    .cta-button span {
      color: #ffffff !important;
    }
    .footer-link {
      color: #000000 !important;
      text-decoration: underline;
      font-weight: 600;
    }
    @media (prefers-color-scheme: dark) {
      html, body, .body-wrapper, .outer-canvas, .email-card, .email-card-inner, .content-table, .td-override {
        background-color: #000000 !important;
        background: #000000 !important;
        color: #ffffff !important;
      }
      p, span, div, h1, h2, h3, td, strong {
        color: #ffffff !important;
      }
      a:not(.cta-button) {
        color: #ffffff !important;
      }
      .brand-logo {
        filter: brightness(0) invert(1) !important;
      }
      .cta-button,
      .cta-button span {
        color: #000000 !important;
        background-color: #ffffff !important;
      }
      .footer-link {
        color: #ffffff !important;
      }
      .muted-meta-text {
        color: #ffffff !important;
      }
      .divider-rule {
        border-bottom: 1px solid #ffffff !important;
      }
      .blue-accent, .blue-link {
        color: #ffffff !important;
      }
    }
  </style>"""


def main() -> None:
    new_img = (
        '                <img src="seanergy-email-logo.png" alt="Seanergy.ai" width="180" height="32" '
        'class="brand-logo" style="display:block;border:0;outline:none;text-decoration:none;'
        'height:32px;width:auto;max-width:180px;filter:invert(1);" />'
    )

    html = TEMPLATE.read_text(encoding="utf-8")

    html = re.sub(
        r'<meta name="color-scheme" content="[^"]+">.*?<style>.*?</style>',
        NEW_HEAD_STYLE,
        html,
        count=1,
        flags=re.DOTALL,
    )

    html = re.sub(
        r'<img src="(?:__LOGO_SRC__|seanergy-email-logo\.png|data:image/[^"]+|cid:[^"]+)" alt="Seanergy\.ai"[^>]*/>',
        new_img,
        html,
        count=1,
    )
    replacements = [
        ("padding:0 32px;", "padding:0 22px;"),
        ("padding:20px 32px 0 32px;", "padding:20px 22px 0 22px;"),
        ("padding:18px 32px 0 32px;", "padding:18px 22px 0 22px;"),
        ("padding:0 32px 32px 32px;", "padding:0 22px 32px 22px;"),
        ("padding:28px 32px 24px 32px;", "padding:28px 22px 24px 22px;"),
        ("padding:28px 16px;", "padding:20px 6px;"),
        ('width="640"', 'width="660"'),
        ("max-width:640px", "max-width:660px"),
        ("color:#333333", "color:#000000"),
        ("color:#555555", "color:#000000"),
        ("color:#666666", "color:#000000"),
        ("color:#1a1a1a", "color:#000000"),
    ]
    for old, new in replacements:
        html = html.replace(old, new)

    TEMPLATE.write_text(html, encoding="utf-8")
    print(f"Patched {TEMPLATE}")


if __name__ == "__main__":
    main()
