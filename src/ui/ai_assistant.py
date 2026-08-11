"""Conversational natural-language analytics workspace with verified evidence."""

from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from config.settings import Settings
from src.data.query_engine import QueryEngine
from src.llm.conversation import ConversationMemory, Interaction
from src.llm.nl_query import NLQueryPipeline
from src.models import ChartSpec, DatasetBundle
from src.ui.brand import inline_brand_icon
from src.ui.components import render_empty
from src.ui.theme import render_section_intro
from src.visualization.chart_selector import select_chart
from src.visualization.charts import result_chart
from src.visualization.export import export_chart


SAMPLES = [
    ("◎ Regional leader", "Rank markets by revenue", "Which region has the highest total sales?"),
    ("↗ Profit ranking", "Find the strongest products", "What are the five most profitable sub-categories?"),
    ("⌁ Monthly trend", "Reveal momentum over time", "Show monthly sales and profit trends."),
    ("◇ Discount impact", "Test a profit relationship", "Is discount negatively associated with profit?"),
    ("△ Loss markets", "Surface commercial risk", "Which countries generated losses?"),
    ("✦ Unusual orders", "Investigate suspicious rows", "Find unusual orders with high discounts and negative profit."),
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


def _render_mode_card(
    settings: Settings,
    pipeline: NLQueryPipeline,
    frame: pd.DataFrame,
    filters: dict[str, Any],
    analysis_mode: str,
) -> None:
    if settings.ai_available:
        description = "Structured model planning, AST validation, read-only execution, one safe correction attempt, and evidence-grounded narration."
    else:
        description = "No API key is required. Common business questions use a deterministic local planner; connect Gemini, OpenAI, or Ollama for broader language understanding."
    provider_state = "Hosted AI connected" if settings.ai_available else "Private local fallback"
    st.markdown(
        f"""<div class="mode-card"><div class="mode-orb">{inline_brand_icon('ai-mode-icon')}</div><div><strong>{escape(pipeline.mode_label)} · {escape(pipeline.model_label)}</strong><br><span>{escape(description)}</span><div class="mode-meta"><b>{escape(analysis_mode)} response</b><b>{escape(provider_state)}</b><b>{len(frame):,} active rows</b><b>{len(filters)} active filters</b><b>Read-only execution</b></div></div></div>""",
        unsafe_allow_html=True,
    )


def _render_history(memory: ConversationMemory) -> None:
    records = memory.as_list()
    if not records:
        return
    with st.expander(f"Conversation memory · {len(records)} interaction(s)"):
        for item in records:
            with st.chat_message("user"):
                st.write(item["question"])
            with st.chat_message("assistant"):
                st.write(item["answer"])
                st.caption(item["result_summary"])


def _render_last_result(last: dict[str, Any], pipeline: NLQueryPipeline) -> None:
    generated, result, narrative = last["generated"], last["result"], last["narrative"]
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
            st.warning("The hosted model was unavailable, so this answer used the safe local fallback. " + str(metrics.get("fallback_reason", "")))
        st.success("Read-only query validated · dataset table only · result limit applied")
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


def _render_followups(last: dict[str, Any]) -> None:
    """Offer concrete next questions that work in hosted and local modes."""
    st.markdown("#### Continue the investigation")
    st.caption("Choose a verified follow-up or write your own question below.")
    followups = [
        ("↻ Retry this question", str(last.get("question", ""))),
        ("⌁ Track momentum", "Show monthly sales and profit trends."),
        ("↗ Find profit drivers", "Which product category has the highest profit?"),
        ("△ Scan downside", "Which countries generated losses?"),
    ]
    columns = st.columns(4)
    for column, (label, question) in zip(columns, followups, strict=False):
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
    """Render prompt shortcuts, a secure query workflow, evidence, and memory."""
    render_section_intro(
        "Ask · validate · explain",
        "AI Assistant",
        "Collaborate with a secure analytics copilot that plans, validates, executes, and explains every answer against the active dataset.",
    )
    mode_control, mode_help = st.columns([1, 3])
    analysis_mode = mode_control.selectbox(
        "AI response mode",
        ["Fast", "Balanced", "Deep"],
        index=1,
        key="ai_analysis_mode",
        help="Fast uses one hosted-model pass and a computed summary. Balanced adds an AI narrative. Deep uses higher reasoning and detail.",
    )
    mode_help.caption(
        "Fast minimizes latency and free-tier usage · Balanced is the default · Deep spends more model effort on complex investigations."
    )
    _render_mode_card(settings, pipeline, frame, filters, analysis_mode)
    memory = ConversationMemory(st.session_state.get("conversation", []))
    top_left, top_right = st.columns([4, 1])
    top_left.markdown("#### Start with a smart prompt")
    if top_right.button("Clear conversation", use_container_width=True):
        memory.clear()
        st.session_state["conversation"] = []
        st.session_state.pop("last_ai", None)
        st.session_state.pop("last_chart_png", None)
        st.session_state.pop("ai_chart_png", None)
        st.session_state.pop("ai_chart_svg", None)
        st.rerun()

    preset_question = None
    for start in range(0, len(SAMPLES), 3):
        columns = st.columns(3)
        for column, (label, description, question) in zip(columns, SAMPLES[start : start + 3], strict=False):
            if column.button(label, help=f"{description} · {question}", use_container_width=True, key=f"sample_{label}"):
                preset_question = question
    _render_history(memory)
    pending_question = st.session_state.pop("pending_ai_question", None)
    st.caption("Current filters take priority over conversation history. Every generated query is validated before execution.")
    question = pending_question or preset_question or st.chat_input("Ask a business question about sales, profit, customers, products, markets, trends, or risk…")

    if question:
        st.session_state.pop("ai_chart_png", None)
        st.session_state.pop("ai_chart_svg", None)
        st.session_state.pop("last_chart_png", None)
        engine = QueryEngine(frame, max_rows=settings.max_result_rows, timeout_seconds=settings.query_timeout_seconds)
        with st.status(f"AI analyst is working in {analysis_mode.lower()} mode…", expanded=True) as status:
            stage_icons = {"planning": "◌", "validation": "✓", "execution": "✓", "narrative": "✦"}

            def report_progress(stage: str, message: str) -> None:
                if stage != "complete":
                    st.write(f"{stage_icons.get(stage, '·')} {message}")

            try:
                generated, result, narrative, corrected = pipeline.run(
                    question,
                    engine,
                    bundle.schema_profile,
                    filters=filters,
                    history=memory.prompt_context(),
                    analysis_mode=analysis_mode,
                    progress=report_progress,
                )
                status.update(label="Verified answer ready", state="complete", expanded=False)
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
        st.toast(f"{pipeline.mode_label} analysis completed", icon="✅")

    last = st.session_state.get("last_ai")
    if last:
        _render_last_result(last, pipeline)
        _render_followups(last)
