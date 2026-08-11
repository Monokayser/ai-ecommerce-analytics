"""Advanced analytics tests."""

from __future__ import annotations

import pandas as pd

from src.advanced.anomaly_detection import detect_anomalies
from src.advanced.comparison import compare_subsets


def test_iqr_and_isolation_forest_outputs():
    frame = pd.DataFrame({"Sales": [10.0] * 30 + [1000.0], "Region": ["East"] * 31})
    iqr = detect_anomalies(frame, "Sales", method="IQR")
    isolation = detect_anomalies(frame, "Sales", method="Isolation Forest", contamination=0.05)
    assert iqr.total_anomalies == 1
    assert isolation.total_anomalies >= 1
    assert "is_anomaly" in isolation.data


def test_comparison_metrics_and_unequal_subset_warning(ecommerce_frame):
    result = compare_subsets(ecommerce_frame.iloc[:1], ecommerce_frame.iloc[1:], "A", "B")
    assert {"Metric", "A", "B", "Difference (%)"}.issubset(result.metrics.columns)
    assert result.warnings
    assert len(result.detail) == len(ecommerce_frame)
