"""Accessible shared Plotly theme."""

from __future__ import annotations

import plotly.graph_objects as go

COLORS = ["#62DCFF", "#2DD4BF", "#4B8CFF", "#F7C66B", "#A78BFA", "#FF7285", "#7DD3FC"]


def apply_theme(figure: go.Figure, *, source_context: str = "") -> go.Figure:
    """Apply consistent typography, spacing, grid, and filter context."""
    figure.update_layout(
        colorway=COLORS,
        font={"family": "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Arial, Helvetica, sans-serif", "color": "#DCEEFF", "size": 13},
        title_font={"color": "#F7FBFF", "size": 19},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,15,26,0.38)",
        margin={"l": 50, "r": 35, "t": 75, "b": 55},
        legend={"orientation": "h", "y": 1.06, "x": 0, "font": {"color": "#B7CDDF"}},
        hoverlabel={"bgcolor": "#0B2136", "bordercolor": "#3C7EA5", "font_color": "#F7FBFF", "font_size": 12},
        transition={"duration": 320, "easing": "cubic-in-out"},
    )
    figure.update_xaxes(showgrid=True, gridcolor="rgba(132,183,219,0.13)", zerolinecolor="rgba(132,183,219,0.18)", linecolor="rgba(132,183,219,0.18)", title_standoff=12)
    figure.update_yaxes(showgrid=True, gridcolor="rgba(132,183,219,0.13)", zerolinecolor="rgba(132,183,219,0.18)", linecolor="rgba(132,183,219,0.18)", title_standoff=12)
    if source_context:
        figure.add_annotation(text=source_context, x=0, y=-0.18, xref="paper", yref="paper", showarrow=False, font={"size": 10, "color": "#7F9BB2"})
    return figure
