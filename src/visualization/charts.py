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
        return frame.copy(deep=False)
    return frame.sample(n=limit, random_state=seed).copy(deep=False)


def time_series_chart(frame: pd.DataFrame, context: str = "") -> go.Figure:
    """Monthly Sales and Profit trend with dual y axes."""
    metrics = [column for column in ("Sales", "Profit") if column in frame]
    data = frame.loc[frame["Order Date"].notna(), ["Order Date", *metrics]].copy(deep=False)
    data["Month"] = pd.to_datetime(data["Order Date"]).dt.to_period("M").dt.to_timestamp()
    grouped = data.groupby("Month", as_index=False, observed=True)[metrics].sum()
    figure = make_subplots(specs=[[{"secondary_y": len(metrics) > 1}]])
    if "Sales" in grouped:
        figure.add_trace(
            go.Scatter(
                x=grouped["Month"], y=grouped["Sales"], name="Sales", mode="lines+markers",
                line={"color": "#7FFFE1", "width": 3, "shape": "spline"},
                marker={"size": 7, "color": "#071C15", "line": {"color": "#7FFFE1", "width": 2}},
                fill="tozeroy", fillcolor="rgba(57,230,189,.08)",
            ),
            secondary_y=False,
        )
    if "Profit" in grouped:
        figure.add_trace(
            go.Scatter(
                x=grouped["Month"], y=grouped["Profit"], name="Profit", mode="lines+markers",
                line={"color": "#B7F06D", "width": 2.4, "shape": "spline"},
                marker={"size": 6, "color": "#071C15", "line": {"color": "#B7F06D", "width": 2}},
            ),
            secondary_y=True,
        )
    figure.update_layout(title="Monthly Sales and Profit Trend")
    figure.update_layout(hovermode="x unified")
    figure.update_xaxes(
        title="Month",
        rangeselector={
            "buttons": [
                {"count": 3, "label": "3M", "step": "month", "stepmode": "backward"},
                {"count": 6, "label": "6M", "step": "month", "stepmode": "backward"},
                {"count": 1, "label": "1Y", "step": "year", "stepmode": "backward"},
                {"step": "all", "label": "All"},
            ],
            "bgcolor": "rgba(5,31,23,.86)",
            "activecolor": "rgba(57,230,189,.38)",
            "bordercolor": "rgba(127,255,225,.22)",
        },
        rangeslider={
            "visible": True,
            "thickness": 0.06,
            "bgcolor": "rgba(3,24,17,.68)",
            "bordercolor": "rgba(127,255,225,.14)",
            "borderwidth": 1,
        },
    )
    figure.update_yaxes(title="Sales", secondary_y=False)
    if len(metrics) > 1:
        figure.update_yaxes(title="Profit", secondary_y=True)
    return apply_theme(figure, source_context=context)


def geographic_chart(frame: pd.DataFrame, context: str = "") -> go.Figure:
    """Country choropleth or region/country bar fallback."""
    metric = "Sales" if "Sales" in frame else "Profit"
    if "Country" in frame and metric in frame:
        grouped = frame[["Country", metric]].groupby("Country", as_index=False, observed=True)[metric].sum()
        grouped["ISO3"] = grouped["Country"].map(COUNTRY_ISO3)
        if grouped["ISO3"].notna().all() and grouped["Country"].nunique() > 1:
            figure = px.choropleth(
                grouped,
                locations="ISO3",
                locationmode="ISO-3",
                hover_name="Country",
                color=metric,
                color_continuous_scale=["#09231B", "#1F7D5F", "#7FFFE1"],
                title=f"{metric} by Country",
            )
            figure.update_geos(
                projection_type="natural earth",
                showframe=False,
                showcoastlines=True,
                coastlinecolor="rgba(156,233,207,.25)",
                bgcolor="rgba(2,14,10,.15)",
            )
            return apply_theme(figure, source_context=context)
    dimension = "Region" if "Region" in frame else "Country"
    grouped = frame[[dimension, metric]].groupby(dimension, as_index=False, observed=True)[metric].sum().sort_values(metric)
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
    columns = [metric] + ([color] if color else [])
    data = _bounded_sample(frame[columns], 50_000)
    figure = px.histogram(data, x=metric, color=color, marginal="box", nbins=40, title=f"Distribution of {metric}")
    return apply_theme(figure, source_context=context)


def hierarchy_chart(frame: pd.DataFrame, context: str = "", mode: str = "sunburst") -> go.Figure:
    """Region to category to sub-category drill-down view."""
    path = [column for column in ("Region", "Product Category", "Sub-Category") if column in frame]
    value = "Sales" if "Sales" in frame else "Quantity"
    data = frame[[*path, value]].groupby(path, as_index=False, dropna=False, observed=True)[value].sum()
    if mode == "treemap":
        figure = px.treemap(data, path=path, values=value, color=value, color_continuous_scale=["#09231B", "#27A77D", "#8AFFD9"], title=f"{value} Treemap: {' > '.join(path)}")
    else:
        figure = px.sunburst(data, path=path, values=value, color=value, color_continuous_scale=["#09231B", "#27A77D", "#8AFFD9"], title=f"{value} Sunburst: {' > '.join(path)}")
    figure.update_traces(hovertemplate="%{label}<br>%{value:,.2f}<br>%{percentParent:.1%} of parent<extra></extra>")
    return apply_theme(figure, source_context=context)


def grouped_bar_chart(frame: pd.DataFrame, dimension: str = "Product Category", context: str = "") -> go.Figure:
    """Grouped Sales and Profit comparison."""
    measures = [column for column in ("Sales", "Profit") if column in frame]
    grouped = frame[[dimension, *measures]].groupby(dimension, as_index=False, observed=True)[measures].sum().melt(id_vars=dimension, var_name="Metric", value_name="Value")
    figure = px.bar(grouped, x=dimension, y="Value", color="Metric", barmode="group", title=f"Sales and Profit by {dimension}")
    figure.update_layout(
        updatemenus=[{
            "type": "buttons",
            "direction": "right",
            "x": 1,
            "xanchor": "right",
            "y": 1.16,
            "buttons": [
                {"label": "Grouped", "method": "relayout", "args": [{"barmode": "group"}]},
                {"label": "Stacked", "method": "relayout", "args": [{"barmode": "relative"}]},
            ],
            "bgcolor": "rgba(5,31,23,.86)",
            "bordercolor": "rgba(127,255,225,.2)",
        }]
    )
    return apply_theme(figure, source_context=context)


def scatter_chart(frame: pd.DataFrame, x: str = "Discount", y: str = "Profit", context: str = "") -> go.Figure:
    """Numeric relationship scatter with least-squares trend line."""
    color = next((column for column in ("Product Category", "Region", "Customer Segment") if column in frame), None)
    size = "Sales" if "Sales" in frame and "Sales" not in {x, y} and frame["Sales"].min() >= 0 else None
    hover = [column for column in ("Order ID", "Country", "Sub-Category") if column in frame]
    required = list(dict.fromkeys([x, y] + ([color] if color else []) + ([size] if size else []) + hover))
    data = _bounded_sample(frame[required].dropna(subset=[x, y]), 8_000)
    figure = px.scatter(
        data,
        x=x,
        y=y,
        color=color,
        size=size,
        size_max=22,
        hover_data=hover,
        opacity=0.62,
        render_mode="webgl",
        title=f"{y} versus {x}",
    )
    if len(data) >= 2 and data[x].nunique() > 1:
        slope, intercept = np.polyfit(data[x], data[y], 1)
        xs = np.linspace(data[x].min(), data[x].max(), 100)
        figure.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, name="Linear trend", mode="lines", line={"color": "#DC2626"}))
    return apply_theme(figure, source_context=context)


def three_dimensional_chart(
    frame: pd.DataFrame,
    context: str = "",
    axes: tuple[str, str, str] | None = None,
    color_field: str | None = None,
) -> go.Figure:
    """WebGL 3D relationship space for three business measures."""
    preferred = list(axes) if axes else [column for column in ("Sales", "Profit", "Discount", "Quantity") if column in frame]
    if len(preferred) < 3:
        raise ValueError("At least three supported numeric measures are required for the 3D view.")
    x, y, z = preferred[:3]
    color = color_field or next((column for column in ("Product Category", "Region", "Customer Segment") if column in frame), None)
    hover = [column for column in ("Order ID", "Country", "Sub-Category") if column in frame]
    required = list(dict.fromkeys([x, y, z] + ([color] if color else []) + hover))
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
        bgcolor="rgba(2,12,9,0.22)",
        xaxis={"backgroundcolor": "rgba(4,28,20,.45)", "gridcolor": "rgba(116,244,194,.18)", "showbackground": True},
        yaxis={"backgroundcolor": "rgba(4,28,20,.45)", "gridcolor": "rgba(116,244,194,.18)", "showbackground": True},
        zaxis={"backgroundcolor": "rgba(4,28,20,.45)", "gridcolor": "rgba(116,244,194,.18)", "showbackground": True},
        camera={"eye": {"x": 1.45, "y": 1.45, "z": 1.15}},
    )
    return figure


def profit_terrain_chart(frame: pd.DataFrame, context: str = "") -> go.Figure:
    """Render a 3D surface of mean profit across sales and discount bands."""
    required = ["Sales", "Profit", "Discount"]
    if not set(required).issubset(frame.columns):
        raise ValueError("Sales, Profit, and Discount are required for the profit terrain.")
    data = _bounded_sample(frame[required].dropna(), 100_000)
    if data.empty or data["Sales"].nunique() < 2 or data["Discount"].nunique() < 2:
        raise ValueError("The profit terrain needs variation in Sales and Discount.")

    sales_bins = min(10, int(data["Sales"].nunique()))
    discount_bins = min(12, int(data["Discount"].nunique()))
    data["Sales band"] = pd.qcut(data["Sales"], q=sales_bins, duplicates="drop")
    data["Discount band"] = pd.cut(data["Discount"], bins=discount_bins, duplicates="drop")
    terrain = data.pivot_table(
        index="Sales band",
        columns="Discount band",
        values="Profit",
        aggfunc="mean",
        observed=True,
    )
    if terrain.shape[0] < 2 or terrain.shape[1] < 2:
        raise ValueError("The active data does not produce enough populated terrain bands.")

    x_values = [float(interval.mid) for interval in terrain.columns]
    y_values = [float(interval.mid) for interval in terrain.index]
    figure = go.Figure(
        go.Surface(
            x=x_values,
            y=y_values,
            z=terrain.to_numpy(),
            colorscale=[
                [0.0, "#5c1627"],
                [0.32, "#a25735"],
                [0.5, "#183c31"],
                [0.72, "#27a77d"],
                [1.0, "#8affd9"],
            ],
            colorbar={"title": "Mean profit", "tickprefix": "$"},
            contours={"z": {"show": True, "usecolormap": True, "highlightcolor": "#b9ffeb", "project_z": True}},
            hovertemplate="Discount %{x:.1%}<br>Sales band midpoint $%{y:,.0f}<br>Mean profit $%{z:,.2f}<extra></extra>",
        )
    )
    figure.update_layout(title="3D Profit Terrain: Sales × Discount × Mean Profit")
    figure = apply_theme(figure, source_context=context)
    figure.update_scenes(
        bgcolor="rgba(2,12,9,0.18)",
        xaxis={"title": "Discount", "tickformat": ".0%", "gridcolor": "rgba(116,244,194,.18)", "showbackground": True, "backgroundcolor": "rgba(4,28,20,.48)"},
        yaxis={"title": "Sales band midpoint", "tickprefix": "$", "gridcolor": "rgba(116,244,194,.18)", "showbackground": True, "backgroundcolor": "rgba(4,28,20,.48)"},
        zaxis={"title": "Mean profit", "tickprefix": "$", "gridcolor": "rgba(116,244,194,.18)", "showbackground": True, "backgroundcolor": "rgba(4,28,20,.48)"},
        camera={"eye": {"x": 1.55, "y": 1.45, "z": 1.15}},
        aspectmode="cube",
    )
    return figure


def animated_chart(frame: pd.DataFrame, context: str = "", metric: str = "Sales") -> go.Figure:
    """Animated category performance by year."""
    if metric not in frame:
        raise ValueError(f"{metric} is unavailable for animation.")
    dimension = "Product Category" if "Product Category" in frame else "Region"
    data = frame.loc[frame["Order Date"].notna(), ["Order Date", dimension, metric]].copy(deep=False)
    data["Year"] = pd.to_datetime(data["Order Date"]).dt.year.astype(str)
    grouped = data.groupby(["Year", dimension], as_index=False, observed=True)[metric].sum()
    upper = max(float(grouped[metric].max()) * 1.22, 1.0)
    figure = px.bar(
        grouped,
        x=dimension,
        y=metric,
        color=dimension,
        animation_frame="Year",
        animation_group=dimension,
        range_y=[min(0.0, float(grouped[metric].min()) * 1.12), upper],
        title=f"Animated {metric} by {dimension}",
        text=metric,
    )
    figure = apply_theme(figure, source_context=context)
    figure.update_layout(
        height=650,
        autosize=True,
        margin={"l": 64, "r": 28, "t": 92, "b": 118},
        bargap=0.2,
        title={"x": 0.01, "xanchor": "left", "font": {"size": 23}},
        legend={"orientation": "h", "x": 0.01, "xanchor": "left", "y": 1.04, "yanchor": "bottom"},
        transition={"duration": 420, "easing": "cubic-in-out"},
        uniformtext={"minsize": 12, "mode": "hide"},
    )
    figure.update_traces(
        texttemplate="%{y:,.3s}",
        textposition="outside",
        cliponaxis=False,
        marker_line={"color": "rgba(225,255,245,.35)", "width": 1},
        hovertemplate=f"{dimension}: %{{x}}<br>{metric}: %{{y:,.2f}}<extra></extra>",
    )
    figure.update_xaxes(tickfont={"size": 13}, title=None)
    figure.update_yaxes(tickfont={"size": 12}, title={"text": metric, "font": {"size": 14}})
    for slider in figure.layout.sliders or []:
        slider.transition = {"duration": 350, "easing": "cubic-in-out"}
        slider.pad = {"t": 36, "b": 4}
        slider.currentvalue = {"prefix": "Year  ", "font": {"color": "#DFFFF3", "size": 14}}
    for menu in figure.layout.updatemenus or []:
        menu.pad = {"r": 12, "t": 62}
    return figure


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
