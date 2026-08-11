"""Generate deterministic synthetic data for development only."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate(path: Path, rows: int = 2000, seed: int = 42) -> None:
    """Write a realistic, explicitly synthetic e-commerce CSV."""
    rng = np.random.default_rng(seed)
    categories = {"Technology": ["Phones", "Accessories", "Machines"], "Furniture": ["Chairs", "Tables", "Bookcases"], "Office Supplies": ["Paper", "Binders", "Storage"]}
    regions = {"North": ["Canada", "United Kingdom"], "South": ["Brazil", "Australia"], "East": ["India", "Japan"], "West": ["United States", "Germany"]}
    start = pd.Timestamp("2023-01-01")
    records = []
    for index in range(rows):
        category = rng.choice(list(categories))
        region = rng.choice(list(regions))
        country = rng.choice(regions[region])
        quantity = int(rng.integers(1, 12))
        discount = float(rng.choice([0, 0.05, 0.1, 0.2, 0.3, 0.5], p=[0.25, 0.15, 0.2, 0.2, 0.15, 0.05]))
        sales = float(max(8, rng.lognormal(5.2, 0.85) * quantity / 4))
        profit = float(sales * (rng.normal(0.18, 0.12) - discount * 0.65))
        order_date = start + pd.Timedelta(days=int(rng.integers(0, 1095)))
        records.append({
            "Order ID": f"DEMO-{index + 1:05d}", "Order Date": order_date.date(), "Ship Date": (order_date + pd.Timedelta(days=int(rng.integers(1, 8)))).date(),
            "Product Category": category, "Sub-Category": rng.choice(categories[category]), "Customer Segment": rng.choice(["Consumer", "Corporate", "Home Office"]),
            "Region": region, "Country": country, "City": f"Demo City {int(rng.integers(1, 31))}", "Sales": round(sales, 2), "Quantity": quantity,
            "Discount": discount, "Profit": round(profit, 2), "Ship Mode": rng.choice(["Standard Class", "Second Class", "First Class", "Same Day"]),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame.from_records(records).to_csv(path, index=False)


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1] / "data" / "sample" / "demo_ecommerce_sales.csv")
