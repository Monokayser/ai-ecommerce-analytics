"""LM Studio OpenAI-compatible structured-output adapter tests."""

from __future__ import annotations

from types import SimpleNamespace

from config.settings import Settings
from src.llm import client as client_module
from src.llm.client import OpenAICompatibleClient, create_llm_client
from src.models import GeneratedQuery


def _plan() -> GeneratedQuery:
    return GeneratedQuery(
        interpreted_question="Rank sales by region.",
        query='SELECT "Region", SUM("Sales") AS "Total Sales" FROM dataset GROUP BY "Region"',
        columns_used=["Region", "Sales"],
        aggregation="SUM",
        recommended_chart="bar",
        reason="Regional ranking.",
    )


def test_lm_studio_uses_chat_completions_json_schema(monkeypatch):
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = SimpleNamespace(content=_plan().model_dump_json())
            return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")], id="local-test")

    fake_sdk = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))

    def fake_openai(**kwargs):
        captured["client_kwargs"] = kwargs
        return fake_sdk

    monkeypatch.setattr(client_module, "OpenAI", fake_openai)
    settings = Settings(
        llm_provider="lmstudio",
        lm_studio_base_url="http://127.0.0.1:1234/v1",
        lm_studio_model="openai/gpt-oss-20b",
    )
    client = create_llm_client(settings)
    assert isinstance(client, OpenAICompatibleClient)
    result = client.complete(system="policy", user="question", response_model=GeneratedQuery)

    assert client.provider_name == "LM Studio"
    assert result.columns_used == ["Region", "Sales"]
    assert captured["model"] == "openai/gpt-oss-20b"
    assert captured["response_format"]["type"] == "json_schema"
    assert captured["response_format"]["json_schema"]["strict"] is True
    assert captured["client_kwargs"]["base_url"] == "http://127.0.0.1:1234/v1/"
    assert client.last_call["request_id"] == "local-test"
