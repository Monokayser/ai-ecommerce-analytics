"""Serializable contracts shared by data, AI, visualization, and reporting layers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Forbid undocumented fields in all external contracts."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)


class DatasetMetadata(StrictModel):
    """Traceable metadata about the active dataset."""

    name: str
    source: str
    rows: int
    columns: int
    memory_bytes: int
    load_time_ms: float
    is_demo: bool = False
    official_demo_ready: bool = False


class CleaningAction(StrictModel):
    """One non-silent dataset cleaning operation."""

    operation: str
    column: str | None = None
    affected_rows: int = 0
    detail: str = ""


class ColumnProfile(StrictModel):
    """LLM-ready profile for one column."""

    name: str
    canonical_name: str
    dtype: str
    semantic_role: str
    unique_count: int
    missing_count: int
    missing_percent: float
    minimum: Any | None = None
    maximum: Any | None = None
    mean: float | None = None
    median: float | None = None
    samples: list[Any] = Field(default_factory=list)


class SchemaProfile(StrictModel):
    """Serializable dataset schema and generation timing."""

    columns: list[ColumnProfile]
    generated_at: datetime
    generation_time_ms: float


class DatasetBundle(StrictModel):
    """Raw and cleaned dataset plus audit metadata."""

    raw: pd.DataFrame
    cleaned: pd.DataFrame
    metadata: DatasetMetadata
    schema_profile: SchemaProfile | None = None
    cleaning_log: list[CleaningAction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    filter_profile: dict[str, Any] = Field(default_factory=dict)
    quality_profile: dict[str, Any] = Field(default_factory=dict)


class FilterSpec(StrictModel):
    """One categorical, numeric, or date filter."""

    column: str
    operator: Literal["eq", "in", "between", "gte", "lte"]
    value: Any
    upper: Any | None = None


class AggregationSpec(StrictModel):
    """Metric and function in an aggregation request."""

    column: str
    function: Literal["count", "sum", "mean", "median", "min", "max", "std"]
    alias: str | None = None


class QueryRequest(StrictModel):
    """Declarative direct-query request."""

    group_by: list[str] = Field(default_factory=list)
    aggregations: list[AggregationSpec]
    filters: list[FilterSpec] = Field(default_factory=list)
    sort_by: str | None = None
    ascending: bool = False
    limit: int | None = None


class QueryResult(StrictModel):
    """Safe query output and execution metadata."""

    data: pd.DataFrame
    query: str
    execution_time_ms: float
    truncated: bool = False


class GeneratedQuery(StrictModel):
    """Structured output required from the query-planning LLM."""

    interpreted_question: str
    analysis_type: Literal[
        "summary",
        "ranking",
        "trend",
        "comparison",
        "distribution",
        "relationship",
        "anomaly",
        "data_quality",
        "contribution",
        "growth",
        "detail",
    ] = "summary"
    plan_steps: list[str] = Field(default_factory=list, max_length=6)
    query_language: Literal["duckdb_sql", "pandas"] = "duckdb_sql"
    query: str
    columns_used: list[str]
    filters_used: list[str] = Field(default_factory=list)
    aggregation: str | None = None
    recommended_chart: str = "table"
    reason: str = Field(max_length=300)
    assumptions: list[str] = Field(default_factory=list, max_length=4)
    suggested_followups: list[str] = Field(default_factory=list, max_length=4)


class NarrativeResponse(StrictModel):
    """Data-grounded answer returned by the narrative LLM."""

    direct_answer: str
    analysis: str
    key_findings: list[str]
    limitations: str
    chart_caption: str


class ChartSpec(StrictModel):
    """Chart selection result."""

    chart_type: str
    x: str | None = None
    y: list[str] = Field(default_factory=list)
    color: str | None = None
    title: str = "Query result"
    rationale: str = ""


class AnomalyResult(StrictModel):
    """Anomaly detection output."""

    data: pd.DataFrame
    total_anomalies: int
    anomaly_percent: float
    method: str
    target: str


class ComparisonResult(StrictModel):
    """Side-by-side subset metrics and detailed data."""

    metrics: pd.DataFrame
    detail: pd.DataFrame
    label_a: str
    label_b: str
    warnings: list[str] = Field(default_factory=list)


class ReportPayload(StrictModel):
    """Provider-independent report export input."""

    project_title: str
    dataset_name: str
    dataset_dimensions: str
    generated_at: datetime
    applied_filters: dict[str, Any]
    question: str
    generated_query: str
    query_execution_time_ms: float
    result_table: pd.DataFrame
    narrative: str
    key_findings: list[str]
    limitations: str
    chart_image: bytes | None = None
    disclaimer: str = "AI-generated analysis should be validated before decisions are made."
    output_path: Path | None = None
