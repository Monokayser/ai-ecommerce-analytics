"""Eight-chart data exploration section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components import active_filter_text, render_empty
from src.ui.theme import render_section_intro
from src.visualization.charts import animated_chart, correlation_chart, distribution_chart, geographic_chart, grouped_bar_chart, hierarchy_chart, scatter_chart, three_dimensional_chart, time_series_chart


def render(frame: pd.DataFrame, filters: dict) -> None:
    """Render the complete visualization suite with feature gates."""
    render_section_intro("Explore patterns", "Data Exploration", "Nine linked interactive views—including a WebGL 3D insight space—respond to the same global filters.")
    if frame.empty:
        render_empty("No rows are available for exploration.")
        return
    context = active_filter_text(filters)
    st.caption("Switch views instantly; hover, zoom, select, and download directly from each chart toolbar.")
    tabs = st.tabs(["⌁ Trend", "◎ Geography", "▦ Correlation", "◇ Distribution", "◫ Hierarchy", "▥ Grouped Bar", "↗ Relationship", "◈ 3D Space", "▶ Animation"])
    with tabs[0]:
        if {"Order Date", "Sales"}.issubset(frame): st.plotly_chart(time_series_chart(frame, context), use_container_width=True)
        else: render_empty("Order Date and Sales are required for this chart.")
    with tabs[1]:
        if ("Country" in frame or "Region" in frame) and ("Sales" in frame or "Profit" in frame): st.plotly_chart(geographic_chart(frame, context), use_container_width=True)
        else: render_empty("A geographic field and numeric measure are required.")
    with tabs[2]:
        if len(frame.select_dtypes(include="number").columns) >= 2: st.plotly_chart(correlation_chart(frame, context), use_container_width=True)
        else: render_empty("At least two numeric columns are required.")
    with tabs[3]:
        metrics = [column for column in ("Sales", "Profit", "Quantity", "Discount") if column in frame]
        if metrics:
            metric = st.selectbox("Distribution metric", metrics)
            st.plotly_chart(distribution_chart(frame, metric, context), use_container_width=True)
        else: render_empty("No supported numeric measure is available.")
    with tabs[4]:
        if "Sales" in frame and any(column in frame for column in ("Region", "Product Category", "Sub-Category")): st.plotly_chart(hierarchy_chart(frame, context), use_container_width=True)
        else: render_empty("Hierarchy fields are unavailable.")
    with tabs[5]:
        dimensions = [column for column in ("Product Category", "Customer Segment", "Region") if column in frame]
        if dimensions:
            dimension = st.selectbox("Bar dimension", dimensions)
            st.plotly_chart(grouped_bar_chart(frame, dimension, context), use_container_width=True)
        else: render_empty("No comparison dimension is available.")
    with tabs[6]:
        if {"Discount", "Profit"}.issubset(frame): st.plotly_chart(scatter_chart(frame, context=context), use_container_width=True)
        else: render_empty("Discount and Profit are required.")
    with tabs[7]:
        supported_3d = [column for column in ("Sales", "Profit", "Discount", "Quantity") if column in frame]
        if len(supported_3d) >= 3:
            st.caption("Drag to rotate · scroll to zoom · double-click to reset the camera")
            st.plotly_chart(three_dimensional_chart(frame, context), use_container_width=True)
        else: render_empty("Three numeric measures are required for the 3D insight space.")
    with tabs[8]:
        if {"Order Date", "Sales"}.issubset(frame) and any(column in frame for column in ("Product Category", "Region")): st.plotly_chart(animated_chart(frame, context), use_container_width=True)
        else: render_empty("Order Date, Sales, and a category are required.")
