"""Brand asset and favicon integration tests."""

from __future__ import annotations

from pathlib import Path

from src.ui.brand import BRAND_ICON_PATH, brand_icon_svg, inline_brand_icon


ROOT = Path(__file__).resolve().parents[1]


def test_minimal_brand_icon_is_accessible_svg():
    svg = brand_icon_svg()

    assert BRAND_ICON_PATH == ROOT / "assets" / "brand-mark.svg"
    assert 'viewBox="0 0 64 64"' in svg
    assert "<title" in svg and "<desc" in svg
    assert len(svg.encode("utf-8")) < 4_000


def test_inline_brand_icon_escapes_css_class():
    rendered = inline_brand_icon('mark" onload="bad')

    assert 'class="mark&quot; onload=&quot;bad"' in rendered
    assert ' onload="bad"' not in rendered


def test_app_uses_svg_as_page_icon():
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert "page_icon=BRAND_ICON_PATH" in app_source
