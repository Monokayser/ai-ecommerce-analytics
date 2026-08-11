"""Repeatable query performance measurements."""

from __future__ import annotations

import statistics
from typing import Any

from src.data.query_engine import QueryEngine
from src.models import QueryRequest


def benchmark_query(engine: QueryEngine, request: QueryRequest, runs: int = 7) -> dict[str, Any]:
    """Return warmed median and p95 execution times."""
    engine.aggregate(request)
    values = [engine.aggregate(request).execution_time_ms for _ in range(runs)]
    ordered = sorted(values)
    p95_index = min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))
    return {"runs": runs, "median_ms": statistics.median(values), "p95_ms": ordered[p95_index], "all_ms": values}
