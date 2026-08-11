"""Reusable constructors for the required interactive chart suite."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.models import ChartSpec
from src.visualization.themes import apply_theme


COUNTRY_ISO3 = {
    "Australia": "AUS",
    "Brazil": "BRA",
    "Canada": "CAN",
    "China": "CHN",
    "France": "FRA",
    "Germany": "DEU",
    "India": "IND",
    "Italy": "ITA",
    "Japan": "JPN",
    "Mexico": "MEX",
    "Netherlands": "NLD",
    "Singapore": "SGP",
    "Spain": "ESP",
    "United Arab Emirates": "ARE",
    "United Kingdom": "GBR",
    "United States": "USA",
    "United States of America": "USA",
}


def _bounded_sample(frame: pd.DataFrame, limit: int, *, seed: int = 42) -> pd.DataFrame:
    """Return a deterministic sample so browser chart payloads remain bounded."""
    if len(frame) <= limit:
        return frame.copy()
    return frame.sample(n=limit, random_state=seed).copy()


def time_series_chart(frame: pd.DataFrame, context: str = "") -> go.Figure:
    """Monthly Sales and Profit trend with dual y axes."""
    data = frame.dropna(subset=["Order Date"]).copy()
    data["Month"] = pd.to_datetime(data["Order Date"]).dt.to_period("M").dt.to_timestamp()
    metrics = [column for column in ("Sales", "Profit") if column in data]
    grouped = data.groupby("Month", as_index=False)[metrics].sum()
    figure = make_subplots(specs=[[{"secondary_y": len(metrics) > 1}]])
    if "Sales" in grouped:
        figure.add_trace(go.Scatter(x=grouped["Month"], y=grouped["Sales"], name="Sales", mode="lines+markers"), secondary_y=False)
    if "Profit" in grouped:
        figure.add_trace(go.Scatter(x=grouped["Month"], y=grouped["Profit"], name="Profit", mode="lines+markers"), secondary_y=True)
    figure.update_layout(title="Monthly Sales and Profit Trend")
    figure.update_xaxes(title="Month")
    figure.update_yaxes(title="Sales", secondary_y=False)
    if len(metrics) > 1:
        figure.update_yaxes(title="Profit", secondary_y=True)
    return apply_theme(figure, source_context=context)


def geographic_chart(frame: pd.DataFrame, context: str = "") -> go.Figure:
    """Country choropleth or region/country bar fallback."""
    metric = "Sales" if "Sales" in frame else "Profit"
    if "Country" in frame and metric in frame:
        grouped = frame.groupby("Country", as_index=False)[metric].sum()
        grouped["ISO3"] = grouped["Country"].map(COUNTRY_ISO3)
        if grouped["ISO3"].notna().all() and grouped["Country"].nunique() > 1:
            figure = px.choropleth(
                grouped,
                locations="ISO3",
                locationmode="ISO-3",
                hover_name="Country",
                color=metric,
                color_continuous_scale="Teal",
                title=f"{metric} by Country",
            )
            return apply_theme(figure, source_context=context)
    dimension = "Region" if "Region" in frame else "Country"
    grouped = frame.groupby(dimension, as_index=False)[metric].sum().sort_values(metric)
    return apply_theme(px.bar(grouped, x=metric, y=dimension, orientation="h", title=f"{metric} by {dimension} (Map Fallback)"), source_context=context)


def correlation_chart(frame: pd.DataFrame, context: str = "") -> go.Figure:
    """Correlation heatmap for available numeric measures."""
    columns = [column for column in frame.select_dtypes(include="number").columns if not column.startswith("_outlier_")]
    corr = _bounded_sample(frame[columns], 100_000).corr()
    figure = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1, colorscale="RdBu", reversescale=True, text=np.round(corr.values, 2), texttemplate="%{text}"))
    figure.update_layout(title="Correlation Matrix")
    return apply_theme(figure, source_context=context)


def distribution_chart(frame: pd.DataFrame, metric: str = "Sales", context: str = "") -> go.Figure:
    """Box-and-histogram distribution view."""
    color = "Region" if "Region" in frame else None
    data = _bounded_sample(frame, 50_000)
    figure = px.histogram(data, x=metric, color=color, marginal="box", nbins=40, title=f"Distribution of {metric}")
    return apply_theme(figure, source_context=context)


def hierarchy_chart(frame: pd.DataFrame, context: str = "") -> go.Figure:
    """Region to category to sub-category sunburst."""
    path = [column for column in ("Region", "Product Category", "Sub-Category") if column in frame]
    value = "Sales" if "Sales" in frame else "Quantity"
    data = frame.groupby(path, as_index=False, dropna=False)[value].sum()
    figure = px.sunburst(data, path=path, values=value, title=f"{value} Hierarchy: {' > '.join(path)}")
    return apply_theme(figure, source_context=context)


def grouped_bar_chart(frame: pd.DataFrame, dimension: str = "Product Category", context: str = "") -> go.Figure:
    """Grouped Sales and Profit comparison."""
    measures = [column for column in ("Sales", "Profit") if column in frame]
    grouped = frame.groupby(dimension, as_index=False)[measures].sum().melt(id_vars=dimension, var_name="Metric", value_name="Value")
    return apply_theme(px.bar(grouped, x=dimension, y="Value", color="Metric", barmode="group", title=f"Sales and Profit by {dimension}"), source_context=context)


def scatter_chart(frame: pd.DataFrame, x: str = "Discount", y: str = "Profit", context: str = "") -> go.Figure:
    """Numeric relationship scatter with least-squares trend line."""
    data = _bounded_sample(frame[[x, y]].dropna(), 8_000)
    figure = px.scatter(data, x=x, y=y, opacity=0.55, render_mode="webgl", title=f"{y} versus {x}")
    if len(data) >= 2 and data[x].nunique() > 1:
        slope, intercept = np.polyfit(data[x], data[y], 1)
        xs = np.linspace(data[x].min(), data[x].max(), 100)
        figure.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, name="Linear trend", mode="lines", line={"color": "#DC2626"}))
    return apply_theme(figure, source_context=context)


def three_dimensional_chart(frame: pd.DataFrame, context: str = "") -> go.Figure:
    """WebGL 3D relationship space for three business measures."""
    preferred = [column for column in ("Sales", "Profit", "Discount", "Quantity") if column in frame]
    if len(preferred) < 3:
        raise ValueError("At least three supported numeric measures are required for the 3D view.")
    x, y, z = preferred[:3]
    color = next((column for column in ("Product Category", "Region", "Customer Segment") if column in frame), None)
    hover = [column for column in ("Order ID", "Country", "Sub-Category") if column in frame]
    required = [x, y, z] + ([color] if color else []) + hover
    data = _bounded_sample(frame[required].dropna(subset=[x, y, z]), 4_000)
    figure = px.scatter_3d(
        data,
        x=x,
        y=y,
        z=z,
        color=color,
        hover_data=hover,
        opacity=0.72,
        title=f"3D Insight Space: {x}, {y}, and {z}",
    )
    figure.update_traces(marker={"size": 4, "line": {"width": 0}})
    figure = apply_theme(figure, source_context=context)
    figure.update_scenes(
        bgcolor="rgba(5,15,26,0.28)",
        xaxis={"backgroundcolor": "rgba(8,31,50,.45)", "gridcolor": "rgba(132,183,219,.18)", "showbackground": True},
        yaxis={"backgroundcolor": "rgba(8,31,50,.45)", "gridcolor": "rgba(132,183,219,.18)", "showbackground": True},
        zaxis={"backgroundcolor": "rgba(8,31,50,.45)", "gridcolor": "rgba(132,183,219,.18)", "showbackground": True},
        camera={"eye": {"x": 1.45, "y": 1.45, "z": 1.15}},
    )
    return figure


def animated_chart(frame: pd.DataFrame, context: str = "") -> go.Figure:
    """Animated category performance by year."""
    data = frame.dropna(subset=["Order Date"]).copy()
    data["Year"] = pd.to_datetime(data["Order Date"]).dt.year.astype(str)
    dimension = "Product Category" if "Product Category" in data else "Region"
    grouped = data.groupby(["Year", dimension], as_index=False)["Sales"].sum()
    figure = px.bar(grouped, x=dimension, y="Sales", color=dimension, animation_frame="Year", range_y=[0, grouped["Sales"].max() * 1.1], title=f"Animated Sales by {dimension}")
    return apply_theme(figure, source_context=context)


def result_chart(frame: pd.DataFrame, spec: ChartSpec) -> go.Figure | None:
    """Render a chart selected for an AI query result."""
    if frame.empty or spec.chart_type in {"table", "kpi"}:
        return None
    if spec.chart_type == "line":
        figure = px.line(frame, x=spec.x, y=spec.y, markers=True, title=spec.title)
    elif spec.chart_type == "scatter":
        figure = px.scatter(_bounded_sample(frame, 8_000), x=spec.x, y=spec.y[0], render_mode="webgl", title=spec.title)
    elif spec.chart_type == "map":
        figure = px.choropleth(frame, locations=spec.x, locationmode="country names", color=spec.y[0], title=spec.title)
    else:
        figure = px.bar(frame, x=spec.x, y=spec.y, barmode="group", title=spec.title)
    return apply_theme(figure)
