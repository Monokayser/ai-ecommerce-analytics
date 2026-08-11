"""Schema, cleaning, and profiling tests."""

from __future__ import annotations

import pandas as pd

from config.settings import Settings
from src.data.cleaner import clean_dataset
from src.data.profiler import iqr_outlier_count, profile_quality
from src.data.schema import canonicalize_columns, inspect_schema, load_aliases


def test_alias_date_numeric_and_cleaning_log():
    aliases = load_aliases(Settings().aliases_path)
    frame = pd.DataFrame({"revenue": ["10", "bad", "1000", "10", "10"], "date": ["2024-01-01", "bad", "2024-01-03", "2024-01-04", "2024-01-05"], "category": [" A ", "A", "B", "A", "A"]})
    cleaned, log, warnings, _ = clean_dataset(frame, aliases)
    assert {"Sales", "Order Date", "Product Category"}.issubset(cleaned.columns)
    assert cleaned["Sales"].isna().sum() == 1
    assert cleaned["Order Date"].isna().sum() == 1
    assert cleaned["Product Category"].iloc[0] == "A"
    assert any(item.operation == "parse_date" for item in log)
    assert any(column.startswith("_outlier_") for column in cleaned.columns)


def test_ambiguous_alias_not_silently_renamed():
    aliases = load_aliases(Settings().aliases_path)
    frame, mapping, warnings = canonicalize_columns(pd.DataFrame({"location": ["East"]}), aliases)
    assert "location" in frame
    assert warnings and mapping["location"] == "location"


def test_schema_and_quality_calculations(ecommerce_frame):
    frame = pd.concat([ecommerce_frame, ecommerce_frame.iloc[[0]]], ignore_index=True)
    frame.loc[1, "Profit"] = None
    schema = inspect_schema(frame)
    profit = next(item for item in schema.columns if item.name == "Profit")
    assert profit.missing_count == 1
    assert profit.semantic_role == "numeric measure"
    quality = profile_quality(frame)
    assert quality["duplicate_rows"] == 1
    assert quality["duplicate_order_ids"] == 1
    assert "Sales" in quality["iqr_outliers"]


def test_iqr_outlier_detection():
    assert iqr_outlier_count(pd.Series([10] * 20 + [1000])) == 1
