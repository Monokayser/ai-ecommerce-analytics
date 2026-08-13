"""Thin Streamlit entry point for the e-commerce analytics platform."""

from __future__ import annotations

import streamlit as st

from config.settings import Settings
from config.version import APP_RELEASE
from src.data.cleaner import clean_dataset
from src.data.loader import load_dataset
from src.data.profiler import profile_quality
from src.data.schema import inspect_schema, load_aliases
from src.llm.client import create_llm_client
from src.llm.nl_query import NLQueryPipeline
from src.llm.prompts import PromptRepository
from src.ui import advanced_analytics, ai_assistant, exploration, overview, quality_performance, report_export
from src.ui.brand import BRAND_ICON_PATH
from src.ui.sidebar import apply_filters, build_filter_profile, render_filters
from src.ui.theme import inject_theme, render_agent_launcher, render_app_header, render_build_marker, render_filter_pills, render_sidebar_brand, render_top_navigation
from src.utils.logging_config import configure_logging


@st.cache_data(show_spinner="Loading and profiling dataset...")
def prepare_dataset(source_bytes: bytes | None, filename: str | None, settings: Settings):
    """Load, clean, and profile the selected source as one cached operation."""
    aliases = load_aliases(settings.aliases_path)
    bundle = load_dataset(
        source_bytes if source_bytes is not None else settings.demo_dataset,
        settings,
        filename=filename,
        is_demo=source_bytes is None,
    )
    cleaned, log, warnings, _ = clean_dataset(bundle.raw, aliases)
    bundle.cleaned = cleaned
    bundle.cleaning_log = log
    bundle.warnings = warnings
    bundle.schema_profile = inspect_schema(cleaned)
    bundle.filter_profile = build_filter_profile(cleaned)
    bundle.quality_profile = profile_quality(cleaned)
    return bundle


def main() -> None:
    """Configure state, dataset, services, navigation, and page rendering."""
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    st.set_page_config(page_title=settings.app_name, page_icon=BRAND_ICON_PATH, layout="wide", initial_sidebar_state="auto")
    inject_theme()
    pages = ["Overview", "Data Exploration", "AI Assistant", "Advanced Analytics", "Data Quality & Performance", "Report Export"]
    if st.query_params.get("home") == "1":
        st.session_state["current_section"] = "Overview"
        st.query_params.clear()
    elif st.query_params.get("assistant") == "1":
        st.session_state["current_section"] = "AI Assistant"
        st.query_params.clear()
    render_sidebar_brand()

    upload = st.sidebar.file_uploader(
        "Upload dataset",
        type=["csv", "json", "parquet"],
        help=f"CSV, JSON, or Parquet · maximum {settings.max_upload_mb} MB",
    )
    try:
        bundle = prepare_dataset(upload.getvalue() if upload else None, upload.name if upload else None, settings)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    for warning in bundle.warnings:
        st.sidebar.warning(warning)
    filters = render_filters(bundle.cleaned, bundle.filter_profile)
    filtered = apply_filters(bundle.cleaned, filters)
    st.sidebar.caption(f"Active scope: {len(filtered):,} of {len(bundle.cleaned):,} rows")
    aliases = load_aliases(settings.aliases_path)
    client = create_llm_client(settings)
    pipeline = NLQueryPipeline(settings, client, PromptRepository(settings.prompts_path), aliases)
    st.sidebar.divider()
    st.sidebar.caption(f"AI MODE\n\n{pipeline.mode_label} · {pipeline.model_label}")

    page = render_top_navigation(pages)
    render_agent_launcher(active=page == "AI Assistant")
    render_app_header(bundle, len(filtered), settings, pipeline, compact=page == "AI Assistant")
    if bundle.metadata.is_demo:
        demo_message = "DEMO DATA · Synthetic development records are active. Upload a real dataset with at least 5,000 rows for the official presentation."
        if page == "AI Assistant":
            st.markdown(f'<div class="demo-strip" role="status">{demo_message}</div>', unsafe_allow_html=True)
        else:
            st.warning(demo_message)
    render_filter_pills(filters)
    st.write("")

    if page == "Overview":
        overview.render(filtered, filters)
    elif page == "Data Exploration":
        exploration.render(filtered, filters)
    elif page == "AI Assistant":
        ai_assistant.render(bundle, filtered, filters, settings, pipeline)
    elif page == "Advanced Analytics":
        advanced_analytics.render(filtered)
    elif page == "Data Quality & Performance":
        quality_performance.render(bundle, filtered, settings)
    else:
        report_export.render(bundle)
    render_build_marker(APP_RELEASE)


if __name__ == "__main__":
    main()
