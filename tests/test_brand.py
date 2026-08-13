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


def test_brand_mark_links_to_overview_home():
    theme_source = (ROOT / "src" / "ui" / "theme.py").read_text(encoding="utf-8")

    assert 'href="?home=1"' in theme_source
    assert 'aria-label="Go to Overview home"' in theme_source


def test_navigation_uses_vector_icons_and_portable_typography():
    theme_source = (ROOT / "src" / "ui" / "theme.py").read_text(encoding="utf-8")
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert "--font-sans:" in theme_source
    assert "Segoe UI Variable Text" in theme_source
    assert ".stApp p," in theme_source
    assert 'label:nth-of-type(6) p::before' in theme_source
    assert "mask-image:url" in theme_source
    assert "page_icons" not in app_source
