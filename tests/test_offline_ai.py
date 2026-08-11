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


def test_offline_planner_ranks_region(ecommerce_frame):
    generated = OfflineQueryPlanner(ecommerce_frame).plan("Which region has the highest total sales?")
    assert generated.recommended_chart == "bar"
    assert generated.columns_used == ["Region", "Sales"]
    result = QueryEngine(ecommerce_frame).execute(generated.query)
    assert len(result.data) == 1
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
