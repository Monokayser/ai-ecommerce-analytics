"""Dataset selection and global filter controls."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


FILTER_DIMENSIONS = ["Region", "Country", "Product Category", "Sub-Category", "Customer Segment", "Ship Mode"]


def render_filters(frame: pd.DataFrame) -> dict[str, Any]:
    """Render available global filters and return active selections."""
    st.sidebar.subheader("Global filters")
    st.sidebar.caption("Shape every page and AI answer from one place.")
    active: dict[str, Any] = {}
    with st.sidebar.expander("Dimensions", expanded=True):
        for column in FILTER_DIMENSIONS:
            if column in frame:
                options = sorted(str(value) for value in frame[column].dropna().unique())
                chosen = st.multiselect(column, options, key=f"filter_{column}")
                if chosen:
                    active[column] = chosen
    with st.sidebar.expander("Date and value ranges", expanded=False):
        if "Order Date" in frame and frame["Order Date"].notna().any():
            minimum = pd.Timestamp(frame["Order Date"].min()).date()
            maximum = pd.Timestamp(frame["Order Date"].max()).date()
            chosen_dates = st.date_input("Order date range", (minimum, maximum), min_value=minimum, max_value=maximum, key="filter_dates")
            if isinstance(chosen_dates, (tuple, list)) and len(chosen_dates) == 2 and tuple(chosen_dates) != (minimum, maximum):
                active["Order Date"] = tuple(chosen_dates)
        for column in ("Sales", "Profit"):
            if column in frame and frame[column].notna().any():
                minimum, maximum = float(frame[column].min()), float(frame[column].max())
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
    """Apply simultaneous global filters to a copied DataFrame."""
    filtered = frame.copy(deep=True)
    for column, value in filters.items():
        if column == "Order Date":
            start, end = value
            filtered = filtered.loc[filtered[column].between(pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1))]
        elif column in ("Sales", "Profit"):
            filtered = filtered.loc[filtered[column].between(value[0], value[1])]
        else:
            filtered = filtered.loc[filtered[column].astype(str).isin(value)]
    return filtered.reset_index(drop=True)
