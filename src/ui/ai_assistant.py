"""Reference-inspired AI agent workspace with secure, verified execution."""

from __future__ import annotations

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
from src.ui.theme import render_section_intro
from src.visualization.chart_selector import select_chart
from src.visualization.charts import result_chart
from src.visualization.export import export_chart


CAPABILITIES = [
    (
        "💡 Generate Commerce Insights",
        "Identify the strongest sales market",
        "Which region has the highest total sales?",
    ),
    (
        "🛡️ Profitability & Risk Analysis",
        "Surface loss-making markets",
        "Which countries generated losses?",
    ),
    (
        "📋 Executive Recommendations",
        "Rank the most profitable product areas",
        "What are the five most profitable sub-categories?",
    ),
    (
        "🔎 Root Cause Investigation",
        "Find high-discount loss patterns",
        "Find unusual orders with high discounts and negative profit.",
    ),
]

FOLLOW_UPS = [
    ("↻ Repeat", None),
    ("⌁ Track momentum", "Show monthly sales and profit trends."),
    ("↗ Find profit drivers", "Which product category has the highest profit?"),
    ("△ Scan downside", "Which countries generated losses?"),
]


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
    if profile == "Private local planner":
        return NLQueryPipeline(pipeline.settings, None, pipeline.prompts, pipeline.aliases)
    return pipeline


def _model_profiles(pipeline: NLQueryPipeline) -> list[str]:
    profiles = ["Private local planner"]
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
        description = "Structured model planning, AST validation, read-only execution, one safe correction attempt, and evidence-grounded narration."
        provider_state = "Configured model endpoint"
    else:
        description = "A deterministic local planner handles common e-commerce tasks with no API key, network call, or model-generated code execution."
        provider_state = "Private offline mode"
    st.markdown(
        f"""<div class="mode-card"><div class="mode-orb">{inline_brand_icon('ai-mode-icon')}</div><div><strong>{escape(pipeline.mode_label)} · {escape(pipeline.model_label)}</strong><br><span>{escape(description)}</span><div class="mode-meta"><b>{escape(analysis_mode)} response</b><b>{escape(provider_state)}</b><b>{len(frame):,} active rows</b><b>{len(filters)} active filters</b><b>Read-only execution</b></div></div></div>""",
        unsafe_allow_html=True,
    )


def _render_pipeline_trace(last: dict[str, Any], pipeline: NLQueryPipeline) -> None:
    metrics = last.get("pipeline_metrics", pipeline.last_run_metrics)
    stages = [
        ("1", "Understand", "Schema + filters"),
        ("2", "Plan", f"{float(metrics.get('planning_ms', 0)):,.0f} ms"),
        ("3", "Validate", "AST allowlist"),
        ("4", "Execute", f"{float(metrics.get('execution_ms', 0)):,.1f} ms"),
        ("5", "Explain", "Verified evidence"),
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


def _render_response_toolbar(bundle: DatasetBundle, last: dict[str, Any] | None) -> None:
    st.markdown("### 🤖 AI Response")
    save_column, word_column, pdf_column = st.columns(3)
    if not last:
        save_column.button("Save", disabled=True, use_container_width=True, help="Save this response in the current session")
        word_column.button("Word", disabled=True, use_container_width=True, help="Download a Word report")
        pdf_column.button("PDF", disabled=True, use_container_width=True, help="Download a PDF report")
        return
    if save_column.button("Save", use_container_width=True, key="save_ai_response", help="Save this response in the current session"):
        _save_last_response(last)
        st.toast("Verified response saved in this session", icon="✅")
    try:
        payload = _report_payload(bundle, last)
        word = generate_word_report(payload)
        pdf = generate_pdf_report(payload)
        word_column.download_button(
            "Word",
            word,
            "ai_verified_response.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            help="Download a Word report",
        )
        pdf_column.download_button(
            "PDF",
            pdf,
            "ai_verified_response.pdf",
            "application/pdf",
            use_container_width=True,
            help="Download a PDF report",
        )
    except Exception as exc:
        word_column.button("Word", disabled=True, use_container_width=True, help="Word export is temporarily unavailable")
        pdf_column.button("PDF", disabled=True, use_container_width=True, help="PDF export is temporarily unavailable")
        st.caption(f"Report export is temporarily unavailable: {exc}")


def _render_last_result(last: dict[str, Any], pipeline: NLQueryPipeline) -> None:
    generated, result, narrative = last["generated"], last["result"], last["narrative"]
    _render_pipeline_trace(last, pipeline)
    st.markdown(
        f'<div class="answer-card"><div class="answer-eyebrow">Verified AI answer</div><h3>{escape(narrative.direct_answer)}</h3><p>{escape(narrative.analysis)}</p><div class="trust-row"><span class="trust-pill safe">✓ Query validated</span><span class="trust-pill">{escape(str(last.get("pipeline_metrics", {}).get("analysis_mode", "Balanced")))} mode</span><span class="trust-pill">Read-only dataset access</span><span class="trust-pill">Evidence grounded</span><span class="trust-pill">{len(result.data):,} result rows</span></div></div>',
        unsafe_allow_html=True,
    )
    answer_tab, evidence_tab, data_tab, chart_tab = st.tabs(["✦ Answer", "✓ Evidence & safety", "▦ Result data", "⌁ Visualization"])
    with answer_tab:
        st.subheader("Key findings")
        for finding in narrative.key_findings:
            st.markdown(f"- {finding}")
        st.info("Limitation · " + narrative.limitations)
    with evidence_tab:
        metrics = last.get("pipeline_metrics", pipeline.last_run_metrics)
        cards = st.columns(5)
        cards[0].metric("Response mode", str(metrics.get("analysis_mode", "Balanced")))
        cards[1].metric("Total time", f"{float(metrics.get('total_ms', 0)):,.1f} ms")
        cards[2].metric("Planning", f"{float(metrics.get('planning_ms', 0)):,.1f} ms")
        cards[3].metric("Execution", f"{result.execution_time_ms:,.1f} ms")
        cards[4].metric("Model passes", f"{int(metrics.get('model_calls', 0))}")
        st.caption("Correction: " + ("used once" if metrics.get("corrected") else "not needed"))
        if metrics.get("provider_fallback"):
            st.warning("The configured model was unavailable, so this answer used the safe local fallback. " + str(metrics.get("fallback_reason", "")))
        st.success("Read-only query validated · dataset table only · timeout and result limit applied")
        st.markdown("**Interpreted question**")
        st.write(generated.interpreted_question)
        st.code(generated.query, language="sql" if generated.query_language == "duckdb_sql" else "python")
        st.json(
            {
                "mode": metrics.get("mode", pipeline.mode_label),
                "model": metrics.get("model", pipeline.model_label),
                "columns": generated.columns_used,
                "filters": generated.filters_used,
                "operation": generated.aggregation,
                "chart rationale": generated.reason,
            }
        )
    with data_tab:
        if result.data.empty:
            render_empty("The validated query returned no matching rows.")
        else:
            st.dataframe(result.data, use_container_width=True, hide_index=True)
            st.download_button(
                "Download result CSV",
                result.data.to_csv(index=False).encode("utf-8"),
                "ai_query_result.csv",
                "text/csv",
                use_container_width=True,
            )
    with chart_tab:
        if result.data.empty:
            render_empty("A visualization needs at least one result row.")
            return
        auto = select_chart(result.data)
        choice = st.selectbox("Chart presentation", ["Auto-selected", "Bar", "Line", "Scatter", "Table only"], index=0)
        spec = _override_spec(result.data, auto, choice)
        st.caption(f"Selected: {spec.chart_type} · {spec.rationale or generated.reason}")
        figure = result_chart(result.data, spec)
        if figure is None:
            st.dataframe(result.data, use_container_width=True, hide_index=True)
            return
        st.plotly_chart(figure, use_container_width=True)
        st.caption(narrative.chart_caption)
        if st.button("Prepare PNG and SVG downloads", use_container_width=True, key="prepare_ai_chart_exports"):
            try:
                with st.spinner("Rendering publication-quality chart files…"):
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
            first.download_button("Download chart PNG", png, "ai_query_chart.png", "image/png", use_container_width=True)
            second.download_button("Download chart SVG", svg, "ai_query_chart.svg", "image/svg+xml", use_container_width=True)


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
    render_section_intro(
        "Ask · act · validate",
        "AI Assistant",
        "Select an analytical capability or write a natural-language task. The agent plans, validates, executes, and explains every response against the active dataset.",
    )

    profiles = _model_profiles(pipeline)
    model_control, mode_control, reset_control = st.columns([2.1, 1.2, 1])
    selected_profile = model_control.selectbox(
        "AI model",
        profiles,
        index=len(profiles) - 1,
        key="ai_model_profile",
        help="Choose the guaranteed-private planner or the configured model endpoint.",
    )
    analysis_mode = mode_control.selectbox(
        "Response mode",
        ["Fast", "Balanced", "Deep"],
        index=1,
        key="ai_analysis_mode",
        help="Fast minimizes latency. Balanced adds a concise narrative. Deep uses more model effort.",
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
        ):
            st.session_state.pop(key, None)
        st.rerun()

    active_pipeline = _active_pipeline(pipeline, selected_profile)
    _render_mode_card(active_pipeline, frame, filters, analysis_mode)
    memory = ConversationMemory(st.session_state.get("conversation", []))
    pending = st.session_state.pop("pending_ai_question", None)

    capability_panel, response_panel = st.columns([0.36, 0.64], gap="large")
    requested_question: str | None = pending

    with capability_panel:
        with st.container(border=True):
            st.markdown("### 🤖 AI Capabilities")
            st.caption("Run a common e-commerce investigation with one click.")
            for label, help_text, question in CAPABILITIES:
                if st.button(label, help=help_text, use_container_width=True, key=f"capability_{label}"):
                    requested_question = question
            st.divider()
            st.markdown("#### 💬 Natural Language Task")
            st.caption("Current global filters are applied automatically and override conversation history.")
            draft = st.text_area(
                "Ask the AI agent",
                key="ai_query_draft",
                height=165,
                placeholder="Example: Compare sales and profit by region, then rank the results from highest to lowest.",
                label_visibility="collapsed",
            )
            if st.button("▶ Run Verified Task", type="primary", use_container_width=True, key="run_ai_query"):
                requested_question = draft
            st.divider()
            with st.expander("💾 Saved Responses", expanded=False):
                _render_saved_responses()
            with st.expander(f"🕘 Conversation · {len(memory.as_list())}/5", expanded=False):
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
                    '<div class="ai-response-empty" role="status"><span>✦</span><h3>Ready for a verified task</h3><p>Choose a capability on the left or enter a natural-language request. The agent will show the plan, validation status, execution evidence, and result—never hidden reasoning.</p></div>',
                    unsafe_allow_html=True,
                )
        if last:
            _render_followups(last)
