"""Gemini structured-output adapter and provider-fallback tests."""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from config.settings import Settings
from src.data.query_engine import QueryEngine
from src.data.schema import inspect_schema
from src.llm import client as client_module
from src.llm.client import GeminiClient, LLMClient, create_llm_client
from src.llm.nl_query import NLQueryPipeline
from src.llm.prompts import PromptRepository
from src.models import GeneratedQuery
from src.utils.exceptions import LLMResponseError


def _valid_plan() -> GeneratedQuery:
    return GeneratedQuery(
        interpreted_question="Rank sales by region.",
        query='SELECT "Region", SUM("Sales") AS "Total Sales" FROM dataset GROUP BY "Region" ORDER BY "Total Sales" DESC',
        columns_used=["Region", "Sales"],
        aggregation="SUM",
        recommended_chart="bar",
        reason="Regional ranking.",
    )


def test_gemini_client_uses_native_schema_and_thinking_level(monkeypatch):
    captured = {}

    class FakeInteractions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text=_valid_plan().model_dump_json(), id="interaction-test")

    fake_sdk = SimpleNamespace(interactions=FakeInteractions())
    monkeypatch.setattr(client_module.genai, "Client", lambda api_key: fake_sdk)
    settings = Settings(llm_provider="gemini", gemini_api_key="test-key", gemini_model="gemini-3.6-flash")
    client = GeminiClient(settings)
    result = client.complete(system="policy", user="question", response_model=GeneratedQuery, reasoning_effort="medium")

    assert result.columns_used == ["Region", "Sales"]
    assert captured["model"] == "gemini-3.6-flash"
    assert captured["system_instruction"] == "policy"
    assert captured["response_format"]["mime_type"] == "application/json"
    assert captured["generation_config"]["thinking_level"] == "medium"
    assert captured["store"] is False
    assert client.last_call["request_id"] == "interaction-test"


def test_client_factory_prefers_configured_gemini(monkeypatch):
    monkeypatch.setattr(client_module.genai, "Client", lambda api_key: SimpleNamespace())
    client = create_llm_client(Settings(llm_provider="gemini", gemini_api_key="test-key"))
    assert isinstance(client, GeminiClient)
    assert create_llm_client(Settings(llm_provider="gemini", gemini_api_key="")) is None


def test_pipeline_falls_back_when_hosted_provider_is_unavailable(ecommerce_frame):
    class FailingClient(LLMClient):
        provider_name = "Gemini"
        model = "gemini-3.6-flash"

        def complete(self, **kwargs):
            raise LLMResponseError("Temporary provider failure.")

    settings = Settings(llm_provider="gemini", gemini_api_key="test-key")
    pipeline = NLQueryPipeline(settings, FailingClient(), PromptRepository(settings.prompts_path), {})
    _, result, narrative, _ = pipeline.run(
        "Which region has the highest total sales?",
        QueryEngine(ecommerce_frame),
        inspect_schema(ecommerce_frame),
    )
    assert not result.data.empty
    assert narrative.direct_answer
    assert pipeline.last_run_metrics["provider_fallback"] is True
    assert "Temporary provider failure" in pipeline.last_run_metrics["fallback_reason"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("", "empty structured response"),
        ("{truncated", "invalid structured response"),
        ('{"interpreted_question":"missing required fields"}', "invalid structured response"),
    ],
)
def test_gemini_rejects_empty_truncated_and_schema_invalid_output(monkeypatch, payload, message):
    class FakeInteractions:
        def create(self, **kwargs):
            return SimpleNamespace(output_text=payload, id="invalid")

    monkeypatch.setattr(client_module.genai, "Client", lambda api_key: SimpleNamespace(interactions=FakeInteractions()))
    client = GeminiClient(Settings(llm_provider="gemini", gemini_api_key="test", llm_max_retries=0))
    with pytest.raises(LLMResponseError, match=message):
        client.complete(system="policy", user="question", response_model=GeneratedQuery)


@pytest.mark.parametrize(
    ("code", "message"),
    [
        (401, "authentication failed"),
        (404, "model 'gemini-3.6-flash' is unavailable"),
        (429, "rate limit was reached"),
        (408, "request timed out"),
    ],
)
def test_gemini_maps_provider_errors_to_safe_messages(monkeypatch, code, message):
    class FakeInteractions:
        def create(self, **kwargs):
            raise client_module.genai_errors.ClientError(code, {"error": {"message": "sensitive provider detail"}})

    monkeypatch.setattr(client_module.genai, "Client", lambda api_key: SimpleNamespace(interactions=FakeInteractions()))
    client = GeminiClient(Settings(llm_provider="gemini", gemini_api_key="test", llm_max_retries=0))
    with pytest.raises(LLMResponseError, match=message):
        client.complete(system="policy", user="question", response_model=GeneratedQuery)


def test_gemini_retries_one_transient_server_failure(monkeypatch):
    attempts = 0

    class FakeInteractions:
        def create(self, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise client_module.genai_errors.ServerError(503, {"error": {"message": "unavailable"}})
            return SimpleNamespace(output_text=_valid_plan().model_dump_json(), id="retry-ok")

    monkeypatch.setattr(client_module.genai, "Client", lambda api_key: SimpleNamespace(interactions=FakeInteractions()))
    monkeypatch.setattr(client_module.time, "sleep", lambda _: None)
    client = GeminiClient(Settings(llm_provider="gemini", gemini_api_key="test", llm_max_retries=1))
    assert client.complete(system="policy", user="question", response_model=GeneratedQuery).aggregation == "SUM"
    assert attempts == 2
    assert client.last_call["attempts"] == 2


def test_gemini_timeout_is_retried_then_safely_reported(monkeypatch):
    class FakeInteractions:
        def create(self, **kwargs):
            raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(client_module.genai, "Client", lambda api_key: SimpleNamespace(interactions=FakeInteractions()))
    monkeypatch.setattr(client_module.time, "sleep", lambda _: None)
    client = GeminiClient(Settings(llm_provider="gemini", gemini_api_key="test", llm_max_retries=1))
    with pytest.raises(LLMResponseError, match="request timed out"):
        client.complete(system="policy", user="question", response_model=GeneratedQuery)
