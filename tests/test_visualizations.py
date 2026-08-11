"""Chart selection and construction tests."""

from __future__ import annotations

import pandas as pd

from src.visualization.chart_selector import select_chart
from src.visualization.charts import animated_chart, correlation_chart, distribution_chart, geographic_chart, grouped_bar_chart, hierarchy_chart, scatter_chart, three_dimensional_chart, time_series_chart


def test_chart_selection_rules():
    assert select_chart(pd.DataFrame({"value": [1]})).chart_type == "kpi"
    assert select_chart(pd.DataFrame({"month": pd.to_datetime(["2024-01-01"]), "Sales": [1]})).chart_type == "line"
    assert select_chart(pd.DataFrame({"Category": ["A", "B"], "Sales": [1, 2]})).chart_type == "bar"
    assert select_chart(pd.DataFrame({"x": [1, 2], "y": [3, 4]})).chart_type == "scatter"
    assert select_chart(pd.DataFrame({"Country": ["India"], "Sales": [1]})).chart_type == "map"


def test_all_required_chart_constructors(ecommerce_frame):
    figures = [time_series_chart(ecommerce_frame), geographic_chart(ecommerce_frame), correlation_chart(ecommerce_frame), distribution_chart(ecommerce_frame), hierarchy_chart(ecommerce_frame), grouped_bar_chart(ecommerce_frame), scatter_chart(ecommerce_frame), three_dimensional_chart(ecommerce_frame), animated_chart(ecommerce_frame)]
    assert len(figures) == 9
    assert all(figure.data for figure in figures)
    assert figures[7].data[0].type == "scatter3d"


def test_webgl_scatter_payload_is_bounded():
    frame = pd.DataFrame({"Discount": range(9001), "Profit": range(9001)})
    figure = scatter_chart(frame)
    assert figure.data[0].type == "scattergl"
    assert len(figure.data[0].x) == 8000
