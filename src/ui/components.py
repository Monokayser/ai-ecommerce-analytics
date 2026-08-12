"""Shared Streamlit rendering and business-formatting helpers."""

from __future__ import annotations

from html import escape
from typing import Any, Callable

import pandas as pd
import streamlit as st


def format_currency(value: float) -> str:
    """Format currency values compactly for KPIs."""
    absolute = abs(value)
    if absolute >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if absolute >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.2f}"


def active_filter_text(filters: dict[str, Any]) -> str:
    """Create concise chart/report context from active filters."""
    if not filters:
        return "Active dataset · no global filters"
    values = []
    for key, value in filters.items():
        display = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
        values.append(f"{key}: {display}")
    return "Active dataset · " + "; ".join(values)


def render_empty(message: str) -> None:
    """Render a consistent empty state."""
    st.markdown(
        f'<div class="empty-state" role="status"><span class="empty-icon">◇</span>{escape(message)}</div>',
        unsafe_allow_html=True,
    )


def render_signal_cards(cards: list[tuple[str, str, str]]) -> None:
    """Render compact glass insight cards for qualitative executive signals."""
    if not cards:
        return
    columns = st.columns(len(cards))
    for column, (label, value, detail) in zip(columns, cards, strict=False):
        column.markdown(
            f'<div class="answer-card"><div class="answer-eyebrow">{escape(label)}</div><h3>{escape(value)}</h3><p>{escape(detail)}</p></div>',
            unsafe_allow_html=True,
        )


def render_visualization_ribbon(frame: pd.DataFrame) -> None:
    """Summarize the active analytical canvas with data-derived readiness cues."""
    numeric_count = len([column for column in frame.select_dtypes(include="number").columns if not column.startswith("_outlier_")])
    dimension_count = len(frame.select_dtypes(exclude="number").columns)
    date_label = "No date axis"
    if "Order Date" in frame and not frame["Order Date"].dropna().empty:
        dates = pd.to_datetime(frame["Order Date"], errors="coerce").dropna()
        if not dates.empty:
            date_label = f"{dates.min():%b %Y} – {dates.max():%b %Y}"
    ready_3d = numeric_count >= 3
    features = [
        ("Live analytical scope", f"{len(frame):,} filtered records power every view"),
        ("Measurement depth", f"{numeric_count} measures · {dimension_count} dimensions"),
        ("Time coverage", date_label),
        ("3D insight engine", "Ready to rotate and inspect" if ready_3d else "Needs three numeric measures"),
    ]
    cards = "".join(
        f'<div class="viz-feature"><b>{escape(title)}</b><span>{escape(detail)}</span></div>'
        for title, detail in features
    )
    st.markdown(f'<div class="viz-ribbon" aria-label="Visualization readiness">{cards}</div>', unsafe_allow_html=True)


def _period_frames(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    if "Order Date" not in frame or frame["Order Date"].dropna().empty:
        return None
    dates = pd.to_datetime(frame["Order Date"], errors="coerce")
    maximum = dates.max()
    current_start = maximum.to_period("M").start_time
    elapsed = maximum.normalize() - current_start.normalize()
    previous_start = current_start - pd.offsets.MonthBegin(1)
    previous_end = min(previous_start + elapsed + pd.Timedelta(days=1), current_start)
    current = frame.loc[dates.between(current_start, maximum + pd.Timedelta(days=1), inclusive="left")]
    previous = frame.loc[dates.between(previous_start, previous_end, inclusive="left")]
    return (current, previous) if not current.empty and not previous.empty else None


def _delta(current: float, previous: float) -> str | None:
    if previous == 0:
        return None
    return f"{(current - previous) / abs(previous) * 100:+.1f}% vs prior"


def render_kpis(frame: pd.DataFrame) -> None:
    """Render responsive KPI cards with matched preceding-period comparisons."""
    sales = float(frame["Sales"].sum()) if "Sales" in frame else 0.0
    profit = float(frame["Profit"].sum()) if "Profit" in frame else 0.0
    orders = int(frame["Order ID"].nunique()) if "Order ID" in frame else len(frame)
    metrics: list[tuple[str, str, str | None, Callable[[pd.DataFrame], float]]] = []
    if "Sales" in frame:
        metrics.append(("Total Sales", format_currency(sales), None, lambda data: float(data["Sales"].sum())))
    if "Profit" in frame:
        metrics.append(("Total Profit", format_currency(profit), None, lambda data: float(data["Profit"].sum())))
    metrics.append(("Total Orders", f"{orders:,}", None, lambda data: float(data["Order ID"].nunique() if "Order ID" in data else len(data))))
    if "Sales" in frame:
        metrics.append(("Average Order Value", format_currency(sales / orders if orders else 0), None, lambda data: float(data["Sales"].sum() / max(data["Order ID"].nunique() if "Order ID" in data else len(data), 1))))
    if "Quantity" in frame:
        metrics.append(("Units Sold", f"{frame['Quantity'].sum():,.0f}", None, lambda data: float(data["Quantity"].sum())))
    if {"Sales", "Profit"}.issubset(frame.columns):
        margin = profit / sales * 100 if sales else 0.0
        metrics.append(("Profit Margin", f"{margin:.2f}%" if sales else "N/A", None, lambda data: float(data["Profit"].sum() / data["Sales"].sum() * 100) if data["Sales"].sum() else 0.0))
    if "Discount" in frame:
        metrics.append(("Average Discount", f"{frame['Discount'].mean() * 100:.2f}%", None, lambda data: float(data["Discount"].mean() * 100)))
    dimension = "Customer ID" if "Customer ID" in frame else "Country" if "Country" in frame else None
    if dimension:
        metrics.append((f"Unique {dimension.replace(' ID', 's')}", f"{frame[dimension].nunique():,}", None, lambda data: float(data[dimension].nunique())))

    periods = _period_frames(frame)
    if periods:
        current_period, previous_period = periods
        metrics = [
            (label, value, _delta(calculator(current_period), calculator(previous_period)), calculator)
            for label, value, _, calculator in metrics
        ]
    for start in range(0, len(metrics), 4):
        columns = st.columns(4)
        for column, (label, value, delta, _) in zip(columns, metrics[start : start + 4], strict=False):
            column.metric(label, value, delta=delta)
    if periods:
        st.caption("KPI deltas compare the latest active partial month with the same span of the preceding month.")
