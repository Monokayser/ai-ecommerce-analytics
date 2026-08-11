"""AI analysis report export section."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from src.models import DatasetBundle, ReportPayload
from src.reporting.pdf_report import generate_pdf_report
from src.reporting.word_report import generate_word_report
from src.ui.theme import render_section_intro


def render(bundle: DatasetBundle) -> None:
    """Generate downloadable PDF and Word reports from the last AI result."""
    render_section_intro("Package the evidence", "Report Export", "Create decision-ready PDF and Word reports from the last validated assistant result.")
    last = st.session_state.get("last_ai")
    if not last:
        st.info("Run an AI Assistant query first to create an analysis report.")
        return
    payload = ReportPayload(
        project_title="AI-Powered E-Commerce Data Analytics and Visualization Platform",
        dataset_name=bundle.metadata.name,
        dataset_dimensions=f"{bundle.metadata.rows:,} rows x {bundle.metadata.columns} columns",
        generated_at=datetime.now(timezone.utc),
        applied_filters=last["filters"],
        question=last["question"],
        generated_query=last["generated"].query,
        query_execution_time_ms=last["result"].execution_time_ms,
        result_table=last["result"].data,
        narrative=last["narrative"].analysis,
        key_findings=last["narrative"].key_findings,
        limitations=last["narrative"].limitations,
        chart_image=st.session_state.get("last_chart_png"),
    )
    try:
        pdf = generate_pdf_report(payload)
        word = generate_word_report(payload)
    except Exception as exc:
        st.error(str(exc))
        return
    first, second = st.columns(2)
    first.download_button("Download PDF report", pdf, "ai_analysis_report.pdf", "application/pdf", use_container_width=True)
    second.download_button("Download Word report", word, "ai_analysis_report.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
