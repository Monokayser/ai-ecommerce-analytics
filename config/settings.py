"""Typed environment-driven application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(int(os.getenv(name, str(default))), maximum))
    except ValueError:
        return default


def _bounded_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        return max(minimum, min(float(os.getenv(name, str(default))), maximum))
    except ValueError:
        return default


def _choice(name: str, default: str, allowed: set[str]) -> str:
    value = os.getenv(name, default).strip().lower()
    return value if value in allowed else default


def _http_endpoint(name: str, default: str, *, allow_empty: bool = False) -> str:
    value = os.getenv(name, default).strip()
    if allow_empty and not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return default
    return value.rstrip("/")


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings with secure, presentation-friendly defaults."""

    app_name: str = "AI-Powered E-Commerce Analytics"
    dataset_title: str = "Global E-Commerce Sales"
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_max_output_tokens: int = 4096
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-terra"
    openai_base_url: str = ""
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "gpt-oss:20b"
    llm_temperature: float = 0.0
    llm_timeout_seconds: float = 45.0
    llm_query_reasoning_effort: str = "medium"
    llm_narrative_reasoning_effort: str = "low"
    llm_response_verbosity: str = "low"
    llm_max_retries: int = 1
    max_upload_mb: int = 200
    max_dataset_rows: int = 5_000_000
    max_dataset_columns: int = 500
    query_timeout_seconds: float = 10.0
    max_result_rows: int = 1000
    question_max_chars: int = 2000
    official_demo_min_rows: int = 5000
    log_level: str = "INFO"
    demo_dataset: Path = BASE_DIR / "data" / "sample" / "demo_ecommerce_sales.csv"
    aliases_path: Path = BASE_DIR / "config" / "aliases.json"
    prompts_path: Path = BASE_DIR / "config" / "prompts.yaml"

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from ``.env`` and environment variables."""
        load_dotenv(BASE_DIR / ".env")
        return cls(
            llm_provider=_choice("LLM_PROVIDER", "gemini", {"gemini", "openai", "ollama"}),
            gemini_api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            gemini_max_output_tokens=_bounded_int("GEMINI_MAX_OUTPUT_TOKENS", 4096, 512, 8192),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.6-terra"),
            openai_base_url=_http_endpoint("OPENAI_BASE_URL", "", allow_empty=True),
            ollama_base_url=_http_endpoint("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            ollama_model=os.getenv("OLLAMA_MODEL", "gpt-oss:20b"),
            llm_temperature=_bounded_float("LLM_TEMPERATURE", 0.0, 0.0, 2.0),
            llm_timeout_seconds=_bounded_float("LLM_TIMEOUT_SECONDS", 45.0, 5.0, 120.0),
            llm_query_reasoning_effort=_choice("LLM_QUERY_REASONING_EFFORT", "medium", {"minimal", "low", "medium", "high", "xhigh"}),
            llm_narrative_reasoning_effort=_choice("LLM_NARRATIVE_REASONING_EFFORT", "low", {"minimal", "low", "medium", "high"}),
            llm_response_verbosity=_choice("LLM_RESPONSE_VERBOSITY", "low", {"low", "medium", "high"}),
            llm_max_retries=_bounded_int("LLM_MAX_RETRIES", 1, 0, 2),
            max_upload_mb=_bounded_int("MAX_UPLOAD_MB", 200, 1, 200),
            max_dataset_rows=_bounded_int("MAX_DATASET_ROWS", 5_000_000, 1_000, 10_000_000),
            max_dataset_columns=_bounded_int("MAX_DATASET_COLUMNS", 500, 10, 2_000),
            query_timeout_seconds=_bounded_float("QUERY_TIMEOUT_SECONDS", 10.0, 1.0, 30.0),
            max_result_rows=_bounded_int("MAX_RESULT_ROWS", 1000, 1, 10_000),
            question_max_chars=_bounded_int("QUESTION_MAX_CHARS", 2000, 100, 10_000),
            official_demo_min_rows=_bounded_int("OFFICIAL_DEMO_MIN_ROWS", 5000, 1000, 100_000),
            log_level=_choice("LOG_LEVEL", "info", {"debug", "info", "warning", "error", "critical"}).upper(),
        )

    @property
    def ai_available(self) -> bool:
        """Return whether an external model provider is configured."""
        if self.llm_provider == "gemini":
            return bool(self.gemini_api_key)
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return self.llm_provider == "ollama"

    @property
    def ai_mode(self) -> str:
        """Return the active assistant mode without exposing secrets."""
        if self.llm_provider == "ollama":
            return "Ollama"
        if self.llm_provider == "gemini" and self.gemini_api_key:
            return "Gemini"
        if self.llm_provider == "openai" and self.openai_api_key:
            return "OpenAI"
        return "Local analytics"
