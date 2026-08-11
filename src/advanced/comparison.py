"""Side-by-side subset comparison metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.models import ComparisonResult


def _metrics(frame: pd.DataFrame) -> dict[str, float]:
    sales = float(frame["Sales"].sum()) if "Sales" in frame else float("nan")
    profit = float(frame["Profit"].sum()) if "Profit" in frame else float("nan")
    orders = float(frame["Order ID"].nunique()) if "Order ID" in frame else float(len(frame))
    quantity = float(frame["Quantity"].sum()) if "Quantity" in frame else float("nan")
    return {
        "Sales": sales,
        "Profit": profit,
        "Order count": orders,
        "Quantity": quantity,
        "Average order value": sales / orders if orders else float("nan"),
        "Profit margin (%)": profit / sales * 100 if sales else float("nan"),
        "Average discount": float(frame["Discount"].mean()) if "Discount" in frame else float("nan"),
        "Sample rows": float(len(frame)),
    }


def compare_subsets(frame_a: pd.DataFrame, frame_b: pd.DataFrame, label_a: str, label_b: str) -> ComparisonResult:
    """Calculate comparable KPIs and percentage differences."""
    values_a, values_b = _metrics(frame_a), _metrics(frame_b)
    rows = []
    for metric in values_a:
        a, b = values_a[metric], values_b[metric]
        difference = b - a
        percent = difference / abs(a) * 100 if a and not np.isnan(a) else float("nan")
        rows.append({"Metric": metric, label_a: a, label_b: b, "Difference (B-A)": difference, "Difference (%)": percent})
    warnings = []
    smaller, larger = sorted([len(frame_a), len(frame_b)])
    if smaller == 0:
        warnings.append("One comparison subset is empty; interpretation is limited.")
    elif larger / smaller >= 1.5:
        warnings.append("Subset sample sizes differ materially; totals should be interpreted alongside averages.")
    detail = pd.concat([frame_a.assign(_comparison_group=label_a), frame_b.assign(_comparison_group=label_b)], ignore_index=True)
    return ComparisonResult(metrics=pd.DataFrame(rows), detail=detail, label_a=label_a, label_b=label_b, warnings=warnings)


def comparison_narrative(result: ComparisonResult) -> str:
    """Create a concise computed comparative narrative."""
    sales_row = result.metrics.loc[result.metrics["Metric"] == "Sales"].iloc[0]
    stronger = result.label_b if sales_row[result.label_b] > sales_row[result.label_a] else result.label_a
    caution = " ".join(result.warnings) if result.warnings else "Sample sizes are shown for context."
    return f"Observed fact: {stronger} has higher total Sales in the selected subsets. {caution} This comparison is descriptive and does not establish causation."
