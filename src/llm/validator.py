"""AST-based read-only SQL validation."""

from __future__ import annotations

import sqlglot
from sqlglot import exp

from src.utils.exceptions import UnsafeQueryError

FORBIDDEN_FUNCTIONS = {
    "read_csv", "read_csv_auto", "read_json", "read_json_auto", "read_parquet",
    "parquet_scan", "csv_scan", "glob", "httpfs", "sqlite_scan", "postgres_scan",
    "query", "getenv", "current_setting",
}


def validate_sql(sql: str, *, allowed_table: str = "dataset", max_rows: int = 1000) -> str:
    """Validate one SELECT/CTE query and apply an outer result limit."""
    if not sql or len(sql) > 20_000:
        raise UnsafeQueryError("Generated SQL is empty or too long.")
    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except sqlglot.errors.ParseError as exc:
        raise UnsafeQueryError("Generated SQL could not be parsed.") from exc
    if len(statements) != 1 or statements[0] is None:
        raise UnsafeQueryError("Exactly one SQL statement is required.")
    statement = statements[0]
    if not isinstance(statement, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise UnsafeQueryError("Only SELECT or WITH queries are permitted.")
    prohibited_nodes = (
        exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter,
        exp.Command, exp.Copy, exp.Merge, exp.Transaction, exp.Use,
    )
    if any(statement.find(node) is not None for node in prohibited_nodes):
        raise UnsafeQueryError("The query contains a prohibited SQL operation.")
    cte_names = {cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)}
    for table in statement.find_all(exp.Table):
        name = table.name.lower()
        if name not in {allowed_table.lower(), *cte_names}:
            raise UnsafeQueryError(f"Query may only read the '{allowed_table}' table.")
        if table.args.get("catalog") or table.args.get("db"):
            raise UnsafeQueryError("Catalog and schema-qualified table access is prohibited.")
    for function in statement.find_all(exp.Func):
        name = function.sql_name().lower()
        if name in FORBIDDEN_FUNCTIONS:
            raise UnsafeQueryError(f"Function '{name}' is prohibited.")
    normalized = statement.sql(dialect="duckdb")
    return f"SELECT * FROM ({normalized}) AS safe_result LIMIT {int(max_rows)}"
