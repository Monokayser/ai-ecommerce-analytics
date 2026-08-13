"""Chart selection and construction tests."""

from __future__ import annotations

import pandas as pd

from src.visualization.chart_selector import select_chart
from src.visualization.charts import animated_chart, correlation_chart, distribution_chart, geographic_chart, grouped_bar_chart, hierarchy_chart, profit_terrain_chart, scatter_chart, three_dimensional_chart, time_series_chart


def test_chart_selection_rules():
    assert select_chart(pd.DataFrame({"value": [1]})).chart_type == "kpi"
    assert select_chart(pd.DataFrame({"month": pd.to_datetime(["2024-01-01"]), "Sales": [1]})).chart_type == "line"
    assert select_chart(pd.DataFrame({"Category": ["A", "B"], "Sales": [1, 2]})).chart_type == "bar"
    assert select_chart(pd.DataFrame({"x": [1, 2], "y": [3, 4]})).chart_type == "scatter"
    assert select_chart(pd.DataFrame({"Country": ["India"], "Sales": [1]})).chart_type == "map"


def test_all_required_chart_constructors(ecommerce_frame):
    figures = [time_series_chart(ecommerce_frame), geographic_chart(ecommerce_frame), correlation_chart(ecommerce_frame), distribution_chart(ecommerce_frame), hierarchy_chart(ecommerce_frame), grouped_bar_chart(ecommerce_frame), scatter_chart(ecommerce_frame), three_dimensional_chart(ecommerce_frame), profit_terrain_chart(ecommerce_frame), animated_chart(ecommerce_frame)]
    assert len(figures) == 10
    assert all(figure.data for figure in figures)
    assert figures[7].data[0].type == "scatter3d"
    assert figures[8].data[0].type == "surface"


def test_webgl_scatter_payload_is_bounded():
    frame = pd.DataFrame({"Discount": range(9001), "Profit": range(9001)})
    figure = scatter_chart(frame)
    assert figure.data[0].type == "scattergl"
    assert len(figure.data[0].x) == 8000


def test_interactive_chart_controls(ecommerce_frame):
    trend = time_series_chart(ecommerce_frame)
    grouped = grouped_bar_chart(ecommerce_frame)
    treemap = hierarchy_chart(ecommerce_frame, mode="treemap")
    animation_frame = ecommerce_frame.copy()
    animation_frame["Order Date"] = pd.to_datetime(["2023-01-01", "2023-02-01", "2024-01-01", "2024-02-01", "2025-01-01", "2025-02-01"])
    animated = animated_chart(animation_frame, metric="Profit")
    custom_3d = three_dimensional_chart(ecommerce_frame, axes=("Quantity", "Discount", "Profit"), color_field="Region")

    assert trend.layout.xaxis.rangeslider.visible is True
    assert len(trend.layout.xaxis.rangeselector.buttons) == 4
    assert len(grouped.layout.updatemenus[0].buttons) == 2
    assert treemap.data[0].type == "treemap"
    assert animated.frames
    assert animated.layout.height == 650
    assert animated.layout.sliders[0].currentvalue.prefix == "Year  "
    assert animated.data[0].textposition == "outside"
    assert custom_3d.data[0].type == "scatter3d"
    assert custom_3d.layout.scene.xaxis.title.text == "Quantity"
