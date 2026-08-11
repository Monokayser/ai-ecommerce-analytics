"""Anomaly detection and comparative analysis interface."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.advanced.anomaly_detection import anomaly_explanation, detect_anomalies
from src.advanced.comparison import compare_subsets, comparison_narrative
from src.ui.components import render_empty
from src.ui.theme import render_section_intro
from src.visualization.themes import apply_theme


def render(frame: pd.DataFrame) -> None:
    """Render both fully integrated advanced features."""
    render_section_intro("Detect and compare", "Advanced Analytics", "Investigate unusual observations and compare two business subsets with transparent methods.")
    anomaly_tab, comparison_tab = st.tabs(["Anomaly Detection", "Comparative Analysis"])
    with anomaly_tab:
        numeric = [column for column in frame.select_dtypes(include="number").columns if not column.startswith("_outlier_")]
        if not numeric:
            render_empty("No numeric anomaly target is available.")
        else:
            controls = st.columns(4)
            target = controls[0].selectbox("Target", numeric)
            method = controls[1].selectbox("Method", ["IQR", "Isolation Forest"])
            contamination = controls[2].slider("Contamination", 0.01, 0.25, 0.05, 0.01)
            groups = ["None"] + [column for column in ("Region", "Product Category", "Customer Segment") if column in frame]
            grouping = controls[3].selectbox("Grouping", groups)
            result = detect_anomalies(frame, target, method=method, contamination=contamination, grouping=None if grouping == "None" else grouping)
            left, right = st.columns(2)
            left.metric("Anomalies", f"{result.total_anomalies:,}")
            right.metric("Anomaly rate", f"{result.anomaly_percent:.2f}%")
            plot = result.data.reset_index(names="Observation")
            figure = px.scatter(plot, x="Observation", y=target, color="is_anomaly", color_discrete_map={False: "#0F766E", True: "#DC2626"}, title=f"{target}: Normal versus Anomalous Observations")
            st.plotly_chart(apply_theme(figure), use_container_width=True)
            st.write(anomaly_explanation(result))
            st.dataframe(result.data.loc[result.data["is_anomaly"]], use_container_width=True)
            st.download_button("Export anomalies CSV", result.data.loc[result.data["is_anomaly"]].to_csv(index=False), "anomalies.csv", "text/csv")
    with comparison_tab:
        dimensions = [column for column in ("Region", "Product Category", "Customer Segment", "Country") if column in frame]
        if not dimensions:
            render_empty("No supported comparison dimension is available.")
        else:
            dimension = st.selectbox("Compare by", dimensions)
            options = sorted(frame[dimension].dropna().astype(str).unique())
            if len(options) < 2:
                render_empty("At least two subset values are required.")
            else:
                first, second = st.columns(2)
                value_a = first.selectbox("Subset A", options, index=0)
                remaining = [value for value in options if value != value_a]
                value_b = second.selectbox("Subset B", remaining, index=0)
                subset_a = frame.loc[frame[dimension].astype(str) == value_a]
                subset_b = frame.loc[frame[dimension].astype(str) == value_b]
                result = compare_subsets(subset_a, subset_b, value_a, value_b)
                st.write(comparison_narrative(result))
                for warning in result.warnings: st.warning(warning)
                st.dataframe(result.metrics, use_container_width=True)
                chart_data = result.metrics.loc[result.metrics["Metric"].isin(["Sales", "Profit", "Order count", "Quantity"])].melt(id_vars=["Metric"], value_vars=[value_a, value_b], var_name="Subset", value_name="Value")
                st.plotly_chart(apply_theme(px.bar(chart_data, x="Metric", y="Value", color="Subset", barmode="group", title="Side-by-Side KPI Comparison")), use_container_width=True)
                if "Order Date" in result.detail and "Sales" in result.detail:
                    trend = result.detail.copy()
                    trend["Month"] = pd.to_datetime(trend["Order Date"]).dt.to_period("M").dt.to_timestamp()
                    trend = trend.groupby(["Month", "_comparison_group"], as_index=False)["Sales"].sum()
                    st.plotly_chart(apply_theme(px.line(trend, x="Month", y="Sales", color="_comparison_group", title="Sales Trend Comparison")), use_container_width=True)
                if "Sales" in result.detail:
                    st.plotly_chart(apply_theme(px.box(result.detail, x="_comparison_group", y="Sales", color="_comparison_group", title="Sales Distribution Comparison")), use_container_width=True)
