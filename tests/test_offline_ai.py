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
from src.ui.ai_assistant import CAPABILITIES, FOLLOW_UPS
from src.utils.exceptions import LLMResponseError


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


@pytest.mark.parametrize(
    ("question", "analysis_type", "expected_columns"),
    [
        ("Calculate monthly sales growth.", "growth", {"Period", "Total Sales", "Previous Sales", "Sales Growth Percent"}),
        ("Show the distribution and quartiles of sales.", "distribution", {"Sample_Size", "Median Sales", "Q1 Sales", "Q3 Sales"}),
        ("Show each region's contribution to total sales.", "contribution", {"Region", "Total Sales", "Sales Share Percent"}),
        ("Compare profit margin by region.", "comparison", {"Region", "Total Sales", "Total Profit", "Profit Margin Percent"}),
        ("Audit data quality, missing values, and exact duplicate records.", "data_quality", {"Row_Count", "Exact_Duplicate_Count"}),
    ],
)
def test_offline_agent_executes_advanced_analytics_intents(ecommerce_frame, question, analysis_type, expected_columns):
    generated = OfflineQueryPlanner(ecommerce_frame).plan(question)
    result = QueryEngine(ecommerce_frame).execute(generated.query)

    assert generated.analysis_type == analysis_type
    assert generated.plan_steps
    assert expected_columns.issubset(result.data.columns)


def test_offline_agent_supports_multi_dimension_multi_metric_tasks(ecommerce_frame):
    generated = OfflineQueryPlanner(ecommerce_frame).plan("Compare sales and profit by region and product category.")
    result = QueryEngine(ecommerce_frame).execute(generated.query)

    assert generated.columns_used == ["Region", "Product Category", "Sales", "Profit"]
    assert {"Region", "Product Category", "Total Sales", "Total Profit", "Sample_Size"}.issubset(result.data.columns)


def test_offline_agent_resolves_short_follow_up_from_verified_history(ecommerce_frame):
    generated = OfflineQueryPlanner(ecommerce_frame).plan(
        "Now by product category",
        history="Q: Show total sales by region.\nQuery: SELECT 1\nAnswer: West leads.",
    )

    assert generated.columns_used == ["Product Category", "Sales"]
    assert generated.analysis_type == "comparison"


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
    assert "West" in narrative.direct_answer
    assert "$1,100.00" in narrative.direct_answer
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


def test_balanced_mode_uses_two_grounded_model_passes(ecommerce_frame):
    settings = Settings(openai_api_key="test-key")
    client = RecordingClient()
    pipeline = NLQueryPipeline(settings, client, PromptRepository(settings.prompts_path), {})

    pipeline.run(
        "Show total sales by region.",
        QueryEngine(ecommerce_frame),
        inspect_schema(ecommerce_frame),
        analysis_mode="balanced",
    )

    assert len(client.calls) == 2
    assert pipeline.last_run_metrics["analysis_mode"] == "Balanced"
    assert pipeline.last_run_metrics["model_calls"] == 2


class CorrectionClient:
    provider_name = "Test AI"
    model = "correction-model"

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, *, response_model, **_kwargs):
        self.calls += 1
        if response_model is GeneratedQuery and self.calls == 1:
            return GeneratedQuery(
                interpreted_question="Use a missing field.",
                query='SELECT "Missing" FROM dataset',
                columns_used=["Missing"],
                reason="Deliberately invalid first plan.",
            )
        if response_model is GeneratedQuery:
            return GeneratedQuery(
                interpreted_question="Compare sales by region.",
                query='SELECT "Region", SUM("Sales") AS "Total Sales" FROM dataset GROUP BY "Region" ORDER BY "Total Sales" DESC',
                columns_used=["Region", "Sales"],
                aggregation="SUM",
                recommended_chart="bar",
                reason="Corrected regional ranking.",
            )
        return NarrativeResponse(
            direct_answer="The corrected query completed.",
            analysis="The response uses only the validated replacement plan.",
            key_findings=["A single correction was sufficient."],
            limitations="Synthetic fixture.",
            chart_caption="Validated regional sales result.",
        )


def test_pipeline_corrects_an_invalid_plan_exactly_once(ecommerce_frame):
    settings = Settings(openai_api_key="test-key")
    client = CorrectionClient()
    pipeline = NLQueryPipeline(settings, client, PromptRepository(settings.prompts_path), {})

    generated, result, _, corrected = pipeline.run(
        "Show total sales by region.",
        QueryEngine(ecommerce_frame),
        inspect_schema(ecommerce_frame),
    )

    assert corrected is True
    assert client.calls == 3
    assert generated.columns_used == ["Region", "Sales"]
    assert len(result.data) == 4
    assert pipeline.last_run_metrics["corrected"] is True


class NarrativeFailureClient(RecordingClient):
    def complete(self, *, response_model, **kwargs):
        if response_model is NarrativeResponse:
            self.calls.append((kwargs.get("reasoning_effort"), kwargs.get("verbosity")))
            raise LLMResponseError("Narrative service unavailable")
        return super().complete(response_model=response_model, **kwargs)


def test_pipeline_keeps_verified_results_when_narrative_provider_fails(ecommerce_frame):
    settings = Settings(openai_api_key="test-key")
    client = NarrativeFailureClient()
    pipeline = NLQueryPipeline(settings, client, PromptRepository(settings.prompts_path), {})

    _, result, narrative, corrected = pipeline.run(
        "Show total sales by region.",
        QueryEngine(ecommerce_frame),
        inspect_schema(ecommerce_frame),
    )

    assert corrected is False
    assert len(result.data) == 4
    assert narrative.direct_answer
    assert pipeline.last_run_metrics["provider_fallback"] is True
    assert pipeline.last_run_metrics["fallback_reason"] == "Narrative service unavailable"


@pytest.mark.parametrize("question", ["", "   ", "x" * 2001])
def test_pipeline_rejects_empty_or_oversized_questions(ecommerce_frame, question):
    settings = Settings(openai_api_key="")
    pipeline = NLQueryPipeline(settings, None, PromptRepository(settings.prompts_path), {})

    with pytest.raises(LLMResponseError, match="Question must contain"):
        pipeline.run(question, QueryEngine(ecommerce_frame), inspect_schema(ecommerce_frame))


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


@pytest.mark.parametrize(
    "question",
    [item[2] for item in CAPABILITIES]
    + [question for _label, question in FOLLOW_UPS if question is not None],
)
def test_every_assistant_action_has_a_safe_local_execution_path(ecommerce_frame, question):
    """Every visible preset and follow-up remains useful without a hosted API key."""
    generated = OfflineQueryPlanner(ecommerce_frame).plan(question)
    result = QueryEngine(ecommerce_frame).execute(generated.query)

    assert result.data is not None
    assert generated.query_language in {"duckdb_sql", "pandas"}
    assert generated.columns_used
