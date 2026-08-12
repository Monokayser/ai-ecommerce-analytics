"""Generate reproducible figures used by the capstone report and presentation."""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "generated" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#06131f"
PANEL = "#0d2233"
TEAL = "#24d1c0"
CYAN = "#67d8ff"
WHITE = "#f4f8fb"
MUTED = "#a9bbc8"
AMBER = "#f5b642"


def chart_layout(fig: go.Figure, title: str, height: int = 560) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0.04, "font": {"size": 24, "color": WHITE}},
        paper_bgcolor=NAVY,
        plot_bgcolor=NAVY,
        font={"family": "Arial", "color": WHITE, "size": 15},
        margin={"l": 75, "r": 35, "t": 85, "b": 70},
        height=height,
        legend={"orientation": "h", "y": 1.08, "x": 0.04},
    )
    fig.update_xaxes(gridcolor="#244154", zerolinecolor="#244154")
    fig.update_yaxes(gridcolor="#244154", zerolinecolor="#244154")
    return fig


def write(fig: go.Figure, name: str, width: int = 1200, height: int = 650) -> None:
    fig.write_image(OUT / name, width=width, height=height, scale=2)


def region_sales() -> None:
    labels = ["West", "North", "South", "East"]
    values = [213841.94, 201033.12, 185757.24, 185584.52]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=[TEAL, CYAN, "#5aa7bd", "#427c95"], text=[f"${v/1000:.1f}k" for v in values], textposition="outside"))
    chart_layout(fig, "Measured Sales by Region — Synthetic Demo Dataset")
    fig.update_yaxes(title="Sales (USD)", tickprefix="$", tickformat=",.0f", range=[0, 245000])
    fig.update_xaxes(title="Region")
    write(fig, "region_sales.png")


def performance() -> None:
    names = ["Sales by Region", "Profit by Category", "East Sales by Category"]
    med = [15.7956, 14.8455, 15.7186]
    p95 = [20.6105, 20.0162, 20.1737]
    fig = go.Figure()
    fig.add_bar(name="Median", x=names, y=med, marker_color=TEAL, text=[f"{v:.2f}" for v in med], textposition="outside")
    fig.add_bar(name="p95", x=names, y=p95, marker_color=CYAN, text=[f"{v:.2f}" for v in p95], textposition="outside")
    chart_layout(fig, "Warmed DuckDB Aggregation Latency — 21 Measured Runs", 600)
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Latency (milliseconds)", range=[0, 27])
    fig.add_annotation(
        x=0.99,
        y=0.96,
        xref="paper",
        yref="paper",
        text="500 ms official target is outside this scale<br><b>measured medians are 31–34× lower</b>",
        showarrow=False,
        align="right",
        bgcolor=PANEL,
        bordercolor=AMBER,
        borderwidth=1,
        font={"color": WHITE, "size": 15},
    )
    write(fig, "query_performance.png", height=700)


def anomalies() -> None:
    fig = go.Figure(go.Bar(
        x=["IQR (Profit)", "Isolation Forest (Profit)"],
        y=[12.55, 5.0],
        marker_color=[AMBER, TEAL],
        text=["251 rows", "100 rows"],
        textposition="outside",
    ))
    chart_layout(fig, "Anomaly Flags by Method — 2,000 Rows")
    fig.update_yaxes(title="Flagged share (%)", range=[0, 15])
    fig.update_xaxes(title="Method")
    write(fig, "anomaly_comparison.png")


def comparison() -> None:
    metrics = ["Sales", "Profit", "Orders", "Units", "AOV"]
    east = [185584.52 / 1000, 14924.37 / 1000, 502, 2924 / 10, 369.69]
    west = [213841.94 / 1000, 22444.72 / 1000, 491, 3069 / 10, 435.52]
    fig = go.Figure()
    fig.add_bar(name="East", x=metrics, y=east, marker_color="#427c95")
    fig.add_bar(name="West", x=metrics, y=west, marker_color=TEAL)
    chart_layout(fig, "East–West Comparison — Values Normalized for Display")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Display units (Sales/Profit in $k; Units ÷10)")
    write(fig, "east_west.png")


def testing() -> None:
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=84,
        number={"suffix": "%", "font": {"color": WHITE, "size": 58}},
        title={"text": "Statement coverage", "font": {"color": MUTED, "size": 22}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": MUTED},
            "bar": {"color": TEAL},
            "bgcolor": PANEL,
            "bordercolor": "#315066",
            "steps": [{"range": [0, 70], "color": "#102737"}, {"range": [70, 100], "color": "#173d48"}],
        },
        domain={"x": [0.0, 0.55], "y": [0.1, 0.95]},
    ))
    fig.add_trace(go.Bar(x=[72, 0, 0], y=["Tests passed", "Bandit findings", "Known vulnerabilities"], orientation="h", marker_color=[TEAL, CYAN, AMBER], text=["72", "0", "0"], textposition="outside", xaxis="x2", yaxis="y2"))
    chart_layout(fig, "Verification Summary — Local Test Workstation", 600)
    fig.update_layout(
        xaxis2={"domain": [0.65, 1.0], "range": [0, 82], "showgrid": False, "visible": False},
        yaxis2={"domain": [0.16, 0.85], "anchor": "x2", "showgrid": False},
        showlegend=False,
    )
    write(fig, "verification_summary.png", height=700)


def data_quality() -> None:
    fig = go.Figure()
    fig.add_bar(x=["Missing cells", "Exact duplicates", "Sales outlier flags", "Profit outlier flags"], y=[0, 0, 161, 251], marker_color=[CYAN, CYAN, AMBER, TEAL], text=["0", "0", "161", "251"], textposition="outside")
    chart_layout(fig, "Data-Quality Profile After Reversible Cleaning")
    fig.update_yaxes(title="Rows / cells flagged", range=[0, 285])
    write(fig, "data_quality.png")


def architecture() -> None:
    img = Image.new("RGB", (1600, 850), NAVY)
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 52)
        box_font = ImageFont.truetype("arialbd.ttf", 26)
        small_font = ImageFont.truetype("arial.ttf", 21)
    except OSError:
        title_font = box_font = small_font = ImageFont.load_default()
    draw.text((70, 45), "Secure Analytics Architecture", fill=WHITE, font=title_font)
    cols = [100, 430, 760, 1090]
    rows = [180, 410, 640]
    nodes = [
        (cols[0], rows[0], "Validated Upload", "CSV • JSON • Parquet"),
        (cols[1], rows[0], "Data Engineering", "aliases • cleaning • profiling"),
        (cols[2], rows[0], "DuckDB", "parameterized analytics"),
        (cols[3], rows[0], "Streamlit UI", "six responsive sections"),
        (cols[0], rows[1], "Natural Language", "question + explicit filters"),
        (cols[1], rows[1], "Adaptive Planner", "local • hosted • Ollama"),
        (cols[2], rows[1], "Security Gate", "Pydantic • SQL AST • safe pandas"),
        (cols[3], rows[1], "Evidence", "result • chart • narrative"),
        (cols[1], rows[2], "Advanced Analytics", "IQR • Isolation Forest • compare"),
        (cols[2], rows[2], "Reporting", "Word • PDF • PNG • SVG"),
    ]
    boxes = []
    for x, y, head, sub in nodes:
        box = (x, y, x + 280, y + 125)
        boxes.append(box)
        draw.rounded_rectangle(box, radius=24, fill=PANEL, outline=TEAL if "Security" in head else "#315066", width=4)
        draw.text((x + 22, y + 25), head, fill=WHITE, font=box_font)
        draw.text((x + 22, y + 72), sub, fill=MUTED, font=small_font)

    def arrow(start, end, color=CYAN):
        draw.line([start, end], fill=color, width=6)
        x, y = end
        draw.polygon([(x, y), (x - 17, y - 10), (x - 17, y + 10)], fill=color)

    arrow((380, 242), (430, 242)); arrow((710, 242), (760, 242)); arrow((1040, 242), (1090, 242))
    arrow((380, 472), (430, 472)); arrow((710, 472), (760, 472)); arrow((1040, 472), (1090, 472))
    arrow((900, 305), (900, 410), TEAL); arrow((900, 535), (900, 640), TEAL)
    arrow((710, 702), (760, 702)); arrow((1370, 535), (1040, 702), TEAL)
    draw.text((70, 800), "Generated from the implemented repository architecture; model output never executes directly.", fill=MUTED, font=small_font)
    img.save(OUT / "architecture.png", quality=95)


def ui_frame() -> None:
    src = ROOT / "docs" / "assets" / "dashboard-overview.jpg"
    image = Image.open(src).convert("RGB")
    canvas = Image.new("RGB", (1600, 1020), NAVY)
    image.thumbnail((1460, 820))
    canvas.paste(image, ((1600 - image.width) // 2, 135))
    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 48)
        sub_font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        title_font = sub_font = ImageFont.load_default()
    draw.text((70, 42), "Responsive Analytics Workspace", fill=WHITE, font=title_font)
    draw.text((73, 98), "Navy/teal accessible theme • persistent filters • explicit demo-data status", fill=MUTED, font=sub_font)
    canvas.save(OUT / "ui_overview.png", quality=95)


if __name__ == "__main__":
    region_sales()
    performance()
    anomalies()
    comparison()
    testing()
    data_quality()
    architecture()
    ui_frame()
    print(f"Generated assets in {OUT}")
