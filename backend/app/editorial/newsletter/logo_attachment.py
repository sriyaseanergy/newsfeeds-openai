from __future__ import annotations

import base64
import re
from pathlib import Path

from app.notifications.email.models import EmailAttachment

LOGO_FILENAME = "seanergy-email-logo.png"
LOGO_CONTENT_ID = LOGO_FILENAME
LOGO_PATH = Path(__file__).resolve().parent / "templates" / LOGO_FILENAME
LOGO_RELATIVE_SRC = LOGO_FILENAME
LOGO_SRC_PLACEHOLDER = "__LOGO_SRC__"
LOGO_IMG_SRC = f"cid:{LOGO_CONTENT_ID}"

_LOGO_IMG_PATTERN = re.compile(
    rf'(<img src=")(?:{re.escape(LOGO_SRC_PLACEHOLDER)}|{re.escape(LOGO_RELATIVE_SRC)}|cid:[^"]+|data:image/[^"]+)(" alt="Seanergy\.ai"[^>]*/>)',
    re.IGNORECASE,
)


def build_logo_data_uri() -> str:
    logo_bytes = LOGO_PATH.read_bytes()
    encoded = base64.b64encode(logo_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def resolve_logo_src(*, embed_for_preview: bool) -> str:
    if embed_for_preview:
        return build_logo_data_uri()
    return LOGO_IMG_SRC


def apply_logo_src(html: str, logo_src: str) -> str:
    updated, count = _LOGO_IMG_PATTERN.subn(rf"\1{logo_src}\2", html, count=1)
    if count != 1:
        msg = "Could not locate the Seanergy logo image tag in the newsletter HTML."
        raise ValueError(msg)
    return updated


def ensure_logo_cid_reference(html: str) -> str:
    return apply_logo_src(html, LOGO_IMG_SRC)


def build_logo_attachment() -> EmailAttachment:
    logo_bytes = LOGO_PATH.read_bytes()
    return EmailAttachment(
        filename=LOGO_FILENAME,
        content_type="image/png",
        content_bytes_base64=base64.b64encode(logo_bytes).decode("ascii"),
        content_id=LOGO_CONTENT_ID,
        is_inline=True,
    )
