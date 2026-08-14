"""Production-hardening regression tests."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from config.settings import Settings
from src.data.loader import load_dataset
from src.ui.theme import APP_CSS
from src.utils.exceptions import DataLoadError


ROOT = Path(__file__).resolve().parents[1]


def test_environment_values_are_bounded_and_endpoints_are_http(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "shell")
    monkeypatch.setenv("MAX_UPLOAD_MB", "9999")
    monkeypatch.setenv("MAX_RESULT_ROWS", "-5")
    monkeypatch.setenv("OLLAMA_BASE_URL", "file:///etc/passwd")
    monkeypatch.setenv("LM_STUDIO_BASE_URL", "file:///etc/passwd")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://user:secret@example.com/v1")
    monkeypatch.setenv("LOG_LEVEL", "verbose")
    settings = Settings.from_env()
    assert settings.llm_provider == "gemini"
    assert settings.max_upload_mb == 200
    assert settings.max_result_rows == 1
    assert settings.ollama_base_url == "http://localhost:11434/v1"
    assert settings.lm_studio_base_url == "http://localhost:1234/v1"
    assert settings.openai_base_url == ""
    assert settings.log_level == "INFO"


def test_lm_studio_provider_is_a_supported_local_endpoint(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "lmstudio")
    monkeypatch.setenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("LM_STUDIO_MODEL", "openai/gpt-oss-20b")
    settings = Settings.from_env()
    assert settings.ai_available is True
    assert settings.ai_mode == "LM Studio"
    assert settings.lm_studio_base_url == "http://127.0.0.1:1234/v1"


def test_dataset_dimension_guards(ecommerce_frame):
    csv_bytes = ecommerce_frame.to_csv(index=False).encode("utf-8")
    with pytest.raises(DataLoadError, match="row processing limit"):
        load_dataset(csv_bytes, Settings(max_dataset_rows=5), filename="orders.csv")
    with pytest.raises(DataLoadError, match="column processing limit"):
        load_dataset(csv_bytes, Settings(max_dataset_columns=3), filename="orders.csv")


def test_accessibility_and_cross_browser_css_guards_present():
    assert "system-ui" in APP_CSS
    assert "-webkit-backdrop-filter" in APP_CSS
    assert "prefers-reduced-motion" in APP_CSS
    assert "forced-colors" in APP_CSS
    assert "focus-visible" in APP_CSS
    assert "skip-link" in APP_CSS
    assert "st-key-top_navigation" in APP_CSS
    assert "telemetry-rail" in APP_CSS
    assert "kpi-meter" in APP_CSS
    assert "prefers-reduced-motion: no-preference" in APP_CSS
    assert "hoverScan" in APP_CSS
    assert "font-size:.82rem" in APP_CSS
    assert 'data-testid="stMultiSelectDropdown"' in APP_CSS
    assert "[data-tag]" in APP_CSS
    assert "grid-template-columns: repeat(6, minmax(0, 1fr))" in APP_CSS
    assert "min-height: 58px" in APP_CSS
    assert '[data-testid="stPlotlyChart"] {' in APP_CSS
    assert "transform: none !important" in APP_CSS


def test_midnight_analytics_theme_is_complete_and_native_widgets_match():
    compact = APP_CSS.replace(" ", "").lower()
    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))

    assert "v1.14midnightanalyticstheme" in compact
    assert "--canvas:#03070b" in compact
    assert "--cyan:#70ddff" in compact
    assert "background-attachment:fixed" not in compact
    assert "backdrop-filter:none" in compact
    assert "@media(forced-colors:active)" in compact
    assert "@media(prefers-reduced-motion:reduce)" in compact
    assert config["theme"]["primaryColor"] == "#70DDFF"
    assert config["theme"]["backgroundColor"] == "#03070B"
    assert config["theme"]["secondaryBackgroundColor"] == "#081119"


def test_streamlit_and_container_security_defaults():
    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert config["server"]["enableXsrfProtection"] is True
    assert config["server"]["enableCORS"] is True
    assert config["server"]["enableWebsocketCompression"] is True
    assert config["client"]["showErrorDetails"] == "none"
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "USER appuser" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "no-new-privileges:true" in compose
    assert "cap_drop" in compose
