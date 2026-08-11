"""Gemini, OpenAI Responses, and Ollama structured-output clients."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import TypeVar

from google import genai
from google.genai import errors as genai_errors
from openai import APITimeoutError, APIConnectionError, APIError, AuthenticationError, BadRequestError, NotFoundError, OpenAI, RateLimitError
from pydantic import BaseModel, ValidationError

from config.settings import Settings
from src.utils.exceptions import LLMResponseError

T = TypeVar("T", bound=BaseModel)
LOGGER = logging.getLogger(__name__)


class LLMClient(ABC):
    """Provider-neutral structured-response contract."""

    @abstractmethod
    def complete(
        self,
        *,
        system: str,
        user: str,
        response_model: type[T],
        reasoning_effort: str | None = None,
        verbosity: str | None = None,
    ) -> T:
        """Return validated structured output."""


def _gemini_thinking_level(reasoning_effort: str | None) -> str:
    """Map provider-neutral effort labels to Gemini's supported levels."""
    effort = (reasoning_effort or "medium").lower()
    if effort in {"none", "minimal"}:
        return "minimal"
    if effort == "low":
        return "low"
    if effort == "medium":
        return "medium"
    return "high"


class GeminiClient(LLMClient):
    """Use the native Gemini Interactions API with Pydantic JSON schemas."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        self.last_call: dict[str, object] = {}

    @property
    def provider_name(self) -> str:
        return "Gemini"

    def complete(
        self,
        *,
        system: str,
        user: str,
        response_model: type[T],
        reasoning_effort: str | None = None,
        verbosity: str | None = None,
    ) -> T:
        del verbosity  # Output length is constrained by the response schema and token limit.
        schema = response_model.model_json_schema()
        started = time.perf_counter()
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                interaction = self.client.interactions.create(
                    model=self.model,
                    system_instruction=system,
                    input=user,
                    response_format={"type": "text", "mime_type": "application/json", "schema": schema},
                    generation_config={
                        "thinking_level": _gemini_thinking_level(reasoning_effort),
                        "max_output_tokens": self.settings.gemini_max_output_tokens,
                    },
                    store=False,
                    timeout=self.settings.llm_timeout_seconds,
                )
                content = interaction.output_text or ""
                if not content.strip():
                    raise LLMResponseError("Gemini returned an empty structured response.")
                parsed = response_model.model_validate_json(content)
                elapsed = (time.perf_counter() - started) * 1000
                self.last_call = {
                    "provider": self.provider_name,
                    "model": self.model,
                    "latency_ms": elapsed,
                    "attempts": attempt + 1,
                    "request_id": getattr(interaction, "id", ""),
                }
                LOGGER.info("llm_call_completed", extra={"event": "llm_call", "duration_ms": elapsed, "status": "success"})
                return parsed
            except genai_errors.ServerError as exc:
                if attempt < self.settings.llm_max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMResponseError("Gemini is temporarily unavailable. The local analytics fallback will be used.") from exc
            except genai_errors.ClientError as exc:
                status = int(getattr(exc, "code", 0) or 0)
                if status == 429 and attempt < self.settings.llm_max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                if status in {401, 403}:
                    raise LLMResponseError("Gemini authentication failed. Check GEMINI_API_KEY and project access.") from exc
                if status == 404:
                    raise LLMResponseError(f"The configured Gemini model '{self.model}' is unavailable.") from exc
                if status == 429:
                    raise LLMResponseError("Gemini's free-tier rate limit was reached. The local analytics fallback will be used.") from exc
                raise LLMResponseError("Gemini rejected the structured request. Check the model configuration.") from exc
            except LLMResponseError:
                raise
            except (ValidationError, json.JSONDecodeError, genai_errors.APIError) as exc:
                raise LLMResponseError("Gemini returned an invalid structured response.") from exc
        raise LLMResponseError("The Gemini request could not be completed.")


class OpenAICompatibleClient(LLMClient):
    """Use OpenAI Responses API or Ollama's OpenAI-compatible chat endpoint."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if settings.llm_provider == "ollama":
            self.client = OpenAI(base_url=settings.ollama_base_url.rstrip("/") + "/", api_key="ollama", timeout=settings.llm_timeout_seconds, max_retries=0)
            self.model = settings.ollama_model
        else:
            kwargs = {"api_key": settings.openai_api_key, "timeout": settings.llm_timeout_seconds, "max_retries": 0}
            if settings.openai_base_url:
                kwargs["base_url"] = settings.openai_base_url
            self.client = OpenAI(**kwargs)
            self.model = settings.openai_model
        self.last_call: dict[str, object] = {}

    @property
    def provider_name(self) -> str:
        return "Ollama" if self.settings.llm_provider == "ollama" else "OpenAI"

    def complete(
        self,
        *,
        system: str,
        user: str,
        response_model: type[T],
        reasoning_effort: str | None = None,
        verbosity: str | None = None,
    ) -> T:
        schema = response_model.model_json_schema()
        effort = reasoning_effort or self.settings.llm_query_reasoning_effort
        response_verbosity = verbosity or self.settings.llm_response_verbosity
        started = time.perf_counter()
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                if self.settings.llm_provider == "ollama":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                        response_format={"type": "json_schema", "json_schema": {"name": response_model.__name__, "strict": True, "schema": schema}},
                        temperature=self.settings.llm_temperature,
                    )
                    content = response.choices[0].message.content or ""
                    request_id = getattr(response, "id", "")
                    if response.choices[0].finish_reason == "length":
                        raise LLMResponseError("The local model response was truncated.")
                else:
                    response = self.client.responses.create(
                        model=self.model,
                        instructions=system,
                        input=user,
                        reasoning={"effort": effort, "context": "current_turn"},
                        text={
                            "verbosity": response_verbosity,
                            "format": {"type": "json_schema", "name": response_model.__name__, "strict": True, "schema": schema},
                        },
                    )
                    content = response.output_text or ""
                    request_id = getattr(response, "id", "")
                if not content.strip():
                    raise LLMResponseError("The model returned an empty response.")
                parsed = response_model.model_validate(json.loads(content))
                elapsed = (time.perf_counter() - started) * 1000
                self.last_call = {
                    "provider": self.provider_name,
                    "model": self.model,
                    "latency_ms": elapsed,
                    "attempts": attempt + 1,
                    "request_id": request_id,
                }
                LOGGER.info("llm_call_completed", extra={"event": "llm_call", "duration_ms": elapsed, "status": "success"})
                return parsed
            except (RateLimitError, APIConnectionError, APITimeoutError) as exc:
                if attempt < self.settings.llm_max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                if isinstance(exc, RateLimitError):
                    raise LLMResponseError("The model is busy or rate-limited. Try again shortly.") from exc
                if isinstance(exc, APITimeoutError):
                    raise LLMResponseError("The model request timed out. Try a shorter question or a faster model.") from exc
                raise LLMResponseError("The configured model endpoint is unavailable.") from exc
            except AuthenticationError as exc:
                raise LLMResponseError("Model authentication failed. Check the configured API key.") from exc
            except NotFoundError as exc:
                raise LLMResponseError(f"The configured model '{self.model}' is unavailable for this account or endpoint.") from exc
            except BadRequestError as exc:
                raise LLMResponseError("The provider rejected the structured model request. Check the model and provider settings.") from exc
            except LLMResponseError:
                raise
            except (APIError, ValidationError, json.JSONDecodeError, IndexError) as exc:
                raise LLMResponseError("The model returned an invalid structured response.") from exc
        raise LLMResponseError("The model request could not be completed.")


def create_llm_client(settings: Settings) -> LLMClient | None:
    """Create the selected provider or return None when AI is unconfigured."""
    if not settings.ai_available:
        return None
    if settings.llm_provider == "gemini":
        return GeminiClient(settings)
    return OpenAICompatibleClient(settings)
