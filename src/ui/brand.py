"""Reusable product identity assets."""

from __future__ import annotations

from functools import lru_cache
from html import escape
from pathlib import Path


BRAND_ICON_PATH = Path(__file__).resolve().parents[2] / "assets" / "brand-mark.svg"


@lru_cache(maxsize=1)
def brand_icon_svg() -> str:
    """Return the trusted local SVG mark for inline application branding."""
    return BRAND_ICON_PATH.read_text(encoding="utf-8")


def inline_brand_icon(css_class: str = "brand-icon") -> str:
    """Add a controlled CSS class to the trusted SVG root element."""
    class_name = escape(css_class, quote=True)
    return brand_icon_svg().replace("<svg ", f'<svg class="{class_name}" ', 1)
