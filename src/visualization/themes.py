"""Accessible shared Plotly theme."""

from __future__ import annotations

import plotly.graph_objects as go

COLORS = ["#70DDFF", "#39A9D2", "#72E3BD", "#A6C8FF", "#F2C96D", "#FF7D91", "#B8DCE8"]


def apply_theme(figure: go.Figure, *, source_context: str = "") -> go.Figure:
    """Apply consistent typography, spacing, grid, and filter context."""
    figure.update_layout(
        colorway=COLORS,
        font={"family": "Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif", "color": "#DCE8EE", "size": 13},
        title_font={"color": "#F6FAFC", "size": 19},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,11,16,0.64)",
        margin={"l": 50, "r": 35, "t": 75, "b": 55},
        legend={"orientation": "h", "y": 1.06, "x": 0, "font": {"color": "#AFC2CC"}},
        hoverlabel={"bgcolor": "#09141C", "bordercolor": "#49BADD", "font_color": "#F6FAFC", "font_size": 12},
        hovermode="closest",
        modebar={"bgcolor": "rgba(6,14,20,.82)", "color": "#88A9B8", "activecolor": "#70DDFF"},
    )
    figure.update_xaxes(showgrid=True, gridcolor="rgba(135,195,216,0.11)", zerolinecolor="rgba(135,195,216,0.18)", linecolor="rgba(135,195,216,0.17)", title_standoff=12)
    figure.update_yaxes(showgrid=True, gridcolor="rgba(135,195,216,0.11)", zerolinecolor="rgba(135,195,216,0.18)", linecolor="rgba(135,195,216,0.17)", title_standoff=12)
    if source_context:
        figure.add_annotation(text=source_context, x=0, y=-0.18, xref="paper", yref="paper", showarrow=False, font={"size": 10, "color": "#7893A0"})
    return figure
