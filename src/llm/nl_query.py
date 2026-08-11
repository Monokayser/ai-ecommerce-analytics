"""Three-phase natural-language query pipeline with one correction attempt."""

from __future__ import annotations

import json
import time
from typing import Any

import pandas as pd

from config.settings import Settings
from src.data.query_engine import QueryEngine
from src.llm.client import LLMClient
from src.llm.offline_planner import OfflineQueryPlanner
from src.llm.prompts import PromptRepository
from src.llm.sandbox import PandasInterpreter
from src.llm.validator import validate_sql
from src.models import GeneratedQuery, NarrativeResponse, QueryResult, SchemaProfile
from src.utils.exceptions import AppError, LLMResponseError


class NLQueryPipeline:
    """Generate, validate, execute, correct once, and narrate a data query."""

    def __init__(self, settings: Settings, client: LLMClient | None, prompts: PromptRepository, aliases: dict[str, list[str]]) -> None:
        self.settings = settings
        self.client = client
        self.prompts = prompts
        self.aliases = aliases
        self.last_run_metrics: dict[str, Any] = {}

    @property
    def mode_label(self) -> str:
        """Human-readable assistant mode."""
        if self.client is None:
            return "Local analytics"
        return getattr(self.client, "provider_name", self.settings.ai_mode)

    @property
    def model_label(self) -> str:
        """Human-readable active model without secrets."""
        if self.client is None:
            return "Deterministic planner"
        return str(getattr(self.client, "model", "Configured model"))

    def run(
        self,
        question: str,
        engine: QueryEngine,
        schema: SchemaProfile,
        *,
        filters: dict[str, Any] | None = None,
        history: str = "",
    ) -> tuple[GeneratedQuery, QueryResult, NarrativeResponse, bool]:
        """Execute the full pipeline, returning whether correction was used."""
        from src.data.schema import schema_for_llm

        question = question.strip()
        if not question or len(question) > self.settings.question_max_chars:
            raise LLMResponseError(f"Question must contain 1-{self.settings.question_max_chars} characters.")
        run_started = time.perf_counter()
        plan_started = time.perf_counter()
        system = self.prompts.query_system(schema_for_llm(schema), self.aliases, filters or {})
        provider_fallback = False
        fallback_reason = ""
        if self.client is None:
            generated = OfflineQueryPlanner(engine.frame, max_rows=self.settings.max_result_rows).plan(question)
        else:
            context_payload = {"recent_interactions": history[-4000:], "current_question": question}
            user = "<user_request>" + json.dumps(context_payload, default=str) + "</user_request>"
            try:
                generated = self.client.complete(
                    system=system,
                    user=user,
                    response_model=GeneratedQuery,
                    reasoning_effort=self.settings.llm_query_reasoning_effort,
                    verbosity="low",
                )
            except LLMResponseError as exc:
                provider_fallback = True
                fallback_reason = str(exc)[:300]
                generated = OfflineQueryPlanner(engine.frame, max_rows=self.settings.max_result_rows).plan(question)
        plan_ms = (time.perf_counter() - plan_started) * 1000
        corrected = False
        try:
            result = self._execute(generated, engine)
        except AppError as first_error:
            if self.client is None or provider_fallback:
                raise
            corrected = True
            correction = {
                "task": "Correct this query exactly once and return a complete replacement plan.",
                "original_question": question,
                "previous_plan": generated.model_dump(),
                "sanitized_error": f"{type(first_error).__name__}: {str(first_error)[:300]}",
                "allowed_columns": engine.columns,
            }
            correction_started = time.perf_counter()
            try:
                generated = self.client.complete(
                    system=system,
                    user=json.dumps(correction, default=str),
                    response_model=GeneratedQuery,
                    reasoning_effort=self.settings.llm_query_reasoning_effort,
                    verbosity="low",
                )
            except LLMResponseError as exc:
                provider_fallback = True
                fallback_reason = str(exc)[:300]
                generated = OfflineQueryPlanner(engine.frame, max_rows=self.settings.max_result_rows).plan(question)
            plan_ms += (time.perf_counter() - correction_started) * 1000
            result = self._execute(generated, engine)
        narrative_started = time.perf_counter()
        if self.client is None or provider_fallback:
            narrative = computed_narrative(question, result.data)
        else:
            narrative_input = build_result_evidence(question, generated, result, filters or {})
            try:
                narrative = self.client.complete(
                    system=self.prompts.narrative_system(),
                    user="<verified_result>" + json.dumps(narrative_input, default=str)[:18_000] + "</verified_result>",
                    response_model=NarrativeResponse,
                    reasoning_effort=self.settings.llm_narrative_reasoning_effort,
                    verbosity=self.settings.llm_response_verbosity,
                )
            except LLMResponseError as exc:
                provider_fallback = True
                fallback_reason = str(exc)[:300]
                narrative = computed_narrative(question, result.data)
        narrative_ms = (time.perf_counter() - narrative_started) * 1000
        narrative.chart_caption = validate_caption(narrative.chart_caption, result.data)
        self.last_run_metrics = {
            "mode": self.mode_label,
            "model": self.model_label,
            "planning_ms": plan_ms,
            "execution_ms": result.execution_time_ms,
            "narrative_ms": narrative_ms,
            "total_ms": (time.perf_counter() - run_started) * 1000,
            "corrected": corrected,
            "provider_fallback": provider_fallback,
            "fallback_reason": fallback_reason,
        }
        return generated, result, narrative, corrected

    def _execute(self, generated: GeneratedQuery, engine: QueryEngine) -> QueryResult:
        unknown = sorted(set(generated.columns_used) - set(engine.columns))
        if unknown:
            raise LLMResponseError("The generated plan referenced unavailable columns: " + ", ".join(unknown))
        if generated.query_language == "duckdb_sql":
            return engine.execute(validate_sql(generated.query, max_rows=self.settings.max_result_rows))
        return PandasInterpreter(engine.frame, max_rows=self.settings.max_result_rows).execute(generated.query)


def build_result_evidence(
    question: str,
    generated: GeneratedQuery,
    result: QueryResult,
    filters: dict[str, Any],
) -> dict[str, Any]:
    """Build bounded, computed evidence for the narrative model."""
    frame = result.data
    numeric = frame.select_dtypes(include="number")
    return {
        "original_question": question,
        "interpreted_question": generated.interpreted_question,
        "applied_filters": filters,
        "query": generated.query,
        "execution_time_ms": round(result.execution_time_ms, 3),
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "columns": list(frame.columns),
        "rows": frame.head(25).to_dict("records"),
        "numeric_summary": numeric.describe().round(4).to_dict() if not numeric.empty else {},
        "missing_by_column": frame.isna().sum().to_dict(),
        "result_was_truncated": result.truncated,
    }


def validate_caption(caption: str, result: pd.DataFrame) -> str:
    """Reject unsupported numeric claims while preserving descriptive captions."""
    import re

    result_numbers = {str(value) for value in result.select_dtypes(include="number").to_numpy().flatten()[:200]}
    claimed = re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?%?", caption)
    unsupported = [value for value in claimed if value.rstrip("%") not in result_numbers]
    if unsupported:
        return f"Query result containing {len(result)} row(s) across {len(result.columns)} column(s)."
    return caption[:300]


def computed_narrative(question: str, result: pd.DataFrame) -> NarrativeResponse:
    """Create a useful, explicitly computed local-mode summary."""
    if result.empty:
        return NarrativeResponse(
            direct_answer="No matching records were found.",
            analysis="The safe local query completed successfully but returned zero rows for the active data and filters.",
            key_findings=["No result can be ranked or compared from an empty result set."],
            limitations="This answer reflects the current filters and the deterministic local planner.",
            chart_caption="The validated query returned no matching rows.",
        )
    first = result.iloc[0]
    lead = ", ".join(f"{column}: {_display_value(value)}" for column, value in first.items())
    numeric = result.select_dtypes(include="number")
    findings = [f"The query returned {len(result):,} row(s) across {len(result.columns)} column(s)."]
    if not numeric.empty:
        for column in list(numeric.columns)[:2]:
            findings.append(f"{column} ranges from {_display_value(numeric[column].min())} to {_display_value(numeric[column].max())} in this result.")
    return NarrativeResponse(
        direct_answer=lead,
        analysis=f"A deterministic, read-only plan answered: {question.strip()} The first result is shown above; review the complete table for all matching values.",
        key_findings=findings,
        limitations="Local analytics mode uses common e-commerce intents and computed summaries; configure Gemini, OpenAI, or Ollama for deeper language interpretation.",
        chart_caption=f"Validated result with {len(result):,} row(s) and {len(result.columns)} column(s).",
    )


def _display_value(value: Any) -> str:
    if pd.isna(value):
        return "missing"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)
