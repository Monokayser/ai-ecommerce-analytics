"""SQL and pandas sandbox regression tests."""

from __future__ import annotations

import pytest

from src.llm.sandbox import PandasInterpreter
from src.llm.validator import validate_sql
from src.utils.exceptions import UnsafeQueryError


def test_valid_select_and_cte_accepted():
    assert "safe_result" in validate_sql("SELECT Region, SUM(Sales) FROM dataset GROUP BY Region")
    assert "safe_result" in validate_sql("WITH totals AS (SELECT Region, SUM(Sales) s FROM dataset GROUP BY Region) SELECT * FROM totals")


@pytest.mark.parametrize("sql", [
    "DROP TABLE dataset", "DELETE FROM dataset", "UPDATE dataset SET Sales=0", "INSERT INTO dataset VALUES (1)",
    "SELECT * FROM dataset; SELECT 1", "COPY dataset TO 'x.csv'", "SELECT * FROM read_csv_auto('secret.csv')",
    "SELECT * FROM other_table", "ATTACH 'secret.db' AS x", "INSTALL httpfs", "PRAGMA version",
    "SELECT * FROM dataset WHERE EXISTS (SELECT 1 FROM read_parquet('secret.parquet'))",
    "SELECT * FROM dataset JOIN sqlite_scan('secret.db', 'users') AS users ON TRUE",
    "EXPORT DATABASE 'backup'", "CALL load_extension('httpfs')",
])
def test_unsafe_sql_rejected(sql):
    with pytest.raises(UnsafeQueryError):
        validate_sql(sql)


def test_safe_pandas_expression(ecommerce_frame):
    result = PandasInterpreter(ecommerce_frame).execute("dataset.groupby('Region').agg({'Sales': 'sum'}).reset_index()")
    assert set(result.data.columns) == {"Region", "Sales"}


@pytest.mark.parametrize("expression", [
    "__import__('os').system('whoami')", "open('secret.txt').read()", "dataset.__class__", "dataset.to_csv('x.csv')",
    "eval('1+1')", "os.system('dir')", "requests.get('https://example.com')", "dataset[dataset['Sales'] > 10]",
])
def test_unsafe_pandas_rejected(ecommerce_frame, expression):
    with pytest.raises(UnsafeQueryError):
        PandasInterpreter(ecommerce_frame).execute(expression)
