"""Shared deterministic test fixtures."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def ecommerce_frame() -> pd.DataFrame:
    """Return a small representative e-commerce DataFrame."""
    return pd.DataFrame({
        "Order ID": ["A", "B", "C", "D", "E", "F"],
        "Order Date": pd.to_datetime(["2024-01-01", "2024-01-03", "2024-02-01", "2024-02-02", "2024-03-01", "2024-03-02"]),
        "Product Category": ["Technology", "Furniture", "Technology", "Office Supplies", "Furniture", "Technology"],
        "Sub-Category": ["Phones", "Chairs", "Accessories", "Paper", "Tables", "Machines"],
        "Customer Segment": ["Consumer", "Corporate", "Consumer", "Home Office", "Corporate", "Consumer"],
        "Region": ["East", "West", "East", "South", "West", "North"],
        "Country": ["India", "United States", "India", "Brazil", "Germany", "Canada"],
        "Sales": [100.0, 200.0, 150.0, 80.0, 900.0, 120.0],
        "Quantity": [1, 2, 1, 3, 4, 1],
        "Discount": [0.0, 0.1, 0.2, 0.0, 0.5, 0.1],
        "Profit": [20.0, 30.0, 10.0, 15.0, -100.0, 18.0],
        "Ship Mode": ["Standard Class", "Second Class", "Standard Class", "First Class", "Second Class", "Same Day"],
    })
