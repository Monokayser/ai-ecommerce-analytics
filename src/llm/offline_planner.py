"""Deterministic natural-language planner used when no external LLM is configured."""

from __future__ import annotations

import re

import pandas as pd

from src.data.query_engine import quote_identifier
from src.models import GeneratedQuery
from src.utils.exceptions import LLMResponseError


NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "twenty": 20,
}

DIMENSION_TERMS = {
    "Sub-Category": ("sub-category", "sub category", "subcategory"),
    "Product Category": ("product category", "categories", "category"),
    "Customer Segment": ("customer segment", "segments", "segment"),
    "Ship Mode": ("ship mode", "shipping mode", "delivery mode"),
    "Country": ("countries", "country"),
    "Region": ("regions", "region"),
    "City": ("cities", "city"),
    "Order ID": ("orders", "order"),
}

METRIC_TERMS = {
    "Profit": ("profit", "profitable", "loss", "losses", "margin"),
    "Sales": ("sales", "revenue", "order value"),
    "Quantity": ("quantity", "units", "volume"),
    "Discount": ("discount", "markdown", "rebate"),
}


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _top_n(question: str, default: int = 10) -> int:
    match = re.search(r"\b(?:top|bottom|first|last)\s+(\d+)\b", question)
    if match:
        return min(max(int(match.group(1)), 1), 50)
    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b(?:top|bottom|first|last)?\s*{word}\b", question):
            return value
    return default


class OfflineQueryPlanner:
    """Translate common e-commerce questions into validated DuckDB SQL."""

    def __init__(self, frame: pd.DataFrame, *, max_rows: int = 1000) -> None:
        self.frame = frame
        self.columns = set(frame.columns)
        self.max_rows = max_rows

    def _has(self, *columns: str) -> bool:
        return all(column in self.columns for column in columns)

    def _dimension(self, question: str) -> str | None:
        for column, terms in DIMENSION_TERMS.items():
            if column in self.columns and any(term in question for term in terms):
                return column
        return next((column for column in ("Region", "Product Category", "Country", "Customer Segment") if column in self.columns), None)

    def _metric(self, question: str) -> str | None:
        for column, terms in METRIC_TERMS.items():
            if column in self.columns and any(term in question for term in terms):
                return column
        return next((column for column in ("Sales", "Profit", "Quantity") if column in self.columns), None)

    def _matched_values(self, column: str, question: str) -> list[str]:
        values = [str(value) for value in self.frame[column].dropna().unique()[:500]]
        return [value for value in values if re.search(rf"\b{re.escape(value.lower())}\b", question)]

    def plan(self, question: str) -> GeneratedQuery:
        """Return a safe, explainable plan for frequent analytical intents."""
        normalized = " ".join(question.lower().split())
        if not normalized:
            raise LLMResponseError("Enter a question about the active dataset.")

        if any(term in normalized for term in ("monthly", "month", "trend", "over time")) and self._has("Order Date"):
            measures = [column for column in ("Sales", "Profit", "Quantity") if column in self.columns and column.lower() in normalized]
            if not measures:
                measures = [column for column in ("Sales", "Profit") if column in self.columns]
            if not measures:
                raise LLMResponseError("A numeric measure is required for trend analysis.")
            grain = "year" if "year" in normalized and "month" not in normalized else "month"
            select = [f"DATE_TRUNC('{grain}', {quote_identifier('Order Date')}) AS Period"]
            select.extend(f"SUM({quote_identifier(column)}) AS {quote_identifier('Total ' + column)}" for column in measures)
            sql = f"SELECT {', '.join(select)} FROM dataset WHERE {quote_identifier('Order Date')} IS NOT NULL GROUP BY 1 ORDER BY 1"
            return GeneratedQuery(
                interpreted_question=f"Show the {grain}ly trend for {', '.join(measures)}.",
                query=sql,
                columns_used=["Order Date", *measures],
                aggregation="SUM by time period",
                recommended_chart="line",
                reason="A time series is the clearest way to show change over time.",
            )

        if any(term in normalized for term in ("correlation", "associated", "relationship", "correspond")):
            numeric = [column for column in ("Discount", "Profit", "Sales", "Quantity") if column in self.columns and column.lower() in normalized]
            if len(numeric) < 2 and self._has("Discount", "Profit"):
                numeric = ["Discount", "Profit"]
            if len(numeric) >= 2:
                first, second = numeric[:2]
                sql = (
                    f"SELECT {quote_identifier(first)}, {quote_identifier(second)} FROM dataset "
                    f"WHERE {quote_identifier(first)} IS NOT NULL AND {quote_identifier(second)} IS NOT NULL"
                )
                return GeneratedQuery(
                    interpreted_question=f"Examine the relationship between {first} and {second}.",
                    query=sql,
                    columns_used=[first, second],
                    aggregation="CORRELATION / relationship inspection",
                    recommended_chart="scatter",
                    reason="The paired observations support a relationship plot without implying causation.",
                )

        if ("unusual" in normalized or "anomal" in normalized) and self._has("Discount", "Profit"):
            identifiers = [column for column in ("Order ID", "Region", "Product Category") if column in self.columns]
            selected = [*identifiers, "Discount", "Profit"]
            sql = (
                f"SELECT {', '.join(quote_identifier(column) for column in selected)} FROM dataset "
                f"WHERE {quote_identifier('Profit')} < 0 AND {quote_identifier('Discount')} >= "
                f"(SELECT QUANTILE_CONT({quote_identifier('Discount')}, 0.75) FROM dataset) "
                f"ORDER BY {quote_identifier('Discount')} DESC, {quote_identifier('Profit')} ASC"
            )
            return GeneratedQuery(
                interpreted_question="Find loss-making orders with discounts in the top quartile.",
                query=sql,
                columns_used=selected,
                filters_used=["Profit < 0", "Discount >= dataset 75th percentile"],
                aggregation="FILTER",
                recommended_chart="scatter",
                reason="The rule identifies high-discount losses without changing the source data.",
            )

        dimension = self._dimension(normalized)
        metric = self._metric(normalized)
        if dimension and metric:
            q_dimension = quote_identifier(dimension)
            q_metric = quote_identifier(metric)
            matches = self._matched_values(dimension, normalized)
            where_parts = [f"{q_dimension} IS NOT NULL", f"{q_metric} IS NOT NULL"]
            filters_used: list[str] = []
            if matches:
                where_parts.append(f"{q_dimension} IN ({', '.join(_literal(value) for value in matches)})")
                filters_used.append(f"{dimension}: {', '.join(matches)}")

            if "loss" in normalized and metric == "Profit":
                alias = "Total Profit"
                sql = (
                    f"SELECT {q_dimension}, SUM({q_metric}) AS {quote_identifier(alias)} FROM dataset "
                    f"WHERE {' AND '.join(where_parts)} GROUP BY {q_dimension} HAVING SUM({q_metric}) < 0 "
                    f"ORDER BY {quote_identifier(alias)} ASC"
                )
                filters_used.append("Total Profit < 0")
                aggregation = "SUM with negative-profit filter"
            elif "average order value" in normalized and self._has("Sales", "Order ID"):
                alias = "Average Order Value"
                sql = (
                    f"SELECT {q_dimension}, SUM({quote_identifier('Sales')}) / NULLIF(COUNT(DISTINCT {quote_identifier('Order ID')}), 0) "
                    f"AS {quote_identifier(alias)} FROM dataset WHERE {' AND '.join(where_parts)} GROUP BY {q_dimension} "
                    f"ORDER BY {quote_identifier(alias)} DESC"
                )
                metric = "Sales"
                aggregation = "AVG order value"
            else:
                function = "AVG" if any(term in normalized for term in ("average", "mean")) else "SUM"
                alias = ("Average " if function == "AVG" else "Total ") + metric
                descending = not any(term in normalized for term in ("lowest", "bottom", "least", "worst"))
                order = "DESC" if descending else "ASC"
                default_n = 1 if any(term in normalized for term in ("highest", "lowest")) else 10
                limit = _top_n(normalized, default=default_n) if any(term in normalized for term in ("top", "bottom", "highest", "lowest", "most", "least")) else self.max_rows
                sql = (
                    f"SELECT {q_dimension}, {function}({q_metric}) AS {quote_identifier(alias)} FROM dataset "
                    f"WHERE {' AND '.join(where_parts)} GROUP BY {q_dimension} ORDER BY {quote_identifier(alias)} {order} LIMIT {limit}"
                )
                aggregation = function
                if limit < self.max_rows:
                    filters_used.append(f"{order.lower()} top {limit}")
            return GeneratedQuery(
                interpreted_question=f"Compare {metric} by {dimension}.",
                query=sql,
                columns_used=list(dict.fromkeys([dimension, metric, *( ["Order ID"] if "average order value" in normalized and "Order ID" in self.columns else [])])),
                filters_used=filters_used,
                aggregation=aggregation,
                recommended_chart="bar",
                reason="A grouped ranking answers the comparison directly.",
            )

        measures = [column for column in ("Sales", "Profit", "Quantity", "Discount") if column in self.columns]
        select = ["COUNT(*) AS Row_Count"]
        if "Order ID" in self.columns:
            select.append(f"COUNT(DISTINCT {quote_identifier('Order ID')}) AS Order_Count")
        select.extend(f"SUM({quote_identifier(column)}) AS {quote_identifier('Total ' + column)}" for column in measures if column != "Discount")
        if "Discount" in measures:
            select.append(f"AVG({quote_identifier('Discount')}) AS {quote_identifier('Average Discount')}")
        return GeneratedQuery(
            interpreted_question="Summarize the active dataset using core business metrics.",
            query=f"SELECT {', '.join(select)} FROM dataset",
            columns_used=(["Order ID"] if "Order ID" in self.columns else []) + measures,
            aggregation="SUMMARY",
            recommended_chart="table",
            reason="A compact computed summary is the safest fallback for a broad question.",
        )
