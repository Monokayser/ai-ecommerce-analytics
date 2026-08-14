"""Lazy-rendered nine-chart data exploration section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components import active_filter_text, render_empty
from src.ui.theme import render_section_intro
from src.visualization.charts import animated_chart, correlation_chart, distribution_chart, geographic_chart, grouped_bar_chart, hierarchy_chart, profit_terrain_chart, scatter_chart, three_dimensional_chart, time_series_chart


def render(frame: pd.DataFrame, filters: dict) -> None:
    """Render the complete visualization suite with feature gates."""
    with st.container(key="exploration_workspace"):
        _render_workspace(frame, filters)


def _render_workspace(frame: pd.DataFrame, filters: dict) -> None:
    """Render the exploration workspace inside its responsive layout scope."""
    render_section_intro("Explore patterns", "Data Exploration", "Nine linked visualization workspaces—including relationship-cloud and aggregated profit-terrain 3D modes—respond to the same global filters.")
    if frame.empty:
        render_empty("No rows are available for exploration.")
        return
    context = active_filter_text(filters)
    st.caption("Switch views instantly; hover, zoom, drill, animate, switch analytical modes, and download from each chart toolbar.")
    views = ["Trend", "Geography", "Correlation", "Distribution", "Hierarchy", "Grouped Bar", "Relationship", "3D Space", "Animation"]
    view = st.segmented_control(
        "Visualization view",
        views,
        default="Trend",
        required=True,
        key="exploration_view",
        width="stretch",
        help="Only the selected visualization is rendered, keeping interactions fast on large datasets.",
    )
    if view == "Trend":
        if {"Order Date", "Sales"}.issubset(frame): st.plotly_chart(time_series_chart(frame, context), width="stretch")
        else: render_empty("Order Date and Sales are required for this chart.")
    elif view == "Geography":
        if ("Country" in frame or "Region" in frame) and ("Sales" in frame or "Profit" in frame): st.plotly_chart(geographic_chart(frame, context), width="stretch")
        else: render_empty("A geographic field and numeric measure are required.")
    elif view == "Correlation":
        if len(frame.select_dtypes(include="number").columns) >= 2: st.plotly_chart(correlation_chart(frame, context), width="stretch")
        else: render_empty("At least two numeric columns are required.")
    elif view == "Distribution":
        metrics = [column for column in ("Sales", "Profit", "Quantity", "Discount") if column in frame]
        if metrics:
            metric = st.selectbox("Distribution metric", metrics)
            st.plotly_chart(distribution_chart(frame, metric, context), width="stretch")
        else: render_empty("No supported numeric measure is available.")
    elif view == "Hierarchy":
        if "Sales" in frame and any(column in frame for column in ("Region", "Product Category", "Sub-Category")):
            hierarchy_mode = st.radio("Hierarchy mode", ["Sunburst", "Treemap"], horizontal=True)
            st.caption("Click a segment to drill into the hierarchy; click the center or breadcrumb to move back up.")
            st.plotly_chart(hierarchy_chart(frame, context, hierarchy_mode.lower()), width="stretch")
        else: render_empty("Hierarchy fields are unavailable.")
    elif view == "Grouped Bar":
        dimensions = [column for column in ("Product Category", "Customer Segment", "Region") if column in frame]
        if dimensions:
            dimension = st.selectbox("Bar dimension", dimensions)
            st.plotly_chart(grouped_bar_chart(frame, dimension, context), width="stretch")
        else: render_empty("No comparison dimension is available.")
    elif view == "Relationship":
        numeric = [column for column in ("Sales", "Profit", "Discount", "Quantity") if column in frame]
        if len(numeric) >= 2:
            relationship_controls = st.columns(2)
            default_x = numeric.index("Discount") if "Discount" in numeric else 0
            default_y = numeric.index("Profit") if "Profit" in numeric else min(1, len(numeric) - 1)
            x_metric = relationship_controls[0].selectbox("Horizontal measure", numeric, index=default_x)
            y_metric = relationship_controls[1].selectbox("Vertical measure", numeric, index=default_y)
            if x_metric == y_metric:
                render_empty("Choose two different measures to reveal a relationship.")
            else:
                st.caption("Point size represents Sales when available; color represents a business dimension. Zoom or box-select to inspect clusters.")
                st.plotly_chart(scatter_chart(frame, x_metric, y_metric, context), width="stretch")
        else: render_empty("At least two numeric measures are required.")
    elif view == "3D Space":
        supported_3d = [column for column in ("Sales", "Profit", "Discount", "Quantity") if column in frame]
        if len(supported_3d) >= 3:
            mode = st.radio(
                "3D analytical mode",
                ["Relationship cloud", "Profit terrain"],
                horizontal=True,
                help="Use the cloud for individual observations or the terrain for aggregated profitability structure.",
            )
            st.caption("Drag to rotate · scroll to zoom · double-click to reset the camera")
            if mode == "Profit terrain" and {"Sales", "Profit", "Discount"}.issubset(frame.columns):
                st.plotly_chart(profit_terrain_chart(frame, context), width="stretch")
                st.caption("Height represents verified mean Profit within each Sales and Discount band; no model prediction is used.")
            else:
                axis_controls = st.columns(4)
                x_axis = axis_controls[0].selectbox("X axis", supported_3d, index=0)
                y_axis = axis_controls[1].selectbox("Y axis", supported_3d, index=1)
                z_axis = axis_controls[2].selectbox("Z axis", supported_3d, index=2)
                color_options = ["Automatic"] + [column for column in ("Product Category", "Region", "Customer Segment") if column in frame]
                color_axis = axis_controls[3].selectbox("Color", color_options)
                if len({x_axis, y_axis, z_axis}) < 3:
                    render_empty("Choose three different measures for the 3D axes.")
                else:
                    st.plotly_chart(
                        three_dimensional_chart(
                            frame,
                            context,
                            (x_axis, y_axis, z_axis),
                            None if color_axis == "Automatic" else color_axis,
                        ),
                        width="stretch",
                    )
        else: render_empty("Three numeric measures are required for the 3D insight space.")
    elif view == "Animation":
        animation_metrics = [column for column in ("Sales", "Profit", "Quantity") if column in frame]
        if "Order Date" in frame and animation_metrics and any(column in frame for column in ("Product Category", "Region")):
            with st.container(key="animation_workspace"):
                guidance, control = st.columns([4.2, 1.2], gap="medium", vertical_alignment="bottom")
                guidance.markdown(
                    """<div class="animation-header"><span>Time playback</span><strong>See category performance change year by year</strong><small>Press Play or drag the timeline. The scale stays fixed for an honest comparison.</small></div>""",
                    unsafe_allow_html=True,
                )
                animation_metric = control.selectbox("Animated measure", animation_metrics)
                st.plotly_chart(
                    animated_chart(frame, context, animation_metric),
                    width="stretch",
                    config={"displaylogo": False, "responsive": True, "scrollZoom": False},
                )
        else: render_empty("Order Date, a supported numeric measure, and a category are required.")
