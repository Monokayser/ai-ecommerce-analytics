"""Deterministic assistant and provider-independent pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from config.settings import Settings
from src.data.query_engine import QueryEngine
from src.data.schema import inspect_schema
from src.llm.nl_query import NLQueryPipeline
from src.llm.offline_planner import OfflineQueryPlanner
from src.llm.prompts import PromptRepository
from src.models import GeneratedQuery, NarrativeResponse


def test_offline_planner_ranks_region(ecommerce_frame):
    generated = OfflineQueryPlanner(ecommerce_frame).plan("Which region has the highest total sales?")
    assert generated.recommended_chart == "bar"
    assert generated.columns_used == ["Region", "Sales"]
    result = QueryEngine(ecommerce_frame).execute(generated.query)
    assert len(result.data) == 1
    assert result.data.iloc[0]["Region"] == "West"


def test_offline_planner_understands_full_ranking_direction(ecommerce_frame):
    generated = OfflineQueryPlanner(ecommerce_frame).plan("Show total sales by region from highest to lowest")

    assert 'ORDER BY "Total Sales" DESC' in generated.query
    assert "LIMIT 1000" in generated.query
    assert "top 1" not in generated.filters_used
    result = QueryEngine(ecommerce_frame).execute(generated.query)
    assert len(result.data) == 4
    assert result.data.iloc[0]["Region"] == "West"


def test_offline_planner_builds_monthly_trend(ecommerce_frame):
    generated = OfflineQueryPlanner(ecommerce_frame).plan("Show monthly sales and profit trends.")
    assert generated.recommended_chart == "line"
    assert "DATE_TRUNC" in generated.query
    result = QueryEngine(ecommerce_frame).execute(generated.query)
    assert list(result.data.columns) == ["Period", "Total Sales", "Total Profit"]


def test_pipeline_without_key_returns_grounded_answer(ecommerce_frame):
    settings = Settings(openai_api_key="")
    pipeline = NLQueryPipeline(settings, None, PromptRepository(settings.prompts_path), {})
    generated, result, narrative, corrected = pipeline.run(
        "Which countries generated losses?",
        QueryEngine(ecommerce_frame),
        inspect_schema(ecommerce_frame),
    )
    assert not corrected
    assert generated.query_language == "duckdb_sql"
    assert not result.data.empty
    assert narrative.direct_answer
    assert pipeline.last_run_metrics["mode"] == "Local analytics"


class RecordingClient:
    provider_name = "Test AI"
    model = "test-structured-model"

    def __init__(self) -> None:
        self.calls: list[tuple[str | None, str | None]] = []

    def complete(self, *, response_model, reasoning_effort=None, verbosity=None, **_kwargs):
        self.calls.append((reasoning_effort, verbosity))
        if response_model is GeneratedQuery:
            return GeneratedQuery(
                interpreted_question="Compare Sales by Region.",
                query='SELECT "Region", SUM("Sales") AS "Total Sales" FROM dataset GROUP BY "Region" ORDER BY "Total Sales" DESC',
                columns_used=["Region", "Sales"],
                aggregation="SUM",
                recommended_chart="bar",
                reason="A ranking answers the question.",
            )
        return NarrativeResponse(
            direct_answer="West leads the result.",
            analysis="The answer is grounded in the validated result.",
            key_findings=["West ranks first."],
            limitations="Test fixture.",
            chart_caption="Validated regional sales result.",
        )


def test_fast_mode_uses_one_model_pass_and_reports_live_stages(ecommerce_frame):
    settings = Settings(openai_api_key="test-key")
    client = RecordingClient()
    pipeline = NLQueryPipeline(settings, client, PromptRepository(settings.prompts_path), {})
    stages: list[str] = []

    _, result, narrative, _ = pipeline.run(
        "Show total sales by region.",
        QueryEngine(ecommerce_frame),
        inspect_schema(ecommerce_frame),
        analysis_mode="fast",
        progress=lambda stage, _message: stages.append(stage),
    )

    assert len(client.calls) == 1
    assert client.calls[0][0] == "low"
    assert len(result.data) == 4
    assert narrative.direct_answer.startswith("Region: West")
    assert stages == ["planning", "validation", "execution", "narrative", "complete"]
    assert pipeline.last_run_metrics["analysis_mode"] == "Fast"
    assert pipeline.last_run_metrics["model_calls"] == 1


def test_deep_mode_uses_high_effort_for_plan_and_narrative(ecommerce_frame):
    settings = Settings(openai_api_key="test-key")
    client = RecordingClient()
    pipeline = NLQueryPipeline(settings, client, PromptRepository(settings.prompts_path), {})

    pipeline.run(
        "Show total sales by region.",
        QueryEngine(ecommerce_frame),
        inspect_schema(ecommerce_frame),
        analysis_mode="deep",
    )

    assert client.calls == [("high", "low"), ("high", "high")]
    assert pipeline.last_run_metrics["analysis_mode"] == "Deep"
    assert pipeline.last_run_metrics["model_calls"] == 2


def test_offline_planner_filters_named_subsets(ecommerce_frame):
    generated = OfflineQueryPlanner(ecommerce_frame).plan("Compare sales in the East and West regions.")
    assert "East" in generated.query and "West" in generated.query
    result = QueryEngine(ecommerce_frame).execute(generated.query)
    assert set(result.data["Region"]) == {"East", "West"}


BENCHMARK_QUESTIONS = json.loads(
    (Path(__file__).resolve().parents[1] / "benchmarks" / "benchmark_questions.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("question", [item["question"] for item in BENCHMARK_QUESTIONS])
def test_local_mode_executes_benchmark_question(ecommerce_frame, question):
    """Every published benchmark question has a safe no-key execution path."""
    generated = OfflineQueryPlanner(ecommerce_frame).plan(question)
    result = QueryEngine(ecommerce_frame).execute(generated.query)
    assert result.data is not None
    assert generated.columns_used
