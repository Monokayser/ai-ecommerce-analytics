"""Data quality, schema, cleaning, and performance section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import Settings
from src.data.performance import benchmark_query
from src.data.profiler import profile_quality
from src.data.query_engine import QueryEngine
from src.models import AggregationSpec, DatasetBundle, FilterSpec, QueryRequest
from src.ui.theme import render_section_intro


def render(bundle: DatasetBundle, frame: pd.DataFrame, settings: Settings) -> None:
    """Render auditable quality and performance evidence."""
    render_section_intro("Trust the evidence", "Data Quality and Performance", "Inspect schema, cleaning actions, validation checks, and measured runtime performance.")
    quality = profile_quality(bundle.cleaned)
    metrics = st.columns(4)
    metrics[0].metric("Rows", f"{quality['rows']:,}")
    metrics[1].metric("Missing cells", f"{sum(item['missing_count'] for item in quality['missing']):,}")
    metrics[2].metric("Exact duplicates", f"{quality['duplicate_rows']:,}")
    metrics[3].metric("Load time", f"{bundle.metadata.load_time_ms:.2f} ms")
    st.subheader("Readiness signal")
    if bundle.metadata.official_demo_ready:
        st.success("Official-demo ready: real dataset has at least 5,000 rows.")
    else:
        st.warning("Development mode: upload a non-demo dataset with at least 5,000 rows for official-demo readiness.")
    tabs = st.tabs(["◇ Missing Data", "✓ Cleaning Log", "▦ Schema", "◉ Validation", "⌁ Performance"])
    with tabs[0]: st.dataframe(pd.DataFrame(quality["missing"]), width="stretch")
    with tabs[1]: st.dataframe(pd.DataFrame([item.model_dump() for item in bundle.cleaning_log]), width="stretch")
    with tabs[2]:
        schema_rows = []
        for item in bundle.schema_profile.columns:
            row = item.model_dump()
            row["samples"] = ", ".join(str(value) for value in row["samples"])
            row["minimum"] = "" if row["minimum"] is None else str(row["minimum"])
            row["maximum"] = "" if row["maximum"] is None else str(row["maximum"])
            schema_rows.append(row)
        st.dataframe(pd.DataFrame(schema_rows), width="stretch")
    with tabs[3]: st.json({key: value for key, value in quality.items() if key not in {"missing", "numeric_statistics", "categorical_frequencies"}})
    with tabs[4]:
        st.write({"load_time_ms": bundle.metadata.load_time_ms, "schema_time_ms": bundle.schema_profile.generation_time_ms, "memory_mb": bundle.metadata.memory_bytes / 1024**2})
        dimension = next((column for column in ("Region", "Product Category", "Customer Segment") if column in frame), None)
        metric = next((column for column in ("Sales", "Profit", "Quantity") if column in frame), None)
        if dimension and metric and st.button("Run warm query benchmark"):
            request = QueryRequest(group_by=[dimension], aggregations=[AggregationSpec(column=metric, function="sum")])
            evidence = benchmark_query(QueryEngine(frame, max_rows=settings.max_result_rows, timeout_seconds=settings.query_timeout_seconds), request)
            st.json(evidence)
            if evidence["median_ms"] < 500: st.success("Median filtered aggregation is below the 500 ms target on this hardware.")
            else: st.warning("Median exceeds 500 ms on this hardware; see performance documentation for trade-offs.")
