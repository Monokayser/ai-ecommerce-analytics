"""Restricted pandas-expression interpreter with no eval or exec."""

from __future__ import annotations

import ast
from typing import Any

import pandas as pd

from src.models import QueryResult
from src.utils.exceptions import QueryExecutionError, UnsafeQueryError

ALLOWED_METHODS = {
    "groupby", "agg", "sum", "mean", "median", "min", "max", "std", "count",
    "sort_values", "head", "tail", "reset_index", "value_counts", "nlargest", "nsmallest",
    "dropna", "fillna", "rename", "round",
}
ALLOWED_KEYWORDS = {"as_index", "ascending", "by", "dropna", "name", "columns"}
MAX_AST_NODES = 120


class PandasInterpreter:
    """Interpret a tiny DataFrame expression grammar against one copied dataset."""

    def __init__(self, frame: pd.DataFrame, max_rows: int = 1000) -> None:
        self.frame = frame.copy(deep=True)
        self.max_rows = max_rows

    def execute(self, expression: str) -> QueryResult:
        """Parse, validate, and interpret a single safe expression."""
        import time

        started = time.perf_counter()
        if len(expression) > 10_000:
            raise UnsafeQueryError("Pandas expression is too long.")
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise UnsafeQueryError("Pandas expression could not be parsed.") from exc
        if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
            raise UnsafeQueryError("Pandas expression is too complex.")
        result = self._visit(tree.body)
        if isinstance(result, pd.Series):
            result = result.reset_index(name=result.name or "value")
        elif not isinstance(result, pd.DataFrame):
            result = pd.DataFrame({"value": [result]})
        result = result.head(self.max_rows).copy(deep=True)
        return QueryResult(data=result, query=expression, execution_time_ms=(time.perf_counter() - started) * 1000, truncated=len(result) >= self.max_rows)

    def _visit(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Name):
            if node.id != "dataset":
                raise UnsafeQueryError("Only the dataset variable is available.")
            return self.frame
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (str, int, float, bool, type(None))):
                return node.value
            raise UnsafeQueryError("Unsupported literal.")
        if isinstance(node, (ast.List, ast.Tuple)):
            values = [self._visit(item) for item in node.elts]
            return values if isinstance(node, ast.List) else tuple(values)
        if isinstance(node, ast.Dict):
            return {self._visit(k): self._visit(v) for k, v in zip(node.keys, node.values, strict=True)}
        if isinstance(node, ast.Subscript):
            target = self._visit(node.value)
            key = self._visit(node.slice)
            if not isinstance(target, (pd.DataFrame, pd.Series)) or not isinstance(key, (str, list, tuple)):
                raise UnsafeQueryError("Only literal column selection is permitted.")
            requested = [key] if isinstance(key, str) else list(key)
            if any(not isinstance(item, str) or item not in self.frame.columns for item in requested):
                raise UnsafeQueryError("Unknown or invalid column selection.")
            return target[key]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method not in ALLOWED_METHODS:
                raise UnsafeQueryError(f"Pandas method '{method}' is not allowed.")
            target = self._visit(node.func.value)
            if not isinstance(target, (pd.DataFrame, pd.Series)) and "GroupBy" not in type(target).__name__:
                raise UnsafeQueryError("Method target is not a safe pandas object.")
            args = [self._visit(arg) for arg in node.args]
            kwargs: dict[str, Any] = {}
            for keyword in node.keywords:
                if keyword.arg not in ALLOWED_KEYWORDS:
                    raise UnsafeQueryError(f"Keyword '{keyword.arg}' is not allowed.")
                kwargs[keyword.arg] = self._visit(keyword.value)
            try:
                return getattr(target, method)(*args, **kwargs)
            except Exception as exc:
                raise QueryExecutionError("The restricted pandas expression failed.") from exc
        raise UnsafeQueryError(f"Pandas syntax '{type(node).__name__}' is not allowed.")
