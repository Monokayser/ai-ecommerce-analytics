"""Kaleido-backed Plotly chart export."""

from __future__ import annotations

import plotly.graph_objects as go

from src.utils.exceptions import ExportError


def export_chart(figure: go.Figure, format: str = "png", *, scale: float = 2.0) -> bytes:
    """Return PNG or SVG bytes with an actionable browser error."""
    if format not in {"png", "svg"}:
        raise ExportError("Chart format must be PNG or SVG.")
    try:
        return figure.to_image(format=format, width=1200, height=700, scale=scale if format == "png" else 1)
    except Exception as exc:
        raise ExportError("Chart export requires Kaleido and a discoverable Chromium/Chrome installation.") from exc
