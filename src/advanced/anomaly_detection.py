"""IQR and Isolation Forest anomaly detection."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.models import AnomalyResult
from src.utils.exceptions import SchemaValidationError


def detect_anomalies(
    frame: pd.DataFrame,
    target: str,
    *,
    method: str = "IQR",
    contamination: float = 0.05,
    grouping: str | None = None,
) -> AnomalyResult:
    """Detect anomalies globally or within categories without changing source data."""
    if target not in frame or not pd.api.types.is_numeric_dtype(frame[target]):
        raise SchemaValidationError("Select an available numeric anomaly target.")
    if not 0.001 <= contamination <= 0.5:
        raise ValueError("Contamination must be between 0.001 and 0.5.")
    data = frame.copy(deep=True)
    data["is_anomaly"] = False

    def mark(group: pd.DataFrame) -> pd.Series:
        values = group[target]
        valid = values.notna()
        flags = pd.Series(False, index=group.index)
        if valid.sum() < 4:
            return flags
        if method.lower().startswith("iqr"):
            q1, q3 = values[valid].quantile([0.25, 0.75])
            iqr = q3 - q1
            flags.loc[valid] = (values[valid] < q1 - 1.5 * iqr) | (values[valid] > q3 + 1.5 * iqr)
        elif method.lower().startswith("isolation"):
            model = IsolationForest(contamination=contamination, random_state=42, n_estimators=150)
            flags.loc[valid] = model.fit_predict(values[valid].to_numpy().reshape(-1, 1)) == -1
        else:
            raise ValueError("Method must be IQR or Isolation Forest.")
        return flags

    if grouping and grouping in data:
        for _, group in data.groupby(grouping, dropna=False):
            data.loc[group.index, "is_anomaly"] = mark(group)
    else:
        data["is_anomaly"] = mark(data)
    count = int(data["is_anomaly"].sum())
    return AnomalyResult(data=data, total_anomalies=count, anomaly_percent=count / max(len(data), 1) * 100, method=method, target=target)


def anomaly_explanation(result: AnomalyResult) -> str:
    """Return a fact-first explanation usable without an LLM."""
    return (
        f"Observed fact: {result.total_anomalies} rows ({result.anomaly_percent:.2f}%) were flagged in {result.target} using {result.method}. "
        "Possible interpretations include unusual orders, promotional effects, returns, or data-quality issues; further validation is required."
    )
