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
        st.markdown(
            '<div class="empty-state" role="status"><span class="empty-icon">↗</span><strong>No verified analysis is ready yet.</strong><br>Run a question in the AI Assistant, then return here to package its evidence.</div>',
            unsafe_allow_html=True,
        )
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
    signature = (last["question"], last["generated"].query, len(last["result"].data))
    if st.session_state.get("report_package_signature") != signature:
        st.session_state.pop("report_pdf", None)
        st.session_state.pop("report_word", None)
    if st.button("Prepare report package", type="primary", width="stretch"):
        try:
            with st.spinner("Building the verified PDF and Word package..."):
                st.session_state["report_pdf"] = generate_pdf_report(payload)
                st.session_state["report_word"] = generate_word_report(payload)
                st.session_state["report_package_signature"] = signature
        except Exception as exc:
            st.error(str(exc))
            return
    pdf = st.session_state.get("report_pdf")
    word = st.session_state.get("report_word")
    if not pdf or not word:
        st.info("Reports are generated only when requested, keeping navigation and reruns fast.")
        return
    st.success("Report package ready · validated query, filters, findings, evidence table, timing, and limitations included")
    first, second = st.columns(2)
    first.download_button("Download PDF report", pdf, "ai_analysis_report.pdf", "application/pdf", width="stretch")
    second.download_button("Download Word report", word, "ai_analysis_report.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", width="stretch")
