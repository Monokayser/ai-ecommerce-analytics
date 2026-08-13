"""Dataset selection and global filter controls."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


FILTER_DIMENSIONS = ["Region", "Country", "Product Category", "Sub-Category", "Customer Segment", "Ship Mode"]


def build_filter_profile(frame: pd.DataFrame) -> dict[str, Any]:
    """Precompute filter choices and bounds once during cached dataset preparation."""
    options = {
        column: sorted(str(value) for value in frame[column].dropna().unique())
        for column in FILTER_DIMENSIONS
        if column in frame
    }
    date_bounds = None
    if "Order Date" in frame and frame["Order Date"].notna().any():
        date_bounds = (pd.Timestamp(frame["Order Date"].min()).date(), pd.Timestamp(frame["Order Date"].max()).date())
    numeric_bounds: dict[str, tuple[float, float]] = {}
    for column in ("Sales", "Profit"):
        if column in frame and frame[column].notna().any():
            numeric_bounds[column] = (float(frame[column].min()), float(frame[column].max()))
    return {"options": options, "date_bounds": date_bounds, "numeric_bounds": numeric_bounds}


def render_filters(frame: pd.DataFrame, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Render available global filters and return active selections."""
    profile = profile or build_filter_profile(frame)
    options_by_column = profile.get("options", {})
    st.sidebar.subheader("Global filters")
    st.sidebar.caption("Shape every page and AI answer from one place.")
    active: dict[str, Any] = {}
    with st.sidebar.expander("Dimensions", expanded=True):
        for column in FILTER_DIMENSIONS:
            if column in frame:
                options = options_by_column.get(column, [])
                chosen = st.multiselect(column, options, key=f"filter_{column}")
                if chosen:
                    active[column] = chosen
    with st.sidebar.expander("Date and value ranges", expanded=False):
        date_bounds = profile.get("date_bounds")
        if date_bounds:
            minimum, maximum = date_bounds
            chosen_dates = st.date_input("Order date range", (minimum, maximum), min_value=minimum, max_value=maximum, key="filter_dates")
            if isinstance(chosen_dates, (tuple, list)) and len(chosen_dates) == 2 and tuple(chosen_dates) != (minimum, maximum):
                active["Order Date"] = tuple(chosen_dates)
        for column in ("Sales", "Profit"):
            if column in profile.get("numeric_bounds", {}):
                minimum, maximum = profile["numeric_bounds"][column]
                if minimum < maximum:
                    chosen = st.slider(f"{column} range", minimum, maximum, (minimum, maximum), key=f"filter_range_{column}")
                    if chosen != (minimum, maximum):
                        active[column] = chosen
    st.sidebar.caption(f"{len(active)} filter groups active" if active else "All data is currently in scope")
    if st.sidebar.button("Reset filters", width="stretch"):
        for key in list(st.session_state):
            if key.startswith("filter_"):
                del st.session_state[key]
        st.rerun()
    return active


def apply_filters(frame: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    """Apply all filters through one vectorized mask and a copy-on-write view."""
    if not filters:
        return frame.copy(deep=False)
    mask = pd.Series(True, index=frame.index, dtype=bool)
    for column, value in filters.items():
        if column == "Order Date":
            start, end = value
            mask &= frame[column].between(pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1))
        elif column in ("Sales", "Profit"):
            mask &= frame[column].between(value[0], value[1])
        else:
            mask &= frame[column].astype(str).isin(value)
    return frame.loc[mask].copy(deep=False).reset_index(drop=True)
