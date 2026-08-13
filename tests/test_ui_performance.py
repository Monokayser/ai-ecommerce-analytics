"""Regression tests for rerun and interaction performance safeguards."""

from __future__ import annotations

import pandas as pd
from pathlib import Path

from src.ui.sidebar import apply_filters, build_filter_profile


def test_filter_profile_precomputes_widget_metadata(ecommerce_frame):
    profile = build_filter_profile(ecommerce_frame)

    assert profile["options"]["Region"] == ["East", "North", "South", "West"]
    assert profile["date_bounds"] == (pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-03-02").date())
    assert profile["numeric_bounds"]["Sales"] == (80.0, 900.0)


def test_filters_use_one_result_copy_and_preserve_source(ecommerce_frame):
    original = ecommerce_frame.copy(deep=True)
    result = apply_filters(
        ecommerce_frame,
        {"Region": ["East", "West"], "Sales": (100.0, 900.0)},
    )

    assert result["Order ID"].tolist() == ["A", "B", "C", "E"]
    result.loc[0, "Sales"] = -1
    pd.testing.assert_frame_equal(ecommerce_frame, original)


def test_exploration_and_advanced_views_are_lazy_rendered():
    exploration = Path("src/ui/exploration.py").read_text(encoding="utf-8")
    advanced = Path("src/ui/advanced_analytics.py").read_text(encoding="utf-8")

    assert "st.segmented_control" in exploration
    assert "st.tabs" not in exploration
    assert "st.segmented_control" in advanced
    assert "st.tabs" not in advanced
