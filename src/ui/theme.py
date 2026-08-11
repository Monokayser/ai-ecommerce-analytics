"""Application-wide glassmorphism design system and presentation helpers."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from config.settings import Settings
from src.llm.nl_query import NLQueryPipeline
from src.models import DatasetBundle
from src.ui.brand import inline_brand_icon


APP_CSS = r"""
<style>
    :root {
        --canvas: #05070d;
        --canvas-soft: #08111e;
        --panel: rgba(8, 25, 42, .76);
        --panel-strong: rgba(10, 31, 51, .92);
        --panel-soft: rgba(17, 45, 70, .58);
        --text: #f7fbff;
        --muted: #9eb2c8;
        --cyan: #62dcff;
        --cyan-soft: #b5efff;
        --blue: #4b8cff;
        --teal: #2dd4bf;
        --green: #55e6a5;
        --amber: #f7c66b;
        --danger: #ff7285;
        --line: rgba(137, 211, 255, .22);
        --line-bright: rgba(137, 223, 255, .46);
        --glass-shadow: 0 26px 72px rgba(0, 0, 0, .42), inset 0 1px 0 rgba(255, 255, 255, .08);
    }

    html { color-scheme: dark; -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }
    html, body, .stApp, button, input, textarea, select {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, Helvetica, sans-serif !important;
        font-synthesis: none;
    }
    body { margin: 0; }
    ::selection { color: #031019; background: #7de5ff; }
    .stApp {
        min-height: 100vh;
        color: var(--text);
        background:
            radial-gradient(circle at 76% -8%, rgba(33, 147, 255, .22), transparent 24rem),
            radial-gradient(circle at 95% 30%, rgba(45, 212, 191, .12), transparent 30rem),
            radial-gradient(circle at 30% 100%, rgba(43, 86, 164, .15), transparent 36rem),
            linear-gradient(145deg, #04060b 0%, #07101b 48%, #05090f 100%);
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: fixed;
        z-index: 0;
        inset: -15% 0 auto 52%;
        height: 60vh;
        pointer-events: none;
        transform: rotate(13deg);
        background: linear-gradient(95deg, transparent 20%, rgba(82, 191, 255, .06) 44%, rgba(103, 218, 255, .17) 50%, transparent 61%);
        filter: blur(14px);
    }
    [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: transparent; }
    [data-testid="stHeader"] { background: rgba(5, 8, 14, .38); -webkit-backdrop-filter: blur(18px); backdrop-filter: blur(18px); }
    [data-testid="stToolbar"] { color: var(--muted); }
    .block-container { position: relative; z-index: 1; max-width: 1480px; padding-top: 1.35rem; padding-bottom: 5rem; }

    h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown { color: var(--text); }
    h1, h2, h3 { letter-spacing: -.035em; }
    h2 { margin-top: .3rem; }
    small, .stCaption, [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
    a { color: var(--cyan); text-underline-offset: .18em; }
    a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible, [tabindex]:focus-visible {
        outline: 3px solid rgba(98, 220, 255, .72) !important;
        outline-offset: 3px !important;
    }
    hr { border-color: var(--line) !important; }
    .skip-link {
        position: fixed;
        z-index: 999999;
        top: .5rem;
        left: .5rem;
        transform: translateY(-160%);
        padding: .7rem 1rem;
        border-radius: 12px;
        color: #031019;
        background: #89e7ff;
        font-weight: 800;
        transition: transform .16s ease;
    }
    .skip-link:focus { transform: translateY(0); }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 15% 4%, rgba(57, 192, 255, .16), transparent 13rem),
            linear-gradient(180deg, rgba(5, 15, 27, .98) 0%, rgba(6, 19, 33, .98) 100%);
        border-right: 1px solid rgba(116, 202, 255, .16);
        box-shadow: 24px 0 70px rgba(0, 0, 0, .22);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.1rem; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p { color: #eaf6ff; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #829ab2 !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(125, 204, 255, .14) !important; }
    [data-testid="stSidebar"] [role="radiogroup"] {
        padding: .45rem;
        border: 1px solid rgba(120, 203, 255, .13);
        border-radius: 18px;
        background: rgba(15, 40, 63, .42);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: .48rem .55rem;
        border-radius: 12px;
        transition: background .18s ease, transform .18s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(87, 191, 255, .10);
        transform: translateX(2px);
    }

    /* Inputs */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div,
    [data-testid="stDateInput"] > div > div,
    [data-testid="stFileUploaderDropzone"] {
        color: var(--text) !important;
        background: rgba(13, 38, 61, .72) !important;
        border-color: rgba(126, 207, 255, .24) !important;
        border-radius: 15px !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .05);
    }
    input, textarea { color: var(--text) !important; caret-color: var(--cyan) !important; }
    input::placeholder, textarea::placeholder { color: #7790a8 !important; }
    [data-baseweb="popover"], [data-baseweb="menu"] { background: #0c2033 !important; color: var(--text) !important; }
    [role="option"] { color: #e9f6ff !important; }
    [role="option"]:hover { background: rgba(73, 171, 229, .16) !important; }
    [data-testid="stSlider"] [role="slider"] { background: var(--cyan) !important; box-shadow: 0 0 18px rgba(98, 220, 255, .55); }
    [data-testid="stFileUploaderDropzone"] { padding: 1rem !important; }

    /* Buttons */
    .stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-secondary"] {
        min-height: 44px;
        border: 1px solid rgba(133, 215, 255, .34) !important;
        border-radius: 999px !important;
        color: #ecfaff !important;
        font-weight: 700 !important;
        background: linear-gradient(120deg, rgba(31, 90, 137, .78), rgba(21, 67, 108, .68)) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .09), 0 9px 24px rgba(0, 0, 0, .18);
        transition: border-color .18s ease, transform .18s ease, box-shadow .18s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stBaseButton-secondary"]:hover {
        color: white !important;
        border-color: rgba(115, 227, 255, .72) !important;
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(25, 143, 217, .24), inset 0 1px 0 rgba(255, 255, 255, .13);
    }
    .stButton > button:focus-visible, .stDownloadButton > button:focus-visible { outline: 3px solid rgba(98, 220, 255, .48) !important; outline-offset: 2px; }

    /* Metrics and data surfaces */
    [data-testid="stMetric"] {
        position: relative;
        overflow: hidden;
        min-height: 122px;
        padding: 1rem 1.05rem;
        border: 1px solid var(--line);
        border-radius: 22px;
        background: linear-gradient(145deg, rgba(16, 46, 73, .73), rgba(7, 24, 41, .76));
        box-shadow: var(--glass-shadow);
    }
    [data-testid="stMetric"]::after {
        content: "";
        position: absolute;
        width: 95px;
        height: 95px;
        right: -46px;
        bottom: -60px;
        border-radius: 50%;
        background: rgba(88, 207, 255, .18);
        filter: blur(12px);
    }
    [data-testid="stMetricLabel"] { color: #9fb7cc; font-weight: 650; }
    [data-testid="stMetricValue"] { color: #f8fcff; font-weight: 790; letter-spacing: -.045em; }
    [data-testid="stMetricDelta"] svg { filter: drop-shadow(0 0 5px currentColor); }
    [data-testid="stPlotlyChart"], [data-testid="stDataFrame"], [data-testid="stJson"] {
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: rgba(7, 24, 40, .72);
        box-shadow: var(--glass-shadow);
    }
    [data-testid="stDataFrame"] { padding: .2rem; }

    /* Tabs, expanders, status, alerts */
    [data-testid="stTabs"] [role="tablist"] {
        gap: .35rem;
        padding: .34rem;
        overflow-x: auto;
        border: 1px solid rgba(128, 207, 255, .16);
        border-radius: 999px;
        background: rgba(8, 29, 47, .72);
    }
    [data-testid="stTabs"] button[role="tab"] {
        min-height: 2.45rem;
        padding: .35rem .8rem;
        border-radius: 999px;
        color: #90a8be;
        font-weight: 700;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: white;
        background: linear-gradient(120deg, rgba(44, 127, 189, .72), rgba(31, 95, 146, .72));
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .12), 0 7px 18px rgba(0, 0, 0, .2);
    }
    [data-testid="stExpander"], [data-testid="stStatusWidget"], [data-testid="stAlert"] {
        overflow: hidden;
        border: 1px solid var(--line) !important;
        border-radius: 18px !important;
        background: rgba(9, 30, 49, .72) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .05);
    }
    [data-testid="stAlert"] p { color: #dff5ff !important; }
    [data-testid="stChatMessage"] {
        border: 1px solid rgba(132, 208, 255, .17);
        border-radius: 20px;
        background: rgba(12, 36, 57, .58);
        padding: .55rem .75rem;
        margin: .45rem 0;
    }
    [data-testid="stChatInput"] {
        border: 1px solid rgba(127, 219, 255, .42) !important;
        border-radius: 22px !important;
        background: rgba(8, 29, 48, .88) !important;
        box-shadow: 0 18px 55px rgba(0, 0, 0, .32), 0 0 28px rgba(47, 164, 225, .11);
    }

    /* Hero inspired by the supplied luminous discount card */
    .app-hero {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        margin-bottom: 1rem;
        padding: clamp(1.45rem, 3vw, 2.35rem);
        border: 1px solid rgba(147, 221, 255, .32);
        border-radius: 30px;
        color: white;
        background:
            radial-gradient(circle at 88% 112%, rgba(112, 222, 255, .38), transparent 28%),
            radial-gradient(circle at 75% 4%, rgba(38, 133, 220, .23), transparent 33%),
            linear-gradient(135deg, rgba(7, 21, 37, .96), rgba(9, 41, 68, .91));
        box-shadow: 0 28px 80px rgba(0, 0, 0, .46), 0 0 50px rgba(42, 170, 235, .12), inset 0 1px 0 rgba(255, 255, 255, .1);
        -webkit-backdrop-filter: blur(24px) saturate(130%);
        backdrop-filter: blur(24px) saturate(130%);
    }
    .app-hero::before {
        content: "";
        position: absolute;
        z-index: -1;
        width: 310px;
        height: 620px;
        right: 3%;
        top: -310px;
        transform: rotate(22deg);
        background: linear-gradient(90deg, transparent, rgba(89, 204, 255, .26), transparent);
        filter: blur(12px);
    }
    .app-hero::after {
        content: "·  ·       ·    ·      ·";
        position: absolute;
        right: 5%;
        top: 21%;
        color: rgba(194, 239, 255, .52);
        font-size: 1.1rem;
        letter-spacing: .75rem;
    }
    .app-eyebrow, .section-kicker {
        margin-bottom: .5rem;
        color: #7fe7ff;
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: .17em;
        text-transform: uppercase;
    }
    .app-title { margin: 0; max-width: 980px; color: white; font-size: clamp(2rem, 4vw, 3.5rem); font-weight: 820; letter-spacing: -.055em; line-height: 1.02; }
    .app-subtitle { max-width: 800px; margin: .8rem 0 1.25rem; color: #bfd1e1; font-size: .98rem; line-height: 1.65; }
    .hero-pills, .filter-pills, .trust-row { display: flex; flex-wrap: wrap; gap: .5rem; }
    .hero-pill, .trust-pill {
        display: inline-flex;
        align-items: center;
        gap: .4rem;
        padding: .4rem .75rem;
        border: 1px solid rgba(174, 228, 255, .18);
        border-radius: 999px;
        background: rgba(177, 224, 255, .08);
        color: #eaf9ff;
        font-size: .76rem;
        font-weight: 700;
        -webkit-backdrop-filter: blur(12px);
        backdrop-filter: blur(12px);
    }
    .status-dot { width: .48rem; height: .48rem; border-radius: 50%; background: var(--green); box-shadow: 0 0 0 4px rgba(85, 230, 165, .11), 0 0 13px rgba(85, 230, 165, .7); }

    /* Custom components */
    .sidebar-brand { padding: .25rem .08rem 1rem; }
    .sidebar-mark {
        width: 46px;
        height: 46px;
        display: grid;
        place-items: center;
        margin-bottom: .7rem;
        border: 0;
        border-radius: 16px;
        background: transparent;
        color: white;
        font-weight: 850;
        box-shadow: 0 10px 30px rgba(34, 164, 222, .22);
    }
    .sidebar-mark svg { width: 100%; height: 100%; display: block; }
    .sidebar-title { color: white; font-size: 1.08rem; font-weight: 780; line-height: 1.2; }
    .sidebar-subtitle { margin-top: .3rem; color: #88a2b9; font-size: .78rem; }
    .sidebar-live { display:flex; align-items:center; gap:.5rem; margin:.8rem 0 .2rem; color:#a8bfd2; font-size:.72rem; }

    .section-shell {
        margin: .2rem 0 1.1rem;
        padding: 1.15rem 1.25rem;
        border: 1px solid rgba(133, 211, 255, .16);
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(13, 39, 62, .65), rgba(8, 26, 43, .55));
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .05);
    }
    .section-title { margin: 0; color: #f6fbff; font-size: clamp(1.55rem, 2.5vw, 2.15rem); font-weight: 790; line-height: 1.08; }
    .section-description { margin: .5rem 0 0; max-width: 850px; color: #9eb3c7; font-size: .9rem; line-height: 1.55; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(133, 211, 255, .16) !important;
        border-radius: 22px !important;
        background: linear-gradient(135deg, rgba(13, 39, 62, .65), rgba(8, 26, 43, .55));
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .05);
    }
    .filter-pill {
        display: inline-flex;
        padding: .35rem .68rem;
        border: 1px solid rgba(98, 220, 255, .24);
        border-radius: 999px;
        background: rgba(40, 127, 180, .13);
        color: #bdefff;
        font-size: .75rem;
        font-weight: 700;
    }
    .scope-note { display:flex; align-items:center; gap:.5rem; color:#8098ae; font-size:.8rem; }
    .mode-card {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: .9rem;
        align-items: center;
        margin: .4rem 0 1.15rem;
        padding: 1rem 1.1rem;
        border: 1px solid rgba(113, 218, 255, .27);
        border-radius: 22px;
        background: radial-gradient(circle at 96% 110%, rgba(89, 213, 255, .25), transparent 23%), linear-gradient(135deg, rgba(9, 32, 53, .92), rgba(10, 45, 72, .72));
        box-shadow: var(--glass-shadow);
    }
    .mode-orb { position:relative; width:46px; height:46px; display:grid; place-items:center; border-radius:16px; background:transparent; color:#02111c; font-size:1.25rem; box-shadow:0 0 30px rgba(77,202,255,.28); transform-style:preserve-3d; }
    .mode-orb svg { width: 100%; height: 100%; display: block; }
    .mode-orb::after { content:""; position:absolute; inset:5px; border:1px solid rgba(255,255,255,.22); border-radius:12px; transform:translateZ(8px); pointer-events:none; }
    .mode-card strong { color: #f5fbff; font-size: .95rem; }
    .mode-card span { color: #9eb4c7; font-size: .82rem; line-height: 1.45; }
    .mode-meta { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:.55rem; }
    .mode-meta b { padding:.28rem .55rem; border:1px solid rgba(136,215,255,.17); border-radius:999px; color:#bfeeff; background:rgba(80,173,222,.09); font-size:.7rem; font-weight:700; }
    .answer-card {
        position: relative;
        overflow: hidden;
        margin: .65rem 0 1rem;
        padding: 1.25rem 1.35rem;
        border: 1px solid rgba(125, 220, 255, .32);
        border-radius: 24px;
        background: radial-gradient(circle at 96% 120%, rgba(93, 219, 255, .25), transparent 25%), linear-gradient(145deg, rgba(10, 35, 57, .93), rgba(9, 26, 43, .9));
        box-shadow: var(--glass-shadow), 0 0 38px rgba(40, 162, 224, .08);
    }
    .answer-card h3 { margin: .15rem 0 .45rem; color: #f7fcff; font-size: 1.3rem; line-height: 1.25; }
    .answer-card p { margin: 0 0 .85rem; max-width: 950px; color: #b6cadb; line-height: 1.58; }
    .answer-eyebrow { color:#6fe1ff; font-size:.69rem; font-weight:800; letter-spacing:.15em; text-transform:uppercase; }
    .trust-pill { padding:.3rem .58rem; color:#b6d7e8; font-size:.69rem; }
    .trust-pill.safe { color:#a7f5d2; border-color:rgba(85,230,165,.24); background:rgba(32,171,117,.09); }
    .empty-state {
        padding: 1.4rem;
        text-align: center;
        border: 1px dashed rgba(129, 211, 255, .28);
        border-radius: 22px;
        background: rgba(10, 32, 51, .55);
        color: #9fb7ca;
    }
    .empty-icon { display:block; margin-bottom:.4rem; color:#6edfff; font-size:1.45rem; }

    @keyframes softFloat { 0%,100% { transform:translate3d(0,0,0) rotateX(0); } 50% { transform:translate3d(0,-3px,8px) rotateX(4deg); } }
    .mode-orb, .sidebar-mark { animation: softFloat 4s ease-in-out infinite; }
    @media (hover: hover) and (pointer: fine) {
        [data-testid="stMetric"], .mode-card, .answer-card, [data-testid="stPlotlyChart"] {
            transform: perspective(900px) translateZ(0);
            transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
        }
        [data-testid="stMetric"]:hover, .mode-card:hover, .answer-card:hover {
            transform: perspective(900px) translateY(-3px) translateZ(6px) rotateX(1deg);
            border-color: rgba(137, 223, 255, .42);
            box-shadow: 0 30px 80px rgba(0,0,0,.46), 0 0 34px rgba(42,170,235,.09), inset 0 1px 0 rgba(255,255,255,.1);
        }
    }
    @supports not ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {
        [data-testid="stHeader"], .app-hero, .hero-pill { background-color: #0a2034; }
        .mode-card, .answer-card, [data-testid="stMetric"] { background-color: #0b2237; }
    }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; scroll-behavior:auto !important; } }
    @media (forced-colors: active) {
        .app-hero, .mode-card, .answer-card, [data-testid="stMetric"], [data-testid="stPlotlyChart"] { border: 1px solid CanvasText; }
        .status-dot { background: Highlight; box-shadow: none; }
    }
    @media (max-width: 1200px) {
        .block-container { max-width: 100%; padding-left: 1rem; padding-right: 1rem; }
        .app-title { font-size: clamp(1.9rem, 4.4vw, 3rem); }
    }
    @media (max-width: 900px) {
        .block-container { padding: .85rem .75rem 3rem; }
        .app-hero { padding: 1.3rem; border-radius: 23px; }
        .app-hero::after { display: none; }
        [data-testid="stMetric"] { min-height: 105px; border-radius: 18px; }
        .section-shell { padding: 1rem; }
        [data-testid="stTabs"] [role="tablist"] { border-radius: 16px; }
        [data-testid="stTabs"] button[role="tab"] { min-width: max-content; }
    }
    @media (max-width: 640px) {
        .block-container { padding-left: .55rem; padding-right: .55rem; }
        .app-hero { padding: 1.15rem; border-radius: 20px; }
        .app-title { font-size: clamp(1.85rem, 10vw, 2.55rem); line-height: 1.05; overflow-wrap: anywhere; }
        .app-subtitle { font-size: .9rem; }
        .hero-pill { font-size: .7rem; padding: .36rem .6rem; }
        .mode-card { grid-template-columns: 1fr; }
        .mode-orb { width: 42px; height: 42px; }
        .answer-card { padding: 1rem; border-radius: 20px; }
        [data-testid="stDataFrame"], [data-testid="stPlotlyChart"] { border-radius: 18px; }
        .stButton > button, .stDownloadButton > button { width: 100%; min-height: 46px; }
    }
</style>
"""


def inject_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)
    st.markdown('<a class="skip-link" href="#main-content">Skip to main content</a>', unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    st.sidebar.markdown(
        f"""<div class="sidebar-brand"><div class="sidebar-mark">{inline_brand_icon('sidebar-brand-icon')}</div><div class="sidebar-title">E-Commerce Analytics</div><div class="sidebar-subtitle">Secure intelligence workspace</div><div class="sidebar-live"><span class="status-dot"></span> Analytics engine online</div></div>""",
        unsafe_allow_html=True,
    )


def render_app_header(bundle: DatasetBundle, active_rows: int, settings: Settings, pipeline: NLQueryPipeline) -> None:
    source = "Demo dataset" if bundle.metadata.is_demo else "Uploaded dataset"
    readiness = "Presentation ready" if bundle.metadata.official_demo_ready else "Development mode"
    st.markdown(
        f"""<section id="main-content" tabindex="-1" class="app-hero" aria-label="Application summary"><div class="app-eyebrow">AI decision intelligence</div><h1 class="app-title">{escape(settings.app_name)}</h1><p class="app-subtitle">Turn raw transactions into interactive evidence. Explore the business, ask questions in natural language, validate every query, and export decision-ready findings.</p><div class="hero-pills"><span class="hero-pill"><span class="status-dot"></span>{escape(pipeline.mode_label)} · {escape(pipeline.model_label)}</span><span class="hero-pill">{source}</span><span class="hero-pill">{active_rows:,} active rows</span><span class="hero-pill">{bundle.metadata.columns} source columns</span><span class="hero-pill">{readiness}</span></div></section>""",
        unsafe_allow_html=True,
    )


def render_filter_pills(filters: dict[str, Any]) -> None:
    if not filters:
        st.markdown('<div class="scope-note" aria-live="polite"><span class="status-dot"></span>All records are in scope · refine the view with global filters</div>', unsafe_allow_html=True)
        return
    chips = []
    for key, value in filters.items():
        display = ", ".join(map(str, value)) if isinstance(value, list) else " → ".join(map(str, value)) if isinstance(value, tuple) else str(value)
        chips.append(f'<span class="filter-pill">{escape(key)}: {escape(display)}</span>')
    st.markdown('<div class="filter-pills" aria-label="Active filters" aria-live="polite">' + "".join(chips) + "</div>", unsafe_allow_html=True)


def render_section_intro(kicker: str, title: str, description: str) -> None:
    with st.container(border=True):
        st.markdown(f'<div class="section-kicker">{escape(kicker)}</div>', unsafe_allow_html=True)
        st.header(title)
        st.caption(description)
