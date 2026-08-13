"""Release metadata and machine-verifiable build-marker tests."""

from pathlib import Path
import tomllib

from config.version import APP_RELEASE, APP_VERSION
from scripts.qa_repository import check_repository


ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_consistent():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert APP_VERSION == "1.12.0"
    assert APP_RELEASE == "v1.12.0"
    assert project["project"]["version"] == APP_VERSION
    assert f"version: {APP_VERSION}" in (ROOT / "CITATION.cff").read_text(encoding="utf-8")


def test_repository_metadata_and_relative_links_are_valid():
    assert check_repository() == []
