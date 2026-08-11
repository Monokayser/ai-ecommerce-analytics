"""Timed DuckDB query engine for declarative and validated SQL queries."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import duckdb
import pandas as pd

from src.models import QueryRequest, QueryResult
from src.utils.exceptions import QueryExecutionError, QueryValidationError

LOGGER = logging.getLogger(__name__)
AGGREGATES = {"count": "COUNT", "sum": "SUM", "mean": "AVG", "median": "MEDIAN", "min": "MIN", "max": "MAX", "std": "STDDEV_SAMP"}


def quote_identifier(value: str) -> str:
    """Quote an already validated DataFrame column name."""
    return '"' + value.replace('"', '""') + '"'


class QueryEngine:
    """Execute read-only analytics against a DataFrame registered as ``dataset``."""

    def __init__(self, frame: pd.DataFrame, *, max_rows: int = 1000, timeout_seconds: float = 10.0) -> None:
        self._frame = frame
        self.max_rows = max_rows
        self.timeout_seconds = timeout_seconds

    @property
    def columns(self) -> list[str]:
        return list(self._frame.columns)

    @property
    def frame(self) -> pd.DataFrame:
        """Expose the registered frame as a read-only application reference."""
        return self._frame

    def _require_column(self, column: str) -> None:
        if column not in self._frame.columns:
            raise QueryValidationError(f"Unknown column: {column}")

    def build_query(self, request: QueryRequest) -> tuple[str, list[Any]]:
        """Compile a declarative request into parameterized DuckDB SQL."""
        if not request.aggregations:
            raise QueryValidationError("At least one aggregation is required.")
        for column in request.group_by:
            self._require_column(column)
        select_parts = [quote_identifier(column) for column in request.group_by]
        for aggregation in request.aggregations:
            self._require_column(aggregation.column)
            function = AGGREGATES[aggregation.function]
            alias = aggregation.alias or f"{aggregation.function}_{aggregation.column}"
            select_parts.append(f"{function}({quote_identifier(aggregation.column)}) AS {quote_identifier(alias)}")
        params: list[Any] = []
        conditions: list[str] = []
        for item in request.filters:
            self._require_column(item.column)
            column = quote_identifier(item.column)
            if item.operator == "eq":
                conditions.append(f"{column} = ?")
                params.append(item.value)
            elif item.operator == "in":
                values = list(item.value)
                if not values:
                    conditions.append("FALSE")
                else:
                    conditions.append(f"{column} IN ({','.join('?' for _ in values)})")
                    params.extend(values)
            elif item.operator == "between":
                conditions.append(f"{column} BETWEEN ? AND ?")
                params.extend([item.value, item.upper])
            elif item.operator == "gte":
                conditions.append(f"{column} >= ?")
                params.append(item.value)
            elif item.operator == "lte":
                conditions.append(f"{column} <= ?")
                params.append(item.value)
        sql = "SELECT " + ", ".join(select_parts) + " FROM dataset"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        if request.group_by:
            sql += " GROUP BY " + ", ".join(quote_identifier(column) for column in request.group_by)
        if request.sort_by:
            allowed_aliases = {a.alias or f"{a.function}_{a.column}" for a in request.aggregations} | set(request.group_by)
            if request.sort_by not in allowed_aliases:
                raise QueryValidationError("Sort column is not present in the query output.")
            sql += f" ORDER BY {quote_identifier(request.sort_by)} {'ASC' if request.ascending else 'DESC'}"
        sql += f" LIMIT {min(request.limit or self.max_rows, self.max_rows)}"
        return sql, params

    def execute(self, sql: str, params: list[Any] | None = None) -> QueryResult:
        """Execute SQL with an interrupt timer and return a copied DataFrame."""
        connection = duckdb.connect(database=":memory:")
        connection.register("dataset", self._frame)
        timed_out = threading.Event()

        def interrupt() -> None:
            timed_out.set()
            connection.interrupt()

        timer = threading.Timer(self.timeout_seconds, interrupt)
        started = time.perf_counter()
        timer.start()
        try:
            result = connection.execute(sql, params or []).fetchdf()
        except Exception as exc:
            message = "Query exceeded the execution timeout." if timed_out.is_set() else "The validated query could not be executed."
            LOGGER.exception("query_execution_failed", extra={"event": "query_execute", "status": "failed"})
            raise QueryExecutionError(message) from exc
        finally:
            timer.cancel()
            connection.close()
        elapsed = (time.perf_counter() - started) * 1000
        truncated = len(result) >= self.max_rows
        LOGGER.info("query_executed", extra={"event": "query_execute", "duration_ms": elapsed, "row_count": len(result), "status": "success"})
        return QueryResult(data=result.copy(deep=True), query=sql, execution_time_ms=elapsed, truncated=truncated)

    def aggregate(self, request: QueryRequest) -> QueryResult:
        """Compile and execute a declarative aggregation."""
        sql, params = self.build_query(request)
        return self.execute(sql, params)
