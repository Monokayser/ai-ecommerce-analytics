"""Application-wide visual system and accessible presentation helpers."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from config.settings import Settings
from src.llm.nl_query import NLQueryPipeline
from src.models import DatasetBundle


APP_CSS = r"""
<style>
    :root {--ink:#0b1930;--muted:#5f6f85;--navy:#071426;--teal:#0f8f83;--line:#dce6ef;--surface:rgba(255,255,255,.93);}
    .stApp {background:radial-gradient(circle at 90% 0%,rgba(20,184,166,.09),transparent 27rem),linear-gradient(180deg,#f7fafc 0%,#eef4f8 100%);}
    .block-container {max-width:1480px;padding-top:1.4rem;padding-bottom:4rem;}
    h1,h2,h3 {color:var(--ink);letter-spacing:-.025em;} h2{margin-top:.35rem;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,var(--navy) 0%,#0a1d34 100%);border-right:1px solid #173653;}
    [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] label,[data-testid="stSidebar"] p{color:#e8f1f8;}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#9fb2c5;} [data-testid="stSidebar"] hr{border-color:#24415c;}
    [data-testid="stSidebar"] .stButton button{border-color:#36526c;color:#e8f1f8;background:#102b47;}
    [data-testid="stSidebar"] .stButton button:hover{border-color:#2dd4bf;color:white;}
    [data-testid="stMetric"]{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:1rem 1.05rem;box-shadow:0 8px 26px rgba(11,25,48,.055);min-height:118px;}
    [data-testid="stMetricLabel"]{color:var(--muted);font-weight:650;} [data-testid="stMetricValue"]{color:var(--ink);font-weight:760;letter-spacing:-.035em;}
    [data-testid="stPlotlyChart"],[data-testid="stDataFrame"]{background:white;border:1px solid var(--line);border-radius:16px;box-shadow:0 8px 28px rgba(11,25,48,.045);overflow:hidden;}
    [data-testid="stTabs"] button{font-weight:650;} .stButton button,.stDownloadButton button{border-radius:10px;font-weight:650;min-height:2.7rem;}
    .stChatInputContainer textarea{border-radius:14px;}
    .app-hero{position:relative;overflow:hidden;margin-bottom:1rem;padding:1.5rem 1.7rem;border-radius:22px;color:white;background:linear-gradient(118deg,#071426 0%,#0b2a45 58%,#0f766e 130%);box-shadow:0 18px 50px rgba(7,20,38,.16);}
    .app-hero:after{content:"";position:absolute;width:260px;height:260px;border-radius:50%;right:-90px;top:-145px;background:rgba(45,212,191,.18);}
    .app-eyebrow{font-size:.75rem;font-weight:750;text-transform:uppercase;letter-spacing:.13em;color:#76e4d4;margin-bottom:.45rem;}
    .app-title{font-size:clamp(1.65rem,3vw,2.45rem);line-height:1.05;font-weight:790;letter-spacing:-.045em;margin:0;color:white;}
    .app-subtitle{color:#c6d5e3;margin:.65rem 0 1rem;max-width:850px;font-size:.96rem;}
    .hero-pills,.filter-pills{display:flex;flex-wrap:wrap;gap:.45rem;}.hero-pill{display:inline-flex;align-items:center;gap:.35rem;padding:.34rem .65rem;border:1px solid rgba(255,255,255,.16);border-radius:999px;background:rgba(255,255,255,.08);color:#eaf5f7;font-size:.76rem;font-weight:650;}
    .filter-pill{display:inline-flex;padding:.28rem .58rem;border-radius:999px;background:#e6f6f3;color:#0b5f58;border:1px solid #c6ebe4;font-size:.76rem;font-weight:650;}.status-dot{width:.46rem;height:.46rem;border-radius:50%;background:#34d399;box-shadow:0 0 0 4px rgba(52,211,153,.12);}
    .sidebar-brand{padding:.35rem .1rem .9rem;}.sidebar-mark{width:38px;height:38px;display:grid;place-items:center;border-radius:11px;background:linear-gradient(135deg,#14b8a6,#0e7490);color:white;font-weight:850;margin-bottom:.65rem;}
    .sidebar-title{color:white;font-size:1.05rem;font-weight:760;line-height:1.2;}.sidebar-subtitle{color:#93a9bd;font-size:.78rem;margin-top:.25rem;}
    .section-kicker{color:#0f766e;font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;font-weight:780;margin-bottom:-.25rem;}
    .mode-card{border:1px solid #cfe6e2;background:linear-gradient(135deg,#f8fffd,#ecf8f6);border-radius:15px;padding:.85rem 1rem;margin:.35rem 0 1rem;}.mode-card strong{color:#0b463f;}.mode-card span{color:#61716f;font-size:.82rem;}
    .answer-card{background:white;border:1px solid var(--line);border-left:4px solid var(--teal);border-radius:14px;padding:1rem 1.1rem;margin:.5rem 0 1rem;}.answer-card h3{margin:.05rem 0 .35rem;font-size:1.08rem;}.answer-card p{margin:0;color:#45556a;}
    @media(max-width:800px){.block-container{padding:1rem .85rem 3rem}.app-hero{padding:1.2rem;border-radius:17px}[data-testid="stMetric"]{min-height:100px}}
</style>
"""


def inject_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    st.sidebar.markdown(
        """<div class="sidebar-brand"><div class="sidebar-mark">EA</div><div class="sidebar-title">E-Commerce Analytics</div><div class="sidebar-subtitle">Secure intelligence workspace</div></div>""",
        unsafe_allow_html=True,
    )


def render_app_header(bundle: DatasetBundle, active_rows: int, settings: Settings, pipeline: NLQueryPipeline) -> None:
    source = "Demo dataset" if bundle.metadata.is_demo else "Uploaded dataset"
    readiness = "Presentation ready" if bundle.metadata.official_demo_ready else "Development mode"
    st.markdown(
        f"""<section class="app-hero" aria-label="Application summary"><div class="app-eyebrow">Decision intelligence workspace</div><h1 class="app-title">{escape(settings.app_name)}</h1><p class="app-subtitle">Explore transactions, ask business questions in plain language, validate every query, and export decision-ready evidence.</p><div class="hero-pills"><span class="hero-pill"><span class="status-dot"></span>{escape(pipeline.mode_label)} · {escape(pipeline.model_label)}</span><span class="hero-pill">{source}</span><span class="hero-pill">{active_rows:,} active rows</span><span class="hero-pill">{bundle.metadata.columns} source columns</span><span class="hero-pill">{readiness}</span></div></section>""",
        unsafe_allow_html=True,
    )


def render_filter_pills(filters: dict[str, Any]) -> None:
    if not filters:
        st.caption("All records are in scope · apply global filters from the sidebar")
        return
    chips = []
    for key, value in filters.items():
        display = ", ".join(map(str, value)) if isinstance(value, list) else " → ".join(map(str, value)) if isinstance(value, tuple) else str(value)
        chips.append(f'<span class="filter-pill">{escape(key)}: {escape(display)}</span>')
    st.markdown('<div class="filter-pills">' + "".join(chips) + "</div>", unsafe_allow_html=True)


def render_section_intro(kicker: str, title: str, description: str) -> None:
    st.markdown(f'<div class="section-kicker">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.header(title)
    st.caption(description)
