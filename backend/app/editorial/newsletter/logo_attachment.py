from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path

from app.notifications.email.models import EmailAttachment

LOGO_LIGHT_FILENAME = "seanergy-email-logo-light.png"
LOGO_DARK_FILENAME = "seanergy-email-logo-dark.png"
LOGO_LIGHT_CONTENT_ID = LOGO_LIGHT_FILENAME
LOGO_DARK_CONTENT_ID = LOGO_DARK_FILENAME

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
LOGO_LIGHT_PATH = _TEMPLATES_DIR / LOGO_LIGHT_FILENAME
LOGO_DARK_PATH = _TEMPLATES_DIR / LOGO_DARK_FILENAME

LOGO_SRC_LIGHT_PLACEHOLDER = "__LOGO_SRC_LIGHT__"
LOGO_SRC_DARK_PLACEHOLDER = "__LOGO_SRC_DARK__"
LOGO_SRC_LIGHT_CID = f"cid:{LOGO_LIGHT_CONTENT_ID}"
LOGO_SRC_DARK_CID = f"cid:{LOGO_DARK_CONTENT_ID}"

# Legacy single-logo aliases.
LOGO_FILENAME = LOGO_LIGHT_FILENAME
LOGO_CONTENT_ID = LOGO_LIGHT_CONTENT_ID
LOGO_PATH = LOGO_LIGHT_PATH
LOGO_SRC_PLACEHOLDER = LOGO_SRC_LIGHT_PLACEHOLDER
LOGO_IMG_SRC = LOGO_SRC_LIGHT_CID

_LOGO_IMG_STYLE = (
    "display:block;border:0;outline:none;text-decoration:none;"
    "height:32px;width:auto;max-width:140px;"
)

_LOGO_BLOCK_PATTERN = re.compile(
    r'<img src="(?:__LOGO_SRC(?:_(?:LIGHT|DARK))?__|seanergy-email-logo(?:-(?:light|dark))?\.png|cid:[^"]+|data:image/[^"]+)" '
    r'alt="Seanergy\.ai"[^>]*/>',
    re.IGNORECASE,
)

_DEBUG_LOG_PATH = Path(__file__).resolve().parents[4] / "debug-ce3fce.log"


def _debug_log(*, hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "ce3fce",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with _DEBUG_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload) + "\n")
    except OSError:
        pass
    # #endregion


def _logo_pixel_stats(path: Path) -> dict[str, int | str]:
    try:
        from PIL import Image

        img = Image.open(path).convert("RGBA")
        dark = light = 0
        for px in img.getdata():
            if px[3] < 128:
                continue
            lum = 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]
            if lum < 128:
                dark += 1
            else:
                light += 1
        return {"path": path.name, "dark_pixels": dark, "light_pixels": light}
    except Exception as exc:
        return {"path": path.name, "error": type(exc).__name__}


def _build_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_logo_data_uri(*, variant: str = "light") -> str:
    path = LOGO_LIGHT_PATH if variant == "light" else LOGO_DARK_PATH
    return _build_data_uri(path)


def resolve_logo_src(*, embed_for_preview: bool, variant: str = "light") -> str:
    if embed_for_preview:
        return build_logo_data_uri(variant=variant)
    return LOGO_SRC_LIGHT_CID if variant == "light" else LOGO_SRC_DARK_CID


def apply_logo_src(html: str, logo_src: str) -> str:
    return apply_logo_sources(
        html,
        light_src=logo_src,
        dark_src=(
            logo_src.replace(LOGO_LIGHT_CONTENT_ID, LOGO_DARK_CONTENT_ID)
            if logo_src.startswith("cid:")
            else _build_data_uri(LOGO_DARK_PATH)
        ),
    )


def apply_logo_sources(
    html: str,
    *,
    light_src: str,
    dark_src: str,
) -> str:
    if LOGO_SRC_LIGHT_PLACEHOLDER in html and LOGO_SRC_DARK_PLACEHOLDER in html:
        result = (
            html.replace(LOGO_SRC_LIGHT_PLACEHOLDER, light_src)
            .replace(LOGO_SRC_DARK_PLACEHOLDER, dark_src)
        )
    elif _LOGO_BLOCK_PATTERN.search(html):
        replacement = (
            f'<img src="{light_src}" alt="Seanergy.ai" width="140" height="32" '
            f'class="brand-logo brand-logo-light" style="{_LOGO_IMG_STYLE}" />\n'
            f'                <img src="{dark_src}" alt="Seanergy.ai" width="140" height="32" '
            f'class="brand-logo brand-logo-dark" style="{_LOGO_IMG_STYLE}" />'
        )
        result = _LOGO_BLOCK_PATTERN.sub(replacement, html, count=1)
    else:
        msg = "Could not locate the Seanergy logo image tag in the newsletter HTML."
        raise ValueError(msg)

    _debug_log(
        hypothesis_id="H2",
        location="logo_attachment.apply_logo_sources",
        message="logo_srcs_applied",
        data={
            "light_src_prefix": light_src[:40],
            "dark_src_prefix": dark_src[:40],
            "dual_img_count": result.count('class="brand-logo brand-logo-'),
            "has_filter_invert": "filter:invert" in result,
        },
    )
    return result


def ensure_logo_cid_reference(html: str) -> str:
    result = apply_logo_sources(
        html,
        light_src=LOGO_SRC_LIGHT_CID,
        dark_src=LOGO_SRC_DARK_CID,
    )
    _debug_log(
        hypothesis_id="H3",
        location="logo_attachment.ensure_logo_cid_reference",
        message="cid_references_set",
        data={
            "has_light_cid": LOGO_SRC_LIGHT_CID in result,
            "has_dark_cid": LOGO_SRC_DARK_CID in result,
        },
    )
    return result


def _build_attachment(path: Path, *, content_id: str, filename: str) -> EmailAttachment:
    logo_bytes = path.read_bytes()
    return EmailAttachment(
        filename=filename,
        content_type="image/png",
        content_bytes_base64=base64.b64encode(logo_bytes).decode("ascii"),
        content_id=content_id,
        is_inline=True,
    )


def build_logo_attachments() -> list[EmailAttachment]:
    attachments = [
        _build_attachment(
            LOGO_LIGHT_PATH,
            content_id=LOGO_LIGHT_CONTENT_ID,
            filename=LOGO_LIGHT_FILENAME,
        ),
        _build_attachment(
            LOGO_DARK_PATH,
            content_id=LOGO_DARK_CONTENT_ID,
            filename=LOGO_DARK_FILENAME,
        ),
    ]
    _debug_log(
        hypothesis_id="H1",
        location="logo_attachment.build_logo_attachments",
        message="attachments_built",
        data={
            "attachment_ids": [item.content_id for item in attachments],
            "light_stats": _logo_pixel_stats(LOGO_LIGHT_PATH),
            "dark_stats": _logo_pixel_stats(LOGO_DARK_PATH),
        },
    )
    return attachments


def build_logo_attachment() -> EmailAttachment:
    return build_logo_attachments()[0]
