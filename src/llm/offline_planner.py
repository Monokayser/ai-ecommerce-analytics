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

FOLLOW_UP_PREFIXES = (
    "and ",
    "also ",
    "now ",
    "same ",
    "what about",
    "how about",
    "break that",
    "compare that",
    "show that",
)


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
        explicit = self._dimensions(question)
        if explicit:
            return explicit[0]
        preferred = next((column for column in ("Region", "Product Category", "Country", "Customer Segment") if column in self.columns), None)
        if preferred:
            return preferred
        categorical = self.frame.select_dtypes(include=["object", "string", "category", "bool"]).columns
        return next((column for column in categorical if self.frame[column].nunique(dropna=True) <= 100), None)

    def _dimensions(self, question: str) -> list[str]:
        """Return up to two explicitly requested dimensions in question order."""
        found: list[tuple[int, str]] = []
        for column, terms in DIMENSION_TERMS.items():
            if column not in self.columns:
                continue
            positions = [question.find(term) for term in terms if term in question]
            if positions:
                found.append((min(positions), column))
        categorical = set(self.frame.select_dtypes(include=["object", "string", "category", "bool"]).columns)
        for column in categorical:
            label = str(column).casefold().replace("_", " ")
            if label and label in question and column not in {item[1] for item in found}:
                found.append((question.find(label), column))
        return [column for _position, column in sorted(found)[:2]]

    def _metric(self, question: str) -> str | None:
        explicit = self._metrics(question)
        if explicit:
            return explicit[0]
        preferred = next((column for column in ("Sales", "Profit", "Quantity") if column in self.columns), None)
        if preferred:
            return preferred
        return next(iter(self.frame.select_dtypes(include="number").columns), None)

    def _metrics(self, question: str) -> list[str]:
        """Return up to three explicitly requested numeric measures in question order."""
        numeric = set(self.frame.select_dtypes(include="number").columns)
        found: list[tuple[int, str]] = []
        for column, terms in METRIC_TERMS.items():
            if column not in self.columns:
                continue
            positions = [question.find(term) for term in terms if term in question]
            if positions:
                found.append((min(positions), column))
        for column in numeric:
            label = str(column).casefold().replace("_", " ")
            if label and label in question and column not in {item[1] for item in found}:
                found.append((question.find(label), column))
        return [column for _position, column in sorted(found)[:3]]

    def _contextualize(self, question: str, history: str) -> str:
        """Resolve short follow-ups locally without letting history override the new request."""
        normalized = " ".join(question.casefold().split())
        if not history or not normalized.startswith(FOLLOW_UP_PREFIXES):
            return normalized
        previous = [line[3:].strip().casefold() for line in history.splitlines() if line.startswith("Q: ")]
        if not previous:
            return normalized
        prior = previous[-1]
        additions: list[str] = []
        if not self._dimensions(normalized):
            additions.extend(self._dimensions(prior))
        if not self._metrics(normalized):
            additions.extend(self._metrics(prior))
        return " ".join([normalized, *(str(value).casefold() for value in additions)])

    @staticmethod
    def _steps(*steps: str) -> list[str]:
        return list(steps)

    def _matched_values(self, column: str, question: str) -> list[str]:
        values = [str(value) for value in self.frame[column].dropna().unique()[:500]]
        return [value for value in values if re.search(rf"\b{re.escape(value.lower())}\b", question)]

    def plan(self, question: str, *, history: str = "") -> GeneratedQuery:
        """Return a safe, explainable plan for frequent analytical intents."""
        normalized = self._contextualize(question, history)
        if not normalized:
            raise LLMResponseError("Enter a question about the active dataset.")

        if any(term in normalized for term in ("data quality", "missing", "null", "completeness", "duplicate")):
            profiled = list(self.frame.columns)[:20]
            select = ["COUNT(*) AS Row_Count"]
            for column in profiled:
                alias = quote_identifier(f"Missing {column}")
                select.append(f"COUNT(*) - COUNT({quote_identifier(column)}) AS {alias}")
            if self.columns:
                duplicate_columns = ", ".join(quote_identifier(column) for column in profiled)
                select.append(
                    "COUNT(*) - COUNT(DISTINCT (" + duplicate_columns + ")) AS Exact_Duplicate_Count"
                )
            return GeneratedQuery(
                interpreted_question="Profile missing values and exact duplicate records in the active dataset.",
                analysis_type="data_quality",
                plan_steps=self._steps("Count active rows", "Measure missing values by column", "Count exact duplicate records"),
                query=f"SELECT {', '.join(select)} FROM dataset",  # nosec B608
                columns_used=profiled,
                aggregation="DATA QUALITY PROFILE",
                recommended_chart="table",
                reason="A compact quality profile identifies incomplete or duplicated data before analysis.",
                suggested_followups=["Which columns have the most missing values?", "Summarize the active dataset."],
            )

        growth_terms = ("growth", "change rate", "month-over-month", "month over month", "mom", "year-over-year", "year over year", "yoy")
        if any(term in normalized for term in growth_terms) and self._has("Order Date"):
            metric = self._metric(normalized)
            if metric is None:
                raise LLMResponseError("A numeric measure is required for growth analysis.")
            grain = "year" if any(term in normalized for term in ("year-over-year", "year over year", "yoy", "annual")) else "month"
            q_date, q_metric = quote_identifier("Order Date"), quote_identifier(metric)
            total_alias = quote_identifier(f"Total {metric}")
            previous_alias = quote_identifier(f"Previous {metric}")
            growth_alias = quote_identifier(f"{metric} Growth Percent")
            sql = (
                f"WITH period_totals AS (SELECT DATE_TRUNC('{grain}', {q_date}) AS Period, "  # nosec B608
                f"SUM({q_metric}) AS {total_alias} FROM dataset WHERE {q_date} IS NOT NULL AND {q_metric} IS NOT NULL GROUP BY 1), "
                f"with_previous AS (SELECT Period, {total_alias}, LAG({total_alias}) OVER (ORDER BY Period) AS {previous_alias} FROM period_totals) "
                f"SELECT Period, {total_alias}, {previous_alias}, ROUND(100.0 * ({total_alias} - {previous_alias}) / "
                f"NULLIF(ABS({previous_alias}), 0), 2) AS {growth_alias} FROM with_previous ORDER BY Period"
            )
            return GeneratedQuery(
                interpreted_question=f"Calculate {grain}-over-{grain} {metric} growth across the active period.",
                analysis_type="growth",
                plan_steps=self._steps(f"Aggregate {metric} by {grain}", "Compare each period with its predecessor", "Calculate the percentage change"),
                query=sql,
                columns_used=["Order Date", metric],
                aggregation=f"SUM + LAG by {grain}",
                recommended_chart="line",
                reason="A period series with the prior value makes growth transparent and reproducible.",
                assumptions=[f"Growth is measured against the immediately preceding {grain} in the active data."],
                suggested_followups=[f"Which {grain} had the strongest {metric} growth?", f"Break {metric} growth down by region."],
            )

        if any(term in normalized for term in ("monthly", "month", "trend", "over time")) and self._has("Order Date"):
            measures = [column for column in ("Sales", "Profit", "Quantity") if column in self.columns and column.lower() in normalized]
            if not measures:
                measures = [column for column in ("Sales", "Profit") if column in self.columns]
            if not measures:
                raise LLMResponseError("A numeric measure is required for trend analysis.")
            grain = "year" if "year" in normalized and "month" not in normalized else "month"
            select = [f"DATE_TRUNC('{grain}', {quote_identifier('Order Date')}) AS Period"]
            select.extend(f"SUM({quote_identifier(column)}) AS {quote_identifier('Total ' + column)}" for column in measures)
            sql = f"SELECT {', '.join(select)} FROM dataset WHERE {quote_identifier('Order Date')} IS NOT NULL GROUP BY 1 ORDER BY 1"  # nosec B608
            return GeneratedQuery(
                interpreted_question=f"Show the {grain}ly trend for {', '.join(measures)}.",
                analysis_type="trend",
                plan_steps=self._steps(f"Group records by {grain}", f"Aggregate {', '.join(measures)}", "Order the periods chronologically"),
                query=sql,
                columns_used=["Order Date", *measures],
                aggregation="SUM by time period",
                recommended_chart="line",
                reason="A time series is the clearest way to show change over time.",
                suggested_followups=["Calculate period-over-period growth.", "Break this trend down by region."],
            )

        if any(term in normalized for term in ("correlation", "associated", "relationship", "correspond")):
            numeric = [column for column in ("Discount", "Profit", "Sales", "Quantity") if column in self.columns and column.lower() in normalized]
            if len(numeric) < 2 and self._has("Discount", "Profit"):
                numeric = ["Discount", "Profit"]
            if len(numeric) >= 2:
                first, second = numeric[:2]
                sql = (
                    f"SELECT {quote_identifier(first)}, {quote_identifier(second)} FROM dataset "  # nosec B608
                    f"WHERE {quote_identifier(first)} IS NOT NULL AND {quote_identifier(second)} IS NOT NULL"
                )
                return GeneratedQuery(
                    interpreted_question=f"Examine the relationship between {first} and {second}.",
                    analysis_type="relationship",
                    plan_steps=self._steps(f"Select paired {first} and {second} values", "Remove incomplete pairs", "Visualize the relationship without causal claims"),
                    query=sql,
                    columns_used=[first, second],
                    aggregation="CORRELATION / relationship inspection",
                    recommended_chart="scatter",
                    reason="The paired observations support a relationship plot without implying causation.",
                    assumptions=["Association does not establish causation."],
                    suggested_followups=[f"Compare average {second} across {first} quartiles.", "Check whether the pattern differs by region."],
                )

        if ("unusual" in normalized or "anomal" in normalized) and self._has("Discount", "Profit"):
            identifiers = [column for column in ("Order ID", "Region", "Product Category") if column in self.columns]
            selected = [*identifiers, "Discount", "Profit"]
            sql = (
                f"SELECT {', '.join(quote_identifier(column) for column in selected)} FROM dataset "  # nosec B608
                f"WHERE {quote_identifier('Profit')} < 0 AND {quote_identifier('Discount')} >= "
                f"(SELECT QUANTILE_CONT({quote_identifier('Discount')}, 0.75) FROM dataset) "
                f"ORDER BY {quote_identifier('Discount')} DESC, {quote_identifier('Profit')} ASC"
            )
            return GeneratedQuery(
                interpreted_question="Find loss-making orders with discounts in the top quartile.",
                analysis_type="anomaly",
                plan_steps=self._steps("Calculate the discount upper quartile", "Find high-discount loss records", "Rank the most material records"),
                query=sql,
                columns_used=selected,
                filters_used=["Profit < 0", "Discount >= dataset 75th percentile"],
                aggregation="FILTER",
                recommended_chart="scatter",
                reason="The rule identifies high-discount losses without changing the source data.",
                assumptions=["This is a transparent screening rule, not proof of a causal anomaly."],
                suggested_followups=["Which categories contain the most flagged records?", "Compare flagged and unflagged profit."],
            )

        dimensions = self._dimensions(normalized)
        explicit_dimension = dimensions[0] if dimensions else None
        dimension = explicit_dimension or self._dimension(normalized)
        metrics = self._metrics(normalized)
        metric = metrics[0] if metrics else self._metric(normalized)

        if metric and any(term in normalized for term in ("distribution", "median", "percentile", "quartile", "spread", "standard deviation")):
            q_metric = quote_identifier(metric)
            if explicit_dimension:
                q_dimension = quote_identifier(explicit_dimension)
                group_select, group_clause = f"{q_dimension}, ", f" GROUP BY {q_dimension} ORDER BY {q_dimension}"
                columns_used = [explicit_dimension, metric]
            else:
                group_select, group_clause = "", ""
                columns_used = [metric]
            sql = (
                f"SELECT {group_select}COUNT({q_metric}) AS Sample_Size, AVG({q_metric}) AS {quote_identifier('Average ' + metric)}, "  # nosec B608
                f"MEDIAN({q_metric}) AS {quote_identifier('Median ' + metric)}, STDDEV_SAMP({q_metric}) AS {quote_identifier('Std Dev ' + metric)}, "
                f"QUANTILE_CONT({q_metric}, 0.25) AS {quote_identifier('Q1 ' + metric)}, QUANTILE_CONT({q_metric}, 0.75) AS {quote_identifier('Q3 ' + metric)}, "
                f"MIN({q_metric}) AS {quote_identifier('Minimum ' + metric)}, MAX({q_metric}) AS {quote_identifier('Maximum ' + metric)} "
                f"FROM dataset WHERE {q_metric} IS NOT NULL{group_clause}"
            )
            return GeneratedQuery(
                interpreted_question=f"Describe the distribution of {metric}" + (f" by {explicit_dimension}." if explicit_dimension else "."),
                analysis_type="distribution",
                plan_steps=self._steps("Count usable observations", "Calculate center and spread", "Report quartiles and range"),
                query=sql,
                columns_used=columns_used,
                aggregation="DESCRIPTIVE STATISTICS",
                recommended_chart="table" if explicit_dimension else "histogram",
                reason="Descriptive statistics expose the center, spread, and range without changing the data.",
                suggested_followups=[f"Show unusual {metric} records.", f"Compare average {metric} by region."],
            )

        if dimension and metric and any(term in normalized for term in ("contribution", "share of", "percentage of", "mix")):
            q_dimension, q_metric = quote_identifier(dimension), quote_identifier(metric)
            total_alias = quote_identifier(f"Total {metric}")
            share_alias = quote_identifier(f"{metric} Share Percent")
            sql = (
                f"WITH grouped AS (SELECT {q_dimension}, SUM({q_metric}) AS {total_alias} FROM dataset "  # nosec B608
                f"WHERE {q_dimension} IS NOT NULL AND {q_metric} IS NOT NULL GROUP BY {q_dimension}) "
                f"SELECT {q_dimension}, {total_alias}, ROUND(100.0 * {total_alias} / NULLIF(SUM({total_alias}) OVER (), 0), 2) "
                f"AS {share_alias} FROM grouped ORDER BY {total_alias} DESC"
            )
            return GeneratedQuery(
                interpreted_question=f"Calculate each {dimension}'s contribution to total {metric}.",
                analysis_type="contribution",
                plan_steps=self._steps(f"Aggregate {metric} by {dimension}", "Calculate the active-data total", "Rank percentage contribution"),
                query=sql,
                columns_used=[dimension, metric],
                aggregation="SUM + PERCENT OF TOTAL",
                recommended_chart="bar",
                reason="Percentage contribution shows both absolute value and business mix.",
                suggested_followups=[f"Which {dimension} has the fastest growth?", f"Compare profit margin by {dimension}."],
            )

        if dimension and self._has("Sales", "Profit") and any(term in normalized for term in ("profit margin", "margin", "profitability")):
            q_dimension = quote_identifier(dimension)
            sql = (
                f"SELECT {q_dimension}, SUM({quote_identifier('Sales')}) AS {quote_identifier('Total Sales')}, "  # nosec B608
                f"SUM({quote_identifier('Profit')}) AS {quote_identifier('Total Profit')}, "
                f"ROUND(100.0 * SUM({quote_identifier('Profit')}) / NULLIF(SUM({quote_identifier('Sales')}), 0), 2) AS {quote_identifier('Profit Margin Percent')}, "
                f"COUNT(*) AS Sample_Size FROM dataset WHERE {q_dimension} IS NOT NULL GROUP BY {q_dimension} "
                f"ORDER BY {quote_identifier('Profit Margin Percent')} DESC"
            )
            return GeneratedQuery(
                interpreted_question=f"Compare sales, profit, and profit margin by {dimension}.",
                analysis_type="comparison",
                plan_steps=self._steps(f"Aggregate sales and profit by {dimension}", "Calculate protected profit margins", "Rank comparable groups"),
                query=sql,
                columns_used=[dimension, "Sales", "Profit"],
                aggregation="SUM + PROFIT MARGIN",
                recommended_chart="bar",
                reason="Sales, profit, margin, and sample size provide a balanced profitability comparison.",
                suggested_followups=[f"Which {dimension} has negative profit?", f"Show monthly profit margin for the leading {dimension}."],
            )

        if dimension and metric:
            group_dimensions = dimensions or [dimension]
            selected_metrics = metrics or [metric]
            quoted_dimensions = [quote_identifier(value) for value in group_dimensions]
            where_parts = [f"{value} IS NOT NULL" for value in quoted_dimensions]
            where_parts.extend(f"{quote_identifier(value)} IS NOT NULL" for value in selected_metrics)
            filters_used: list[str] = []
            for grouped_dimension, q_dimension in zip(group_dimensions, quoted_dimensions, strict=True):
                matches = self._matched_values(grouped_dimension, normalized)
                if matches:
                    where_parts.append(f"{q_dimension} IN ({', '.join(_literal(value) for value in matches)})")
                    filters_used.append(f"{grouped_dimension}: {', '.join(matches)}")
            dimension_sql = ", ".join(quoted_dimensions)

            if "loss" in normalized and "Profit" in selected_metrics:
                alias = "Total Profit"
                sql = (
                    f"SELECT {dimension_sql}, SUM({quote_identifier('Profit')}) AS {quote_identifier(alias)} FROM dataset "  # nosec B608
                    f"WHERE {' AND '.join(where_parts)} GROUP BY {dimension_sql} HAVING SUM({quote_identifier('Profit')}) < 0 "
                    f"ORDER BY {quote_identifier(alias)} ASC"
                )
                filters_used.append("Total Profit < 0")
                aggregation = "SUM with negative-profit filter"
                selected_metrics = ["Profit"]
            elif "average order value" in normalized and self._has("Sales", "Order ID"):
                alias = "Average Order Value"
                sql = (
                    f"SELECT {dimension_sql}, SUM({quote_identifier('Sales')}) / NULLIF(COUNT(DISTINCT {quote_identifier('Order ID')}), 0) "  # nosec B608
                    f"AS {quote_identifier(alias)} FROM dataset WHERE {' AND '.join(where_parts)} GROUP BY {dimension_sql} "
                    f"ORDER BY {quote_identifier(alias)} DESC"
                )
                selected_metrics = ["Sales"]
                aggregation = "AVG order value"
            else:
                function = "AVG" if any(term in normalized for term in ("average", "mean")) else "SUM"
                aliases = [("Average " if function == "AVG" else "Total ") + value for value in selected_metrics]
                descending_range = any(
                    term in normalized
                    for term in ("highest to lowest", "high to low", "largest to smallest", "most to least", "descending")
                )
                ascending_range = any(
                    term in normalized
                    for term in ("lowest to highest", "low to high", "smallest to largest", "least to most", "ascending")
                )
                descending = descending_range or (
                    not ascending_range and not any(term in normalized for term in ("lowest", "bottom", "least", "worst"))
                )
                order = "DESC" if descending else "ASC"
                if descending_range or ascending_range:
                    limit = self.max_rows
                elif any(term in normalized for term in ("top", "bottom", "highest", "lowest", "most", "least")):
                    default_n = 1 if any(term in normalized for term in ("highest", "lowest", "most", "least")) else 10
                    limit = _top_n(normalized, default=default_n)
                else:
                    limit = self.max_rows
                aggregate_sql = ", ".join(
                    f"{function}({quote_identifier(value)}) AS {quote_identifier(alias)}"
                    for value, alias in zip(selected_metrics, aliases, strict=True)
                )
                sql = (
                    f"SELECT {dimension_sql}, {aggregate_sql}, COUNT(*) AS Sample_Size FROM dataset "  # nosec B608
                    f"WHERE {' AND '.join(where_parts)} GROUP BY {dimension_sql} ORDER BY {quote_identifier(aliases[0])} {order} LIMIT {limit}"
                )
                aggregation = function
                if limit < self.max_rows:
                    filters_used.append(f"{order.lower()} top {limit}")
            ranking = any(term in normalized for term in ("top", "bottom", "highest", "lowest", "most", "least", "rank", "best", "worst"))
            return GeneratedQuery(
                interpreted_question=f"Compare {', '.join(selected_metrics)} by {', '.join(group_dimensions)}.",
                analysis_type="ranking" if ranking else "comparison",
                plan_steps=self._steps(
                    f"Group active records by {', '.join(group_dimensions)}",
                    f"Aggregate {', '.join(selected_metrics)}",
                    "Apply requested ranking and subset filters",
                ),
                query=sql,
                columns_used=list(dict.fromkeys([*group_dimensions, *selected_metrics, *( ["Order ID"] if "average order value" in normalized and "Order ID" in self.columns else [])])),
                filters_used=filters_used,
                aggregation=aggregation,
                recommended_chart="bar",
                reason="A grouped, sample-sized result answers the comparison directly.",
                suggested_followups=[
                    f"Show the monthly trend for the leading {group_dimensions[0]}.",
                    f"Compare profit margin by {group_dimensions[0]}.",
                ],
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
            analysis_type="summary",
            plan_steps=self._steps("Count active rows and orders", "Aggregate core business measures", "Return a compact executive summary"),
            query=f"SELECT {', '.join(select)} FROM dataset",  # nosec B608
            columns_used=(["Order ID"] if "Order ID" in self.columns else []) + measures,
            aggregation="SUMMARY",
            recommended_chart="table",
            reason="A compact computed summary is the safest fallback for a broad question.",
            assumptions=["A broad request is interpreted as an executive summary of the active data."],
            suggested_followups=["Which region has the highest total sales?", "Show monthly sales and profit growth.", "Check data quality."],
        )
