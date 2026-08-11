"""Overview dashboard section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components import active_filter_text, format_currency, render_empty, render_kpis, render_signal_cards
from src.ui.theme import render_section_intro
from src.visualization.charts import geographic_chart, grouped_bar_chart, time_series_chart


def render(frame: pd.DataFrame, filters: dict) -> None:
    """Render KPI and headline analytical views."""
    render_section_intro("Monitor the business", "Overview", "Executive view of filtered sales, profitability, volume, and geography.")
    if frame.empty:
        render_empty("No rows match the active filters. Reset or broaden them to continue.")
        return
    render_kpis(frame)
    st.subheader("Executive signals")
    signals: list[tuple[str, str, str]] = []
    if {"Region", "Sales"}.issubset(frame.columns):
        regional = frame.groupby("Region")["Sales"].sum().sort_values(ascending=False)
        signals.append(("Leading region", str(regional.index[0]), f"{format_currency(float(regional.iloc[0]))} in active sales"))
    if {"Product Category", "Profit"}.issubset(frame.columns):
        category = frame.groupby("Product Category")["Profit"].sum().sort_values(ascending=False)
        signals.append(("Top profit category", str(category.index[0]), f"{format_currency(float(category.iloc[0]))} generated profit"))
    if "Profit" in frame:
        loss_rate = float((frame["Profit"] < 0).mean() * 100)
        signals.append(("Loss-making rows", f"{loss_rate:.1f}%", "Share of active transactions below zero profit"))
    render_signal_cards(signals)
    context = active_filter_text(filters)
    left, right = st.columns([1.35, 1])
    if {"Order Date", "Sales"}.issubset(frame.columns):
        left.plotly_chart(time_series_chart(frame, context), use_container_width=True)
    if ("Country" in frame or "Region" in frame) and ("Sales" in frame or "Profit" in frame):
        right.plotly_chart(geographic_chart(frame, context), use_container_width=True)
    dimension = next((column for column in ("Product Category", "Region", "Customer Segment") if column in frame), None)
    if dimension and ("Sales" in frame or "Profit" in frame):
        st.plotly_chart(grouped_bar_chart(frame, dimension, context), use_container_width=True)
