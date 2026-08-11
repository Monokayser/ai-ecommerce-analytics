"""Typed environment-driven application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]


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
            llm_provider=os.getenv("LLM_PROVIDER", "gemini").strip().lower(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            gemini_max_output_tokens=max(512, min(int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "4096")), 8192)),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.6-terra"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", ""),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            ollama_model=os.getenv("OLLAMA_MODEL", "gpt-oss:20b"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
            llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "45")),
            llm_query_reasoning_effort=os.getenv("LLM_QUERY_REASONING_EFFORT", os.getenv("LLM_REASONING_EFFORT", "medium")),
            llm_narrative_reasoning_effort=os.getenv("LLM_NARRATIVE_REASONING_EFFORT", "low"),
            llm_response_verbosity=os.getenv("LLM_RESPONSE_VERBOSITY", "low"),
            llm_max_retries=max(0, min(int(os.getenv("LLM_MAX_RETRIES", "1")), 2)),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "200")),
            query_timeout_seconds=float(os.getenv("QUERY_TIMEOUT_SECONDS", "10")),
            max_result_rows=int(os.getenv("MAX_RESULT_ROWS", "1000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
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
