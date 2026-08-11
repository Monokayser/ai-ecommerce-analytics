"""Data-quality profiling and validation metrics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def iqr_outlier_count(series: pd.Series) -> int:
    """Count values outside 1.5 IQR fences."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return 0
    q1, q3 = numeric.quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((numeric < lower) | (numeric > upper)).sum())


def profile_quality(frame: pd.DataFrame) -> dict[str, Any]:
    """Return comprehensive serializable data-quality metrics."""
    missing = pd.DataFrame({"missing_count": frame.isna().sum(), "missing_percent": frame.isna().mean() * 100})
    numeric_columns = list(frame.select_dtypes(include=np.number).columns)
    category_columns = list(frame.select_dtypes(include=["object", "string", "category"]).columns)
    invalid_dates: dict[str, int] = {}
    for column in [c for c in frame.columns if "date" in c.lower()]:
        invalid_dates[column] = int((pd.to_datetime(frame[column], errors="coerce").isna() & frame[column].notna()).sum())
    profit_sales = None
    if {"Profit", "Sales"}.issubset(frame.columns):
        valid = frame.loc[frame["Sales"].ne(0), ["Profit", "Sales"]]
        profit_sales = {
            "profit_margin_percent": float(valid["Profit"].sum() / valid["Sales"].sum() * 100) if valid["Sales"].sum() else None,
            "negative_profit_rows": int((frame["Profit"] < 0).sum()),
        }
    return {
        "rows": len(frame),
        "columns": len(frame.columns),
        "missing": missing.reset_index(names="column").to_dict("records"),
        "duplicate_rows": int(frame.duplicated().sum()),
        "duplicate_order_ids": int(frame["Order ID"].duplicated().sum()) if "Order ID" in frame else None,
        "numeric_statistics": frame[numeric_columns].describe().to_dict() if numeric_columns else {},
        "categorical_frequencies": {column: frame[column].value_counts(dropna=False).head(10).to_dict() for column in category_columns},
        "iqr_outliers": {column: iqr_outlier_count(frame[column]) for column in numeric_columns},
        "invalid_dates": invalid_dates,
        "negative_sales": int((frame["Sales"] < 0).sum()) if "Sales" in frame else None,
        "negative_quantity": int((frame["Quantity"] < 0).sum()) if "Quantity" in frame else None,
        "discount_outside_0_1": int(((frame["Discount"] < 0) | (frame["Discount"] > 1)).sum()) if "Discount" in frame else None,
        "profit_sales_relationship": profit_sales,
        "constant_columns": [column for column in frame.columns if frame[column].nunique(dropna=False) <= 1],
        "high_cardinality_columns": [column for column in frame.columns if frame[column].nunique(dropna=True) / max(len(frame), 1) > 0.8],
    }
