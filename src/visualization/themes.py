"""Accessible shared Plotly theme."""

from __future__ import annotations

import plotly.graph_objects as go

COLORS = ["#0F766E", "#1D4ED8", "#F59E0B", "#7C3AED", "#DC2626", "#0891B2", "#475569"]


def apply_theme(figure: go.Figure, *, source_context: str = "") -> go.Figure:
    """Apply consistent typography, spacing, grid, and filter context."""
    figure.update_layout(
        colorway=COLORS,
        font={"family": "Arial, sans-serif", "color": "#0F172A", "size": 13},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        margin={"l": 50, "r": 35, "t": 75, "b": 55},
        legend={"orientation": "h", "y": 1.06, "x": 0},
        hoverlabel={"bgcolor": "white", "font_size": 12},
    )
    figure.update_xaxes(showgrid=True, gridcolor="#E2E8F0", title_standoff=12)
    figure.update_yaxes(showgrid=True, gridcolor="#E2E8F0", title_standoff=12)
    if source_context:
        figure.add_annotation(text=source_context, x=0, y=-0.18, xref="paper", yref="paper", showarrow=False, font={"size": 10, "color": "#64748B"})
    return figure
