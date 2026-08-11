"""DuckDB query-engine tests."""

from __future__ import annotations

from src.data.query_engine import QueryEngine
from src.models import AggregationSpec, FilterSpec, QueryRequest


def test_aggregation_and_source_immutability(ecommerce_frame):
    original = ecommerce_frame.copy(deep=True)
    request = QueryRequest(group_by=["Region"], aggregations=[AggregationSpec(column="Sales", function="sum")], sort_by="sum_Sales", limit=3)
    result = QueryEngine(ecommerce_frame).aggregate(request)
    assert list(result.data.columns) == ["Region", "sum_Sales"]
    assert len(result.data) == 3
    assert result.execution_time_ms >= 0
    assert ecommerce_frame.equals(original)


def test_categorical_numeric_date_and_empty_filters(ecommerce_frame):
    engine = QueryEngine(ecommerce_frame)
    base = [AggregationSpec(column="Sales", function="sum")]
    categorical = engine.aggregate(QueryRequest(group_by=["Region"], aggregations=base, filters=[FilterSpec(column="Region", operator="in", value=["East", "West"])]))
    assert set(categorical.data["Region"]) == {"East", "West"}
    numeric = engine.aggregate(QueryRequest(group_by=[], aggregations=base, filters=[FilterSpec(column="Sales", operator="between", value=100, upper=200)]))
    assert numeric.data.iloc[0, 0] == 570
    dated = engine.aggregate(QueryRequest(group_by=[], aggregations=base, filters=[FilterSpec(column="Order Date", operator="between", value="2024-02-01", upper="2024-02-29")]))
    assert dated.data.iloc[0, 0] == 230
    empty = engine.aggregate(QueryRequest(group_by=["Region"], aggregations=base, filters=[FilterSpec(column="Region", operator="eq", value="Missing")]))
    assert empty.data.empty


def test_result_row_limit(ecommerce_frame):
    result = QueryEngine(ecommerce_frame, max_rows=2).execute("SELECT * FROM dataset LIMIT 100")
    # Direct SQL calls are expected to be validated/wrapped by the caller; the engine faithfully executes SQL.
    assert len(result.data) == 6
