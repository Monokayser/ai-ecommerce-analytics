"""Deterministic chart selection based on result column roles."""

from __future__ import annotations

import pandas as pd

from src.models import ChartSpec


def select_chart(frame: pd.DataFrame) -> ChartSpec:
    """Choose a chart without asking the LLM to infer data types."""
    if frame.empty:
        return ChartSpec(chart_type="table", title="No matching data", rationale="The query returned no rows.")
    if frame.shape == (1, 1):
        return ChartSpec(chart_type="kpi", y=[frame.columns[0]], title=str(frame.columns[0]), rationale="Single scalar result.")
    date_columns = [column for column in frame.columns if pd.api.types.is_datetime64_any_dtype(frame[column]) or "date" in column.lower() or "month" in column.lower() or "year" in column.lower()]
    numeric = list(frame.select_dtypes(include="number").columns)
    categories = [column for column in frame.columns if column not in numeric and column not in date_columns]
    geographic = [column for column in frame.columns if any(token in column.lower() for token in ("country", "region", "state", "city"))]
    if geographic and numeric:
        return ChartSpec(chart_type="map", x=geographic[0], y=[numeric[0]], title=f"{numeric[0]} by {geographic[0]}", rationale="Geographic dimension plus measure.")
    if date_columns and numeric:
        return ChartSpec(chart_type="line", x=date_columns[0], y=numeric[:3], title="Trend over time", rationale="Date dimension plus measures.")
    if len(numeric) == 2 and not categories:
        return ChartSpec(chart_type="scatter", x=numeric[0], y=[numeric[1]], title=f"{numeric[1]} vs {numeric[0]}", rationale="Two numeric variables.")
    if categories and numeric:
        return ChartSpec(chart_type="bar", x=categories[0], y=numeric[:2], title=f"{', '.join(numeric[:2])} by {categories[0]}", rationale="Categorical comparison.")
    return ChartSpec(chart_type="table", title="Detailed result", rationale="Complex output is clearest as a table.")
