"""Generate temporary chart, Word, and PDF artifacts for visual QA."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models import ReportPayload
from src.reporting.pdf_report import generate_pdf_report
from src.reporting.word_report import generate_word_report
from src.visualization.charts import grouped_bar_chart
from src.visualization.export import export_chart


def main() -> None:
    """Create deterministic QA artifacts under the ignored tmp directory."""
    root = ROOT
    output = root / "tmp" / "qa"
    output.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(root / "data" / "sample" / "demo_ecommerce_sales.csv")
    grouped = frame.groupby("Region", as_index=False)[["Sales", "Profit"]].sum().sort_values("Sales", ascending=False)
    figure = grouped_bar_chart(frame, "Region", "Source: deterministic development dataset | QA only")
    png = export_chart(figure, "png")
    svg = export_chart(figure, "svg")
    (output / "qa_chart.png").write_bytes(png)
    (output / "qa_chart.svg").write_bytes(svg)
    payload = ReportPayload(
        project_title="AI-Powered E-Commerce Data Analytics and Visualization Platform",
        dataset_name="demo_ecommerce_sales.csv (synthetic development data)",
        dataset_dimensions=f"{len(frame):,} rows x {len(frame.columns)} columns",
        generated_at=datetime.now(timezone.utc),
        applied_filters={"Region": ["East", "West"]},
        question="Which region has the highest total sales?",
        generated_query='SELECT "Region", SUM("Sales") AS "Total Sales" FROM dataset GROUP BY "Region" ORDER BY "Total Sales" DESC',
        query_execution_time_ms=8.42,
        result_table=grouped,
        narrative="The validated aggregation ranks regions by total sales and reports profit alongside the sales result.",
        key_findings=["Regions are compared using the same aggregation.", "The chart and table use the verified query result."],
        limitations="Synthetic development data cannot support real business conclusions.",
        chart_image=png,
    )
    (output / "qa_report.docx").write_bytes(generate_word_report(payload))
    (output / "qa_report.pdf").write_bytes(generate_pdf_report(payload))
    print(output)


if __name__ == "__main__":
    main()
