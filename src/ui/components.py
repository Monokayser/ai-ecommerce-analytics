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
    covered_months = 0
    if "Order Date" in frame and not frame["Order Date"].dropna().empty:
        dates = pd.to_datetime(frame["Order Date"], errors="coerce").dropna()
        if not dates.empty:
            date_label = f"{dates.min():%b %Y} – {dates.max():%b %Y}"
            covered_months = max((dates.max().year - dates.min().year) * 12 + dates.max().month - dates.min().month + 1, 1)
    ready_3d = numeric_count >= 3
    features = [
        ("Live analytical scope", f"{len(frame):,} filtered records power every view", min(len(frame) / 5_000 * 100, 100)),
        ("Measurement depth", f"{numeric_count} measures · {dimension_count} dimensions", min(numeric_count / 4 * 100, 100)),
        ("Time coverage", date_label, min(covered_months / 36 * 100, 100)),
        ("3D insight engine", "Ready to rotate and inspect" if ready_3d else "Needs three numeric measures", 100 if ready_3d else min(numeric_count / 3 * 100, 100)),
    ]
    cards = "".join(
        f'<div class="viz-feature" style="--meter:{meter:.1f}%"><b>{escape(title)}</b><span>{escape(detail)}</span><div class="telemetry-rail" aria-hidden="true"><i></i></div></div>'
        for title, detail, meter in features
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


def _delta_percent(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current - previous) / abs(previous) * 100


def render_kpis(frame: pd.DataFrame) -> None:
    """Render responsive KPI cards with matched preceding-period comparisons."""
    sales = float(frame["Sales"].sum()) if "Sales" in frame else 0.0
    profit = float(frame["Profit"].sum()) if "Profit" in frame else 0.0
    orders = int(frame["Order ID"].nunique()) if "Order ID" in frame else len(frame)
    metrics: list[tuple[str, str, str | None, Callable[[pd.DataFrame], float], float | None]] = []
    if "Sales" in frame:
        metrics.append(("Total Sales", format_currency(sales), None, lambda data: float(data["Sales"].sum()), None))
    if "Profit" in frame:
        metrics.append(("Total Profit", format_currency(profit), None, lambda data: float(data["Profit"].sum()), None))
    metrics.append(("Total Orders", f"{orders:,}", None, lambda data: float(data["Order ID"].nunique() if "Order ID" in data else len(data)), None))
    if "Sales" in frame:
        metrics.append(("Average Order Value", format_currency(sales / orders if orders else 0), None, lambda data: float(data["Sales"].sum() / max(data["Order ID"].nunique() if "Order ID" in data else len(data), 1)), None))
    if "Quantity" in frame:
        metrics.append(("Units Sold", f"{frame['Quantity'].sum():,.0f}", None, lambda data: float(data["Quantity"].sum()), None))
    if {"Sales", "Profit"}.issubset(frame.columns):
        margin = profit / sales * 100 if sales else 0.0
        metrics.append(("Profit Margin", f"{margin:.2f}%" if sales else "N/A", None, lambda data: float(data["Profit"].sum() / data["Sales"].sum() * 100) if data["Sales"].sum() else 0.0, None))
    if "Discount" in frame:
        metrics.append(("Average Discount", f"{frame['Discount'].mean() * 100:.2f}%", None, lambda data: float(data["Discount"].mean() * 100), None))
    dimension = "Customer ID" if "Customer ID" in frame else "Country" if "Country" in frame else None
    if dimension:
        metrics.append((f"Unique {dimension.replace(' ID', 's')}", f"{frame[dimension].nunique():,}", None, lambda data: float(data[dimension].nunique()), None))

    periods = _period_frames(frame)
    if periods:
        current_period, previous_period = periods
        compared_metrics = []
        for label, value, _, calculator, _ in metrics:
            current_value = calculator(current_period)
            previous_value = calculator(previous_period)
            compared_metrics.append(
                (
                    label,
                    value,
                    _delta(current_value, previous_value),
                    calculator,
                    _delta_percent(current_value, previous_value),
                )
            )
        metrics = compared_metrics
    for start in range(0, len(metrics), 4):
        columns = st.columns(4)
        for position, (column, (label, value, delta, _, delta_percent)) in enumerate(zip(columns, metrics[start : start + 4], strict=False), start=start):
            direction = "neutral" if delta_percent is None else "positive" if delta_percent >= 0 else "negative"
            meter = 12.0 if delta_percent is None else min(max(abs(delta_percent), 4.0), 100.0)
            delta_text = delta or "Current active scope"
            delta_icon = "◆" if delta_percent is None else "↑" if delta_percent >= 0 else "↓"
            delay = min(position * 70, 560)
            column.markdown(
                f'<div class="kpi-card {direction}" role="group" aria-label="{escape(label)}: {escape(value)}; {escape(delta_text)}" style="--meter:{meter:.1f}%;--delay:{delay}ms"><div class="kpi-scan" aria-hidden="true"></div><span class="kpi-label">{escape(label)}</span><strong class="kpi-value">{escape(value)}</strong><span class="kpi-delta">{delta_icon} {escape(delta_text)}</span><div class="kpi-meter" aria-hidden="true"><i></i></div></div>',
                unsafe_allow_html=True,
            )
    if periods:
        st.caption("KPI deltas compare the latest active partial month with the same span of the preceding month.")
