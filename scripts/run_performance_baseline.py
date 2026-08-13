"""Measure warmed filtered-query latency and process memory without invented results."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.query_engine import QueryEngine
from src.models import AggregationSpec, FilterSpec, QueryRequest


def percentile(values: list[float], percentile_value: float) -> float:
    """Return a linearly interpolated percentile for a non-empty sample."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def measure(dataset: Path, runs: int = 15) -> dict[str, object]:
    """Load a dataset, warm DuckDB, and return reproducible environment evidence."""
    started = time.perf_counter()
    frame = pd.read_csv(dataset)
    load_ms = (time.perf_counter() - started) * 1000
    engine = QueryEngine(frame, max_rows=1000, timeout_seconds=10)
    request = QueryRequest(
        group_by=["Region", "Product Category"],
        aggregations=[
            AggregationSpec(column="Sales", function="sum", alias="Total Sales"),
            AggregationSpec(column="Profit", function="sum", alias="Total Profit"),
        ],
        filters=[FilterSpec(column="Region", operator="in", value=["North", "South"])],
        sort_by="Total Sales",
        ascending=False,
        limit=100,
    )
    engine.aggregate(request)
    timings = [engine.aggregate(request).execution_time_ms for _ in range(runs)]
    process = psutil.Process()
    return {
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset.name,
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "runs": runs,
        "load_ms": round(load_ms, 3),
        "median_ms": round(statistics.median(timings), 3),
        "p95_ms": round(percentile(timings, 0.95), 3),
        "min_ms": round(min(timings), 3),
        "max_ms": round(max(timings), 3),
        "rss_memory_mb": round(process.memory_info().rss / (1024 * 1024), 2),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or "not reported",
        "target_median_ms": 500,
        "target_met": statistics.median(timings) < 500,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "sample" / "demo_ecommerce_sales.csv")
    parser.add_argument("--runs", type=int, default=15)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.runs < 7:
        parser.error("--runs must be at least 7")
    result = measure(args.dataset.resolve(), args.runs)
    payload = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
