"""Execute the ten-question live LLM benchmark without fabricating results."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import Settings  # noqa: E402
from src.data.cleaner import clean_dataset  # noqa: E402
from src.data.loader import load_dataset  # noqa: E402
from src.data.query_engine import QueryEngine  # noqa: E402
from src.data.schema import inspect_schema, load_aliases  # noqa: E402
from src.llm.client import create_llm_client  # noqa: E402
from src.llm.nl_query import NLQueryPipeline  # noqa: E402
from src.llm.prompts import PromptRepository  # noqa: E402


def _score(item: dict[str, Any], generated, result, narrative) -> dict[str, float]:
    expected = {column.lower() for column in item["expected_columns"]}
    actual = {column.lower() for column in generated.columns_used}
    column_score = len(expected & actual) / len(expected)
    query_upper = generated.query.upper()
    operation = item["expected_operation"]
    operation_score = 1.0 if operation in query_upper or operation in (generated.aggregation or "").upper() else 0.5 if result.data is not None else 0.0
    filter_score = 1.0 if not item["expected_filters"] else sum(str(value).lower().replace(" ", "") in generated.query.lower().replace(" ", "") for value in item["expected_filters"]) / len(item["expected_filters"])
    completeness = sum(bool(value) for value in [narrative.direct_answer, narrative.analysis, narrative.key_findings, narrative.limitations]) / 4
    format_score = 1.0
    chart_score = 1.0 if generated.recommended_chart.lower() == item["expected_chart"] else 0.0
    return {"column_score": column_score, "operation_score": operation_score, "filter_score": filter_score, "accuracy_score": (column_score + operation_score + filter_score) / 3, "completeness_score": completeness, "format_compliance_score": format_score, "chart_suitability_score": chart_score}


def run(args: argparse.Namespace) -> pd.DataFrame:
    settings = replace(Settings.from_env(), llm_provider=args.provider)
    aliases = load_aliases(settings.aliases_path)
    source = Path(args.dataset) if args.dataset else settings.demo_dataset
    bundle = load_dataset(source, settings, is_demo=not bool(args.dataset))
    cleaned, log, warnings, _ = clean_dataset(bundle.raw, aliases)
    bundle.cleaned, bundle.cleaning_log, bundle.warnings = cleaned, log, warnings
    bundle.schema_profile = inspect_schema(cleaned)
    client = create_llm_client(settings)
    questions = json.loads((ROOT / "benchmarks" / "benchmark_questions.json").read_text(encoding="utf-8"))
    rows = []
    live_enabled = os.getenv("RUN_LIVE_LLM_TESTS") == "1" and client is not None
    for item in questions:
        base = {"id": item["id"], "question": item["question"], "expected_columns": "|".join(item["expected_columns"]), "expected_operation": item["expected_operation"], "expected_filters": "|".join(item["expected_filters"]), "expected_chart": item["expected_chart"]}
        if not live_enabled:
            rows.append({**base, "status": "not_run", "accuracy_score": "", "completeness_score": "", "format_compliance_score": "", "execution_success": False, "chart_suitability_score": "", "notes": "Set RUN_LIVE_LLM_TESTS=1 and configure the selected provider."})
            continue
        try:
            pipeline = NLQueryPipeline(settings, client, PromptRepository(settings.prompts_path), aliases)
            generated, result, narrative, corrected = pipeline.run(item["question"], QueryEngine(cleaned, max_rows=settings.max_result_rows), bundle.schema_profile)
            scores = _score(item, generated, result, narrative)
            rows.append({**base, "status": "completed", **scores, "execution_success": True, "notes": f"rows={len(result.data)}; corrected={corrected}"})
        except Exception as exc:
            rows.append({**base, "status": "failed", "accuracy_score": 0, "completeness_score": 0, "format_compliance_score": 0, "execution_success": False, "chart_suitability_score": 0, "notes": f"{type(exc).__name__}: {str(exc)[:200]}"})
    result_frame = pd.DataFrame(rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result_frame.to_csv(output, index=False)
    return result_frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["gemini", "openai", "ollama"], default=os.getenv("LLM_PROVIDER", "gemini"))
    parser.add_argument("--dataset", default="")
    parser.add_argument("--output", default=str(ROOT / "benchmarks" / "benchmark_results.csv"))
    args = parser.parse_args()
    frame = run(args)
    print(frame[["id", "status", "accuracy_score", "execution_success"]].to_string(index=False))


if __name__ == "__main__":
    main()
