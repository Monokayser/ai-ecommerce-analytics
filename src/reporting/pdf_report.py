"""ReportLab PDF analytics report with repeated table headers and page furniture."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, KeepTogether, LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models import ReportPayload
from src.utils.exceptions import ExportError

NAVY = colors.HexColor("#0B2545")
TEAL = colors.HexColor("#0F766E")
MUTED = colors.HexColor("#64748B")


def _safe(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_pdf_report(payload: ReportPayload) -> bytes:
    """Generate a polished static PDF report and return its bytes."""
    try:
        buffer = BytesIO()

        def page_furniture(canvas, document) -> None:
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(MUTED)
            canvas.drawString(inch, 10.45 * inch, "AI E-COMMERCE ANALYTICS | VERIFIED QUERY REPORT")
            canvas.drawRightString(7.5 * inch, 0.55 * inch, f"Page {document.page}")
            canvas.restoreState()

        document = SimpleDocTemplate(
            buffer, pagesize=letter, rightMargin=inch, leftMargin=inch, topMargin=0.9 * inch, bottomMargin=0.8 * inch,
            title=payload.project_title, author="AI E-Commerce Analytics Platform",
        )
        base = getSampleStyleSheet()
        title_style = ParagraphStyle("ReportTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=23, leading=27, textColor=NAVY, alignment=TA_LEFT, spaceAfter=5)
        subtitle_style = ParagraphStyle("Subtitle", parent=base["Normal"], fontSize=13, textColor=TEAL, spaceAfter=14)
        h1 = ParagraphStyle("H1", parent=base["Heading1"], fontSize=16, leading=19, textColor=TEAL, spaceBefore=16, spaceAfter=8)
        h2 = ParagraphStyle("H2", parent=base["Heading2"], fontSize=13, leading=16, textColor=NAVY, spaceBefore=12, spaceAfter=6)
        body = ParagraphStyle("Body", parent=base["BodyText"], fontSize=10.5, leading=14, spaceAfter=6)
        code = ParagraphStyle("Code", parent=body, fontName="Courier", fontSize=8.5, leading=11, backColor=colors.HexColor("#F2F4F7"), borderPadding=8)
        story = [Paragraph(_safe(payload.project_title), title_style), Paragraph("AI Assistant Analysis Report", subtitle_style)]
        metadata_rows = [
            ["Dataset", _safe(payload.dataset_name)], ["Dimensions", _safe(payload.dataset_dimensions)],
            ["Generated", payload.generated_at.strftime("%Y-%m-%d %H:%M UTC")], ["Query time", f"{payload.query_execution_time_ms:.2f} ms"],
            ["Applied filters", _safe(", ".join(f"{k}={v}" for k, v in payload.applied_filters.items()) or "None")],
        ]
        metadata = Table(metadata_rows, colWidths=[1.45 * inch, 5.05 * inch], hAlign="LEFT")
        metadata.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F4F7")), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story.extend([metadata, Paragraph("Question and Validated Query", h1), Paragraph(_safe(payload.question), body), Paragraph(_safe(payload.generated_query), code), Paragraph("Result", h1)])
        data = payload.result_table.head(50)
        if len(data.columns):
            rows = [[Paragraph(f"<b>{_safe(column)}</b>", body) for column in data.columns]]
            rows.extend([[Paragraph(_safe(value)[:140], body) for value in row] for row in data.astype(object).where(data.notna(), "").itertuples(index=False, name=None)])
            widths = [6.5 * inch / len(data.columns)] * len(data.columns)
            result_table = LongTable(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
            result_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDECEB")), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
            story.append(result_table)
        else:
            story.append(Paragraph("No rows matched the query.", body))
        if len(payload.result_table) > 50:
            story.append(Paragraph("Table truncated to the first 50 rows for readability.", body))
        if payload.chart_image:
            chart = Image(BytesIO(payload.chart_image), width=6.5 * inch, height=3.79 * inch)
            story.extend([PageBreak(), KeepTogether([Paragraph("Visualization", h1), chart])])
        story.extend([Paragraph("Analysis", h1), Paragraph(_safe(payload.narrative), body), Paragraph("Key Findings", h2)])
        for finding in payload.key_findings:
            story.append(Paragraph("&#8226; " + _safe(finding), body))
        story.extend([Paragraph("Limitations", h2), Paragraph(_safe(payload.limitations), body), Spacer(1, 12), Paragraph("<b>Important:</b> " + _safe(payload.disclaimer), ParagraphStyle("Disclaimer", parent=body, textColor=colors.HexColor("#7A5A00"), backColor=colors.HexColor("#FFF8E1"), borderPadding=8))])
        document.build(story, onFirstPage=page_furniture, onLaterPages=page_furniture)
        result = buffer.getvalue()
        if payload.output_path:
            payload.output_path.parent.mkdir(parents=True, exist_ok=True)
            payload.output_path.write_bytes(result)
        return result
    except Exception as exc:
        raise ExportError("PDF report generation failed.") from exc
