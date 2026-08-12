"""Reference-inspired AI agent workspace with secure, verified execution."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from config.settings import Settings
from src.data.query_engine import QueryEngine
from src.llm.conversation import ConversationMemory, Interaction
from src.llm.nl_query import NLQueryPipeline
from src.models import ChartSpec, DatasetBundle, ReportPayload
from src.reporting.pdf_report import generate_pdf_report
from src.reporting.word_report import generate_word_report
from src.ui.brand import inline_brand_icon
from src.ui.components import render_empty
from src.visualization.chart_selector import select_chart
from src.visualization.charts import result_chart
from src.visualization.export import export_chart


CAPABILITIES = [
    (
        "💡 Generate Commerce Insights",
        "Find the strongest market and the value behind it.",
        "Which region has the highest total sales?",
    ),
    (
        "🛡️ Profitability & Risk Analysis",
        "Surface loss-making countries before they become larger risks.",
        "Which countries generated losses?",
    ),
    (
        "📋 Executive Recommendations",
        "Rank profitable product areas for an executive decision.",
        "What are the five most profitable sub-categories?",
    ),
    (
        "🔎 Root Cause Investigation",
        "Investigate high-discount orders associated with losses.",
        "Find unusual orders with high discounts and negative profit.",
    ),
]

FOLLOW_UPS = [
    ("↻ Repeat", None),
    ("⌁ Track momentum", "Show monthly sales and profit trends."),
    ("↗ Find profit drivers", "Which product category has the highest profit?"),
    ("△ Scan downside", "Which countries generated losses?"),
]


def _generate_report_files(payload: ReportPayload) -> tuple[bytes, bytes]:
    """Build the Word and PDF versions of one verified response."""
    return generate_word_report(payload), generate_pdf_report(payload)


def _report_cache_key(payload: ReportPayload) -> str:
    """Create a stable key without asking Streamlit to hash a Pydantic/DataFrame graph."""
    digest = hashlib.sha256()
    digest.update(payload.question.encode("utf-8"))
    digest.update(payload.generated_query.encode("utf-8"))
    digest.update(payload.generated_at.isoformat().encode("utf-8"))
    digest.update(payload.result_table.to_csv(index=False).encode("utf-8"))
    digest.update(payload.chart_image or b"")
    return digest.hexdigest()


def _override_spec(frame: pd.DataFrame, auto: ChartSpec, selected: str) -> ChartSpec:
    if selected == "Auto-selected":
        return auto
    numeric = list(frame.select_dtypes(include="number").columns)
    other = [column for column in frame.columns if column not in numeric]
    if selected == "Table only":
        return ChartSpec(chart_type="table", title="Detailed result")
    if selected == "Scatter" and len(numeric) >= 2:
        return ChartSpec(chart_type="scatter", x=numeric[0], y=[numeric[1]], title="Numeric relationship")
    if selected == "Line" and other and numeric:
        return ChartSpec(chart_type="line", x=other[0], y=numeric[:3], title="Result trend")
    if selected == "Bar" and other and numeric:
        return ChartSpec(chart_type="bar", x=other[0], y=numeric[:2], title="Result comparison")
    return auto


def _active_pipeline(pipeline: NLQueryPipeline, profile: str) -> NLQueryPipeline:
    """Return the configured pipeline or a guaranteed-private local profile."""
    if profile == "Private local analytics":
        return NLQueryPipeline(pipeline.settings, None, pipeline.prompts, pipeline.aliases)
    return pipeline


def _model_profiles(pipeline: NLQueryPipeline) -> list[str]:
    profiles = ["Private local analytics"]
    if pipeline.client is not None:
        profiles.append(f"{pipeline.mode_label} · {pipeline.model_label}")
    return profiles


def _render_mode_card(
    pipeline: NLQueryPipeline,
    frame: pd.DataFrame,
    filters: dict[str, Any],
    analysis_mode: str,
) -> None:
    if pipeline.client is not None:
        description = "Your selected AI model interprets the request. The application validates every plan and only runs approved, read-only analysis."
        provider_state = "AI interpretation enabled"
    else:
        description = "Common e-commerce questions are answered on this machine. No API key is needed and no dataset content is sent to an AI provider."
        provider_state = "Data stays on this device"
    st.markdown(
        f"""<div class="mode-card"><div class="mode-orb">{inline_brand_icon('ai-mode-icon')}</div><div><strong>{escape(pipeline.mode_label)} · {escape(pipeline.model_label)}</strong><br><span>{escape(description)}</span><div class="mode-meta"><b>{escape(analysis_mode)} detail</b><b>{escape(provider_state)}</b><b>{len(frame):,} rows in scope</b><b>{len(filters)} active filters</b><b>Verified read-only analysis</b></div></div></div>""",
        unsafe_allow_html=True,
    )


def _render_pipeline_trace(last: dict[str, Any], pipeline: NLQueryPipeline) -> None:
    metrics = last.get("pipeline_metrics", pipeline.last_run_metrics)
    stages = [
        ("1", "Understand", "Question + filters"),
        ("2", "Plan", f"Prepared in {float(metrics.get('planning_ms', 0)):,.0f} ms"),
        ("3", "Safety check", "Read-only plan approved"),
        ("4", "Analyze", f"Completed in {float(metrics.get('execution_ms', 0)):,.1f} ms"),
        ("5", "Answer", "Grounded in results"),
    ]
    items = "".join(
        f'<div class="ai-stage"><span>{number}</span><strong>{escape(label)}</strong><small>{escape(detail)}</small></div>'
        for number, label, detail in stages
    )
    st.markdown(f'<div class="ai-pipeline" aria-label="Completed AI pipeline">{items}</div>', unsafe_allow_html=True)


def _render_history(memory: ConversationMemory) -> None:
    records = memory.as_list()
    if not records:
        st.caption("No conversation yet. The last five verified interactions will appear here.")
        return
    for index, item in enumerate(reversed(records), start=1):
        with st.expander(f"{item['question'][:56]}{'…' if len(item['question']) > 56 else ''}", expanded=index == 1):
            st.caption(item["result_summary"])
            st.write(item["answer"])
            if st.button("Ask again", key=f"history_again_{index}", use_container_width=True):
                st.session_state["pending_ai_question"] = item["question"]
                st.rerun()


def _save_last_response(last: dict[str, Any]) -> None:
    saved = list(st.session_state.get("saved_ai_responses", []))
    record = {
        "saved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "question": str(last["question"]),
        "answer": str(last["narrative"].direct_answer),
        "result_summary": f"{len(last['result'].data):,} rows · {last['result'].execution_time_ms:.1f} ms",
    }
    if not saved or saved[-1]["question"] != record["question"] or saved[-1]["answer"] != record["answer"]:
        saved.append(record)
    st.session_state["saved_ai_responses"] = saved[-10:]


def _render_saved_responses() -> None:
    saved = list(st.session_state.get("saved_ai_responses", []))
    if not saved:
        st.caption("Save a verified response to keep it in this browser session.")
        return
    for index, record in enumerate(reversed(saved), start=1):
        st.markdown(f"**{escape(record['question'])}**")
        st.caption(f"{record['saved_at']} · {record['result_summary']}")
        st.write(record["answer"])
        if st.button("Run this task again", key=f"saved_again_{index}", use_container_width=True):
            st.session_state["pending_ai_question"] = record["question"]
            st.rerun()
        st.divider()


def _report_payload(bundle: DatasetBundle, last: dict[str, Any]) -> ReportPayload:
    return ReportPayload(
        project_title="AI-Powered E-Commerce Data Analytics and Visualization Platform",
        dataset_name=bundle.metadata.name,
        dataset_dimensions=f"{bundle.metadata.rows:,} rows x {bundle.metadata.columns} columns",
        generated_at=last.get("completed_at", datetime.now(timezone.utc)),
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


def _render_response_toolbar(bundle: DatasetBundle, last: dict[str, Any] | None) -> None:
    st.markdown("### 🤖 Verified response")
    save_column, word_column, pdf_column = st.columns(3)
    if not last:
        save_column.button("Save response", disabled=True, use_container_width=True, help="Save this response in the current session")
        word_column.button("Download Word", disabled=True, use_container_width=True, help="Download a Word report")
        pdf_column.button("Download PDF", disabled=True, use_container_width=True, help="Download a PDF report")
        return
    if save_column.button("Save response", use_container_width=True, key="save_ai_response", help="Save this response in the current session"):
        _save_last_response(last)
        st.toast("Verified response saved in this session", icon="✅")
    try:
        payload = _report_payload(bundle, last)
        cache_key = _report_cache_key(payload)
        cached = st.session_state.get("ai_report_files")
        if not cached or cached.get("key") != cache_key:
            word, pdf = _generate_report_files(payload)
            cached = {"key": cache_key, "word": word, "pdf": pdf}
            st.session_state["ai_report_files"] = cached
        word, pdf = cached["word"], cached["pdf"]
        word_column.download_button(
            "Download Word",
            word,
            "ai_verified_response.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            help="Download a Word report",
        )
        pdf_column.download_button(
            "Download PDF",
            pdf,
            "ai_verified_response.pdf",
            "application/pdf",
            use_container_width=True,
            help="Download a PDF report",
        )
    except Exception as exc:
        word_column.button("Download Word", disabled=True, use_container_width=True, help="Word export is temporarily unavailable")
        pdf_column.button("Download PDF", disabled=True, use_container_width=True, help="PDF export is temporarily unavailable")
        st.caption(f"Report downloads are temporarily unavailable. {type(exc).__name__}.")


def _render_last_result(last: dict[str, Any], pipeline: NLQueryPipeline) -> None:
    generated, result, narrative = last["generated"], last["result"], last["narrative"]
    _render_pipeline_trace(last, pipeline)
    st.markdown(
        f'<div class="answer-card"><div class="answer-eyebrow">Verified AI answer</div><h3>{escape(narrative.direct_answer)}</h3><p>{escape(narrative.analysis)}</p><div class="trust-row"><span class="trust-pill safe">✓ Query validated</span><span class="trust-pill">{escape(str(last.get("pipeline_metrics", {}).get("analysis_mode", "Balanced")))} mode</span><span class="trust-pill">Read-only dataset access</span><span class="trust-pill">Evidence grounded</span><span class="trust-pill">{len(result.data):,} result rows</span></div></div>',
        unsafe_allow_html=True,
    )
    answer_tab, chart_tab, data_tab, evidence_tab = st.tabs(["✦ Answer", "⌁ Chart", "▦ Data", "✓ How it was verified"])
    with answer_tab:
        st.subheader("Key findings")
        for finding in narrative.key_findings:
            st.markdown(f"- {finding}")
        st.info("Limitation · " + narrative.limitations)
    with chart_tab:
        if result.data.empty:
            render_empty("A chart needs at least one result row.")
        else:
            auto = select_chart(result.data)
            choice = st.selectbox("Choose how to show this result", ["Recommended", "Bar chart", "Line chart", "Scatter plot", "Table only"], index=0)
            choice_map = {"Recommended": "Auto-selected", "Bar chart": "Bar", "Line chart": "Line", "Scatter plot": "Scatter", "Table only": "Table only"}
            spec = _override_spec(result.data, auto, choice_map[choice])
            st.caption(f"Recommended view: {spec.chart_type} · {spec.rationale or generated.reason}")
            figure = result_chart(result.data, spec)
            if figure is None:
                st.dataframe(result.data, use_container_width=True, hide_index=True)
            else:
                st.plotly_chart(figure, use_container_width=True)
                st.caption(narrative.chart_caption)
                if st.button("Prepare chart downloads", use_container_width=True, key="prepare_ai_chart_exports"):
                    try:
                        with st.spinner("Preparing high-quality PNG and SVG files…"):
                            png = export_chart(figure, "png")
                            svg = export_chart(figure, "svg")
                        st.session_state["ai_chart_png"] = png
                        st.session_state["ai_chart_svg"] = svg
                        st.session_state["last_chart_png"] = png
                    except Exception as exc:
                        st.info(str(exc))
                png = st.session_state.get("ai_chart_png")
                svg = st.session_state.get("ai_chart_svg")
                if png and svg:
                    first, second = st.columns(2)
                    first.download_button("Download PNG", png, "ai_query_chart.png", "image/png", use_container_width=True)
                    second.download_button("Download SVG", svg, "ai_query_chart.svg", "image/svg+xml", use_container_width=True)
    with data_tab:
        if result.data.empty:
            render_empty("The verified analysis returned no matching rows.")
        else:
            st.dataframe(result.data, use_container_width=True, hide_index=True)
            st.download_button(
                "Download result as CSV",
                result.data.to_csv(index=False).encode("utf-8"),
                "ai_query_result.csv",
                "text/csv",
                use_container_width=True,
            )
    with evidence_tab:
        metrics = last.get("pipeline_metrics", pipeline.last_run_metrics)
        cards = st.columns(3)
        cards[0].metric("Answer detail", str(metrics.get("analysis_mode", "Balanced")))
        cards[1].metric("Total time", f"{float(metrics.get('total_ms', 0)):,.1f} ms")
        cards[2].metric("Rows returned", f"{len(result.data):,}")
        correction = "one safe correction was used" if metrics.get("corrected") else "no correction was needed"
        st.caption(
            f"Query time: {result.execution_time_ms:,.1f} ms · Model passes: {int(metrics.get('model_calls', 0))} · {correction}."
        )
        if metrics.get("provider_fallback"):
            st.warning("The configured model was unavailable, so this answer used the safe local fallback. " + str(metrics.get("fallback_reason", "")))
        st.success("Safety check passed · read-only dataset access · time and result limits applied")
        st.markdown("**What the assistant understood**")
        st.write(generated.interpreted_question)
        with st.expander("View the validated query and technical details"):
            st.code(generated.query, language="sql" if generated.query_language == "duckdb_sql" else "python")
            st.json(
                {
                    "analysis engine": metrics.get("mode", pipeline.mode_label),
                    "model": metrics.get("model", pipeline.model_label),
                    "columns used": generated.columns_used,
                    "filters used": generated.filters_used,
                    "operation": generated.aggregation,
                    "chart rationale": generated.reason,
                }
            )


def _run_question(
    question: str,
    bundle: DatasetBundle,
    frame: pd.DataFrame,
    filters: dict[str, Any],
    settings: Settings,
    pipeline: NLQueryPipeline,
    memory: ConversationMemory,
    analysis_mode: str,
) -> None:
    st.session_state.pop("ai_chart_png", None)
    st.session_state.pop("ai_chart_svg", None)
    st.session_state.pop("last_chart_png", None)
    st.session_state.pop("ai_report_files", None)
    engine = QueryEngine(frame, max_rows=settings.max_result_rows, timeout_seconds=settings.query_timeout_seconds)
    with st.status(f"AI agent is working in {analysis_mode.lower()} mode…", expanded=True) as status:
        stage_icons = {"planning": "①", "validation": "②", "execution": "③", "narrative": "④"}

        def report_progress(stage: str, message: str) -> None:
            if stage != "complete":
                st.write(f"{stage_icons.get(stage, '·')} {message}")

        try:
            generated, result, narrative, _ = pipeline.run(
                question,
                engine,
                bundle.schema_profile,
                filters=filters,
                history=memory.prompt_context(),
                analysis_mode=analysis_mode,
                progress=report_progress,
            )
            status.update(label="Verified response ready", state="complete", expanded=False)
        except Exception as exc:
            status.update(label="Analysis stopped safely", state="error")
            st.error(str(exc))
            return
    memory.append(
        Interaction(
            question,
            generated.interpreted_question,
            generated.query,
            filters,
            f"{len(result.data)} rows · {result.execution_time_ms:.1f} ms",
            narrative.direct_answer,
        )
    )
    st.session_state["conversation"] = memory.as_list()
    st.session_state["last_ai"] = {
        "question": question,
        "generated": generated,
        "result": result,
        "narrative": narrative,
        "filters": filters,
        "pipeline_metrics": pipeline.last_run_metrics.copy(),
        "completed_at": datetime.now(timezone.utc),
    }
    st.toast(f"{pipeline.mode_label} task completed", icon="✅")


def _render_followups(last: dict[str, Any]) -> None:
    st.markdown("#### Continue the investigation")
    columns = st.columns(4)
    for column, (label, configured_question) in zip(columns, FOLLOW_UPS, strict=False):
        question = str(last.get("question", "")) if configured_question is None else configured_question
        if column.button(label, help=question, use_container_width=True, key=f"followup_{label}"):
            st.session_state["pending_ai_question"] = question
            st.rerun()


def render(
    bundle: DatasetBundle,
    frame: pd.DataFrame,
    filters: dict[str, Any],
    settings: Settings,
    pipeline: NLQueryPipeline,
) -> None:
    """Render a reference-inspired agent console with secure task execution."""
    st.markdown(
        """<section class="ai-workspace-intro">
        <div class="section-kicker">Ask · act · validate</div>
        <h2>AI Assistant</h2>
        <p>Ask in everyday language or choose a guided task. Every answer is checked against the active dataset before you see it.</p>
        </section>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """<div class="ai-guide" aria-label="How to use the AI assistant">
        <div><span>1</span><strong>Choose or ask</strong><small>Select a ready-made task or write your own question.</small></div>
        <div><span>2</span><strong>Review the answer</strong><small>See the result, chart, data, and verification status.</small></div>
        <div><span>3</span><strong>Save or export</strong><small>Keep the response or download a report for submission.</small></div>
        </div>""",
        unsafe_allow_html=True,
    )

    profiles = _model_profiles(pipeline)
    with st.expander("⚙️ Agent settings and privacy", expanded=False):
        model_control, mode_control, reset_control = st.columns([2.1, 1.2, 1])
        selected_profile = model_control.selectbox(
            "Analysis engine",
            profiles,
            index=len(profiles) - 1,
            key="ai_model_profile",
            help="Private local analytics stays on this device. A configured model understands a wider range of questions.",
        )
        analysis_mode = mode_control.selectbox(
            "Answer detail",
            ["Fast", "Balanced", "Deep"],
            index=1,
            key="ai_analysis_mode",
            help="Fast gives a short answer. Balanced includes context. Deep provides the most detailed interpretation.",
        )
        if reset_control.button("Reset agent", use_container_width=True, key="reset_ai_agent"):
            for key in (
                "conversation",
                "last_ai",
                "last_chart_png",
                "ai_chart_png",
                "ai_chart_svg",
                "saved_ai_responses",
                "pending_ai_question",
                "ai_query_draft",
                "ai_report_files",
            ):
                st.session_state.pop(key, None)
            st.rerun()

        active_pipeline = _active_pipeline(pipeline, selected_profile)
        _render_mode_card(active_pipeline, frame, filters, analysis_mode)
    memory = ConversationMemory(st.session_state.get("conversation", []))
    pending = st.session_state.pop("pending_ai_question", None)

    capability_panel, response_panel = st.columns([0.38, 0.62], gap="large", vertical_alignment="top")
    requested_question: str | None = pending

    with capability_panel:
        with st.container(border=True):
            st.markdown("### 🤖 AI Capabilities")
            st.caption("Choose a ready-made investigation. It runs immediately using the current filters.")
            for label, help_text, question in CAPABILITIES:
                if st.button(label, help=help_text, use_container_width=True, key=f"capability_{label}"):
                    requested_question = question
            st.divider()
            st.markdown("#### 💬 Ask your own question")
            scope_text = f"Using {len(frame):,} rows" + (f" with {len(filters)} active filter(s)." if filters else " with no filters.")
            st.caption(scope_text + " Current filters always take priority over earlier conversation.")
            with st.form("ai_task_form", border=False):
                draft = st.text_area(
                    "Your question",
                    key="ai_query_draft",
                    height=132,
                    max_chars=settings.question_max_chars,
                    placeholder="Example: Compare sales and profit by region and rank the results.",
                    help="Ask about sales, profit, customers, products, countries, regions, discounts, or trends.",
                )
                if st.form_submit_button("Analyze my question", type="primary", use_container_width=True):
                    requested_question = draft
            st.divider()
            with st.expander("💾 Saved Responses", expanded=False):
                _render_saved_responses()
            with st.expander("🕘 Recent conversation", expanded=False):
                _render_history(memory)

    with response_panel:
        last_before_run = st.session_state.get("last_ai")
        if requested_question and requested_question.strip():
            _run_question(
                requested_question.strip(),
                bundle,
                frame,
                filters,
                settings,
                active_pipeline,
                memory,
                analysis_mode,
            )
        elif requested_question is not None:
            st.warning("Enter a natural-language task before running the agent.")

        last = st.session_state.get("last_ai", last_before_run)
        with st.container(border=True):
            _render_response_toolbar(bundle, last)
            st.divider()
            if last:
                _render_last_result(last, active_pipeline)
            else:
                st.markdown(
                    '<div class="ai-response-empty" role="status"><span>✦</span><h3>What would you like to understand?</h3><p>Choose a guided task or ask your own business question. Your verified answer, chart, source data, and safety checks will appear here.</p><div class="empty-hint">Try: “Which category has the highest profit?”</div></div>',
                    unsafe_allow_html=True,
                )
        if last:
            _render_followups(last)
