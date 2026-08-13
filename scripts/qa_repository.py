"""Cross-platform repository metadata, link, and production-reference checks."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.version import APP_RELEASE, APP_VERSION


def _markdown_links(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text)


def check_repository() -> list[str]:
    errors: list[str] = []
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if project["project"]["version"] != APP_VERSION:
        errors.append("pyproject.toml does not match config/version.py")
    if f"version: {APP_VERSION}" not in citation:
        errors.append("CITATION.cff does not match config/version.py")
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    if "render_build_marker(APP_RELEASE)" not in app_text:
        errors.append("app.py does not expose the release build marker")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "https://beah4wbufhqjqgzanubteb.streamlit.app/" not in readme:
        errors.append("README is missing the public production URL")
    if "http://localhost" in (ROOT / "CITATION.cff").read_text(encoding="utf-8"):
        errors.append("Repository metadata contains a localhost production reference")
    for markdown in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
        for raw_target in _markdown_links(markdown):
            target = raw_target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (markdown.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"Broken relative link in {markdown.relative_to(ROOT)}: {raw_target}")
    if APP_RELEASE != f"v{APP_VERSION}":
        errors.append("Release label is inconsistent")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    errors = check_repository()
    if errors:
        print("\n".join(f"ERROR: {item}" for item in errors), file=sys.stderr)
        raise SystemExit(1)
    if not args.quiet:
        print(f"Repository QA passed for {APP_RELEASE}.")


if __name__ == "__main__":
    main()
