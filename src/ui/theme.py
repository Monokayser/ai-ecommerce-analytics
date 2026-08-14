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
        --font-sans: "Segoe UI Variable Text", "Segoe UI", system-ui, Roboto, "Helvetica Neue", Arial, sans-serif;
        --font-display: "Segoe UI Variable Display", "Segoe UI", system-ui, Roboto, "Helvetica Neue", Arial, sans-serif;
        --canvas: #020806;
        --canvas-soft: #06120e;
        --panel: rgba(5, 20, 16, .82);
        --panel-strong: rgba(6, 27, 21, .95);
        --panel-soft: rgba(11, 43, 34, .62);
        --text: #f7fbff;
        --muted: #9eb2c8;
        --cyan: #7fffe1;
        --cyan-soft: #c8fff2;
        --blue: #54c9b2;
        --teal: #39e6bd;
        --green: #79f2bd;
        --amber: #f7c66b;
        --danger: #ff7285;
        --line: rgba(132, 255, 213, .18);
        --line-bright: rgba(139, 255, 221, .42);
        --glass-shadow: 0 26px 72px rgba(0, 0, 0, .42), inset 0 1px 0 rgba(255, 255, 255, .08);
    }

    html {
        color-scheme: dark;
        -webkit-text-size-adjust: 100%;
        text-size-adjust: 100%;
        scroll-behavior: auto;
        scrollbar-gutter: stable;
    }
    html, body, .stApp, button, input, textarea, select {
        font-family: var(--font-sans) !important;
        font-synthesis: none;
        font-optical-sizing: auto;
        font-kerning: normal;
        text-rendering: optimizeLegibility;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    .stApp p,
    .stApp li,
    .stApp label,
    .stApp small,
    .stApp strong,
    .stApp table,
    .stApp [role="tab"],
    .stApp [role="option"] {
        font-family: var(--font-sans) !important;
    }
    body { margin: 0; overflow-x: hidden; }
    ::selection { color: #031019; background: #7de5ff; }
    .stApp {
        min-height: 100vh;
        color: var(--text);
        background:
            radial-gradient(ellipse at 70% -8%, rgba(37, 229, 174, .23), transparent 28rem),
            radial-gradient(ellipse at 98% 32%, rgba(22, 141, 111, .13), transparent 34rem),
            radial-gradient(ellipse at 22% 102%, rgba(40, 123, 91, .16), transparent 38rem),
            linear-gradient(145deg, #010503 0%, #03100c 48%, #020806 100%);
        background-attachment: scroll;
    }
    .stApp::before {
        content: "";
        position: absolute;
        z-index: 0;
        inset: -18% -10% auto 32%;
        height: 72vh;
        pointer-events: none;
        transform: rotate(8deg) skewX(-9deg);
        background:
            linear-gradient(102deg, transparent 20%, rgba(75, 255, 193, .03) 38%, rgba(84, 255, 202, .21) 48%, rgba(96, 246, 203, .05) 58%, transparent 69%);
        opacity: .78;
        filter: blur(12px);
        transform: rotate(8deg) skewX(-9deg) translateZ(0);
    }
    .stApp::after {
        content: "";
        position: absolute;
        z-index: 0;
        left: 0;
        right: 0;
        bottom: -2px;
        height: 15vh;
        min-height: 95px;
        pointer-events: none;
        opacity: .28;
        background:
            linear-gradient(180deg, transparent 0 28%, rgba(11, 31, 23, .72) 29% 100%),
            repeating-linear-gradient(115deg, rgba(108, 255, 204, .11) 0 1px, transparent 1px 9px);
        clip-path: polygon(0 74%, 8% 47%, 15% 65%, 25% 35%, 36% 70%, 45% 48%, 53% 64%, 64% 30%, 75% 67%, 86% 38%, 94% 61%, 100% 42%, 100% 100%, 0 100%);
        filter: drop-shadow(0 -12px 30px rgba(52, 255, 184, .09));
    }
    [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: transparent; }
    [data-testid="stHeader"] {
        background: rgba(3, 13, 10, .94);
        -webkit-backdrop-filter: none;
        backdrop-filter: none;
    }
    [data-testid="stToolbar"] { color: var(--muted); }
    .block-container { position: relative; z-index: 1; max-width: 1480px; padding-top: 1.35rem; padding-bottom: 5rem; }

    h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown { color: var(--text); }
    h1, h2, h3, .app-title, .section-title, .kpi-value {
        font-family: var(--font-display) !important;
        font-variation-settings: "wght" 700;
    }
    h1, h2, h3 { letter-spacing: -.025em; line-height: 1.15; }
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
            radial-gradient(circle at 15% 4%, rgba(53, 236, 180, .15), transparent 13rem),
            linear-gradient(180deg, rgba(2, 12, 9, .985) 0%, rgba(4, 22, 17, .985) 100%);
        border-right: 1px solid rgba(121, 242, 189, .15);
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
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border-color: rgba(127, 255, 213, .25) !important;
        background:
            radial-gradient(circle at 105% 0%, rgba(57,230,189,.12), transparent 10rem),
            linear-gradient(145deg, rgba(5,34,25,.96), rgba(3,23,17,.98)) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 15px 38px rgba(0,0,0,.2);
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        background: rgba(57,230,189,.055);
    }

    /* Inputs */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div,
    [data-testid="stDateInput"] > div > div,
    [data-testid="stFileUploaderDropzone"] {
        color: var(--text) !important;
        background: rgba(6, 33, 25, .78) !important;
        border-color: rgba(126, 255, 211, .22) !important;
        border-radius: 15px !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .05);
    }
    input, textarea { color: var(--text) !important; caret-color: var(--cyan) !important; }
    input::placeholder, textarea::placeholder { color: #aac3ba !important; opacity: 1 !important; }
    [data-baseweb="popover"], [data-baseweb="menu"] { background: #0c2033 !important; color: var(--text) !important; }
    [role="option"] { color: #e9f6ff !important; }
    [role="option"]:hover { background: rgba(73, 171, 229, .16) !important; }
    [data-testid="stSlider"] [role="slider"] { background: var(--cyan) !important; box-shadow: 0 0 18px rgba(98, 220, 255, .55); }
    [data-testid="stFileUploaderDropzone"] { padding: 1rem !important; }

    /* Streamlit React-Aria multiselects: align every filter state with the emerald theme */
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"][data-rac] {
        min-height: 42px;
        border: 1px solid rgba(127,255,213,.17) !important;
        border-radius: 12px !important;
        color: #eafff8 !important;
        background: linear-gradient(135deg, rgba(2,18,13,.98), rgba(5,31,23,.98)) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.035), 0 8px 20px rgba(0,0,0,.16);
        transition: border-color .2s ease, box-shadow .2s ease, background .2s ease;
    }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"][data-rac][data-focus-within="true"] {
        border-color: rgba(127,255,225,.62) !important;
        background: linear-gradient(135deg, rgba(3,26,19,.99), rgba(7,43,32,.99)) !important;
        box-shadow: 0 0 0 3px rgba(57,230,189,.1), 0 0 24px rgba(57,230,189,.1), inset 0 1px 0 rgba(255,255,255,.06);
    }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] input { color:#eafff8 !important; }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] svg { color:#b9e8d9 !important; }
    [data-testid="stSidebar"] [data-tag] {
        overflow: hidden;
        border: 1px solid rgba(143,255,218,.38) !important;
        border-radius: 8px !important;
        color: #042119 !important;
        background: linear-gradient(120deg, #54e0b5, #8affd8) !important;
        box-shadow: 0 5px 14px rgba(34,190,143,.2), inset 0 1px 0 rgba(255,255,255,.38);
    }
    [data-testid="stSidebar"] [data-tag] > span,
    [data-testid="stSidebar"] [data-tag] button {
        color: #042119 !important;
        background: transparent !important;
        font-weight: 780 !important;
    }
    [data-testid="stSidebar"] [data-tag] button:hover { color:#000e0a !important; background:rgba(0,62,45,.1) !important; }
    [data-testid="stMultiSelectDropdown"] {
        border: 1px solid rgba(127,255,213,.28) !important;
        border-radius: 14px !important;
        color: #eafff8 !important;
        background: linear-gradient(145deg, rgba(3,27,20,.99), rgba(2,18,13,.99)) !important;
        box-shadow: 0 22px 55px rgba(0,0,0,.48), 0 0 28px rgba(57,230,189,.08) !important;
    }
    [data-testid="stMultiSelectDropdown"] [role="option"] { color:#dff9f0 !important; border-radius:9px; }
    [data-testid="stMultiSelectDropdown"] [role="option"]:hover,
    [data-testid="stMultiSelectDropdown"] [role="option"][data-focused="true"] {
        color:#f5fffb !important;
        background:rgba(57,230,189,.14) !important;
    }
    [data-testid="stMultiSelectDropdown"] [role="option"][aria-selected="true"] {
        color:#bfffe8 !important;
        background:rgba(37,181,136,.18) !important;
    }

    /* Buttons */
    .stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-secondary"] {
        min-height: 44px;
        border: 1px solid rgba(133, 215, 255, .34) !important;
        border-radius: 999px !important;
        color: #ecfaff !important;
        font-weight: 700 !important;
        background: linear-gradient(120deg, rgba(18, 82, 64, .84), rgba(10, 53, 42, .76)) !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .09), 0 9px 24px rgba(0, 0, 0, .18);
        transition: border-color .18s ease, transform .18s ease, box-shadow .18s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stBaseButton-secondary"]:hover {
        color: white !important;
        border-color: rgba(115, 227, 255, .72) !important;
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(31, 217, 160, .18), inset 0 1px 0 rgba(255, 255, 255, .13);
    }
    [data-testid^="stBaseButton-primary"] {
        min-height: 46px !important;
        border-color: rgba(88, 239, 220, .72) !important;
        color: #032019 !important;
        background: linear-gradient(120deg, #62efc3, #8affdf) !important;
        box-shadow: 0 12px 30px rgba(31, 212, 156, .2), inset 0 1px 0 rgba(255,255,255,.42) !important;
    }
    [data-testid^="stBaseButton-primary"] p,
    [data-testid^="stBaseButton-primary"] span,
    [data-testid^="stBaseButton-primary"] svg { color: #032019 !important; fill: currentColor; font-weight: 800 !important; }
    [data-testid^="stBaseButton-primary"]:hover {
        color: #021812 !important;
        border-color: #9ff8ed !important;
        background: linear-gradient(120deg, #78f7d1, #a1ffe7) !important;
        box-shadow: 0 16px 36px rgba(31, 195, 202, .3), inset 0 1px 0 rgba(255,255,255,.55) !important;
    }
    [data-testid^="stBaseButton-primary"]:hover p,
    [data-testid^="stBaseButton-primary"]:hover span,
    [data-testid^="stBaseButton-primary"]:hover svg { color:#021812 !important; }
    [data-testid^="stBaseButton-primary"]:active { transform:translateY(0) scale(.992) !important; }
    .stButton > button:focus-visible, .stDownloadButton > button:focus-visible { outline: 3px solid rgba(98, 220, 255, .48) !important; outline-offset: 2px; }
    .stButton > button:disabled, .stDownloadButton > button:disabled,
    [data-testid^="stBaseButton"]:disabled {
        color: #91a69f !important;
        border-color: rgba(145,166,159,.16) !important;
        background: rgba(24,40,35,.68) !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
        opacity: .72 !important;
        transform: none !important;
    }

    /* Metrics and data surfaces */
    [data-testid="stMetric"] {
        position: relative;
        overflow: hidden;
        min-height: 122px;
        padding: 1rem 1.05rem;
        border: 1px solid var(--line);
        border-radius: 22px;
        background:
            linear-gradient(145deg, rgba(11, 48, 37, .79), rgba(3, 20, 15, .88));
        box-shadow: var(--glass-shadow);
        transform-style: preserve-3d;
    }
    [data-testid="stMetric"]::after {
        content: "";
        position: absolute;
        width: 95px;
        height: 95px;
        right: -46px;
        bottom: -60px;
        border-radius: 50%;
        background: rgba(94, 244, 192, .18);
        filter: blur(12px);
    }
    [data-testid="stMetricLabel"] { color: #9fb7cc; font-weight: 650; }
    [data-testid="stMetricValue"] { color: #f8fcff; font-weight: 790; letter-spacing: -.045em; }
    [data-testid="stMetricDelta"] svg { filter: drop-shadow(0 0 5px currentColor); }
    [data-testid="stPlotlyChart"], [data-testid="stDataFrame"], [data-testid="stJson"] {
        overflow: hidden;
        width: 100%;
        min-width: 0;
        border: 1px solid var(--line);
        border-radius: 24px;
        background: linear-gradient(145deg, rgba(4, 23, 17, .88), rgba(2, 12, 10, .94));
        box-shadow: var(--glass-shadow);
    }
    [data-testid="stPlotlyChart"], .kpi-card, .viz-feature, .answer-card { contain:layout paint; }
    [data-testid="stPlotlyChart"] > div,
    [data-testid="stPlotlyChart"] .js-plotly-plot,
    [data-testid="stPlotlyChart"] .plot-container { width: 100% !important; min-width: 0 !important; }
    [data-testid="stDataFrame"] { padding: .2rem; }

    /* Exploration workspace: compact controls with a larger analytical canvas */
    .st-key-exploration_workspace { margin-top:-.12rem; gap:.72rem !important; }
    .st-key-exploration_workspace > [data-testid="stLayoutWrapper"]:has(h2#data-exploration) {
        border-radius:18px !important;
    }
    .st-key-exploration_workspace > [data-testid="stLayoutWrapper"]:has(h2#data-exploration) > [data-testid="stVerticalBlock"] {
        gap:.34rem !important;
        padding:.78rem .95rem !important;
    }
    .st-key-exploration_workspace > [data-testid="stLayoutWrapper"]:has(h2#data-exploration) h2 {
        margin:.05rem 0 .12rem !important;
        padding:.18rem 0 !important;
        font-size:clamp(1.65rem,2.8vw,2.3rem) !important;
    }
    .st-key-exploration_workspace > [data-testid="stLayoutWrapper"]:has(h2#data-exploration) [data-testid="stCaptionContainer"] {
        margin:0 !important;
    }
    .st-key-animation_workspace {
        margin-top:.15rem;
        padding:.72rem;
        border:1px solid rgba(127,255,213,.22);
        border-radius:22px;
        background:linear-gradient(145deg,rgba(4,28,20,.82),rgba(2,15,11,.94));
        box-shadow:0 22px 58px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.045);
    }
    .st-key-animation_workspace > [data-testid="stVerticalBlock"] { gap:.55rem !important; }
    .animation-header { display:flex; flex-direction:column; gap:.16rem; padding:.08rem .25rem .12rem; }
    .animation-header span { color:#7fffe1; font-size:.64rem; font-weight:850; letter-spacing:.14em; text-transform:uppercase; }
    .animation-header strong { color:#f5fffb; font-size:1rem; line-height:1.25; }
    .animation-header small { color:#a8c2b8; font-size:.73rem; line-height:1.42; }
    .st-key-animation_workspace [data-testid="stSelectbox"] { margin:0 !important; }
    .st-key-animation_workspace [data-testid="stSelectbox"] label { color:#cfe5dd !important; font-size:.73rem !important; font-weight:760 !important; }
    .st-key-animation_workspace [data-testid="stPlotlyChart"] {
        min-height:650px;
        border-color:rgba(127,255,213,.3);
        border-radius:20px;
        background:radial-gradient(circle at 50% 0,rgba(28,104,77,.12),transparent 42%),rgba(1,13,9,.72);
    }

    /* Tabs, expanders, status, alerts */
    [data-testid="stButtonGroup"] { width:100%; }
    [data-testid="stButtonGroup"] [role="radiogroup"] {
        display:grid !important;
        grid-template-columns:repeat(auto-fit,minmax(104px,1fr));
        gap:.42rem;
        width:100%;
        padding:.36rem;
        border:1px solid rgba(127,255,213,.17);
        border-radius:18px;
        background:rgba(4,25,19,.8);
    }
    [data-testid="stButtonGroup"] button[role="radio"] {
        width:100%;
        min-width:0;
        min-height:44px;
        padding:.5rem .65rem;
        border:1px solid rgba(127,255,213,.1);
        border-radius:13px;
        color:#b9d7cc;
        background:rgba(5,37,28,.38);
        font-weight:700;
        transition:transform .18s ease,border-color .18s ease,background .18s ease,box-shadow .18s ease;
    }
    [data-testid="stButtonGroup"] button[role="radio"]:hover {
        transform:translateY(-1px);
        border-color:rgba(127,255,213,.3);
        background:rgba(37,139,105,.16);
    }
    [data-testid="stButtonGroup"] button[role="radio"][aria-checked="true"] {
        color:#f5fffb;
        border-color:rgba(127,255,213,.46);
        background:linear-gradient(120deg,rgba(45,189,143,.34),rgba(17,103,78,.4));
        box-shadow:inset 0 1px 0 rgba(255,255,255,.1),0 7px 18px rgba(0,0,0,.2);
    }
    [data-testid="stTabs"] [role="tablist"] {
        gap: .35rem;
        padding: .34rem;
        overflow-x: auto;
        border: 1px solid rgba(128, 207, 255, .16);
        border-radius: 999px;
        background: rgba(4, 25, 19, .82);
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
        background: linear-gradient(120deg, rgba(39, 164, 126, .72), rgba(19, 103, 78, .78));
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .12), 0 7px 18px rgba(0, 0, 0, .2);
    }
    [data-testid="stExpander"], [data-testid="stStatusWidget"], [data-testid="stAlert"] {
        overflow: hidden;
        border: 1px solid var(--line) !important;
        border-radius: 18px !important;
        background: rgba(5, 29, 22, .78) !important;
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

    /* AI question composer: strong contrast, clear boundary, and touch-safe action */
    .st-key-ai_task_form,
    [data-testid="stForm"]:has(textarea[aria-label="Describe the task or outcome"]) {
        padding: .78rem !important;
        border: 1px solid rgba(127,255,213,.2) !important;
        border-radius: 18px !important;
        background: linear-gradient(145deg, rgba(3,24,17,.94), rgba(4,35,25,.82)) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.045), 0 16px 34px rgba(0,0,0,.18);
    }
    .st-key-ai_task_form [data-testid="stTextAreaRootElement"],
    [data-testid="stForm"]:has(textarea[aria-label="Describe the task or outcome"]) [data-testid="stTextAreaRootElement"] {
        overflow: hidden;
        border: 1px solid rgba(127,255,213,.25) !important;
        border-radius: 14px !important;
        background: #03150f !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.035);
        transition: border-color .2s ease, box-shadow .2s ease, background .2s ease;
    }
    .st-key-ai_task_form [data-testid="stTextAreaRootElement"]:focus-within,
    [data-testid="stForm"]:has(textarea[aria-label="Describe the task or outcome"]) [data-testid="stTextAreaRootElement"]:focus-within {
        border-color: rgba(127,255,225,.72) !important;
        background:#041b14 !important;
        box-shadow: 0 0 0 3px rgba(57,230,189,.11), 0 0 24px rgba(57,230,189,.09);
    }
    textarea[aria-label="Describe the task or outcome"] {
        min-height: 106px !important;
        padding: .9rem !important;
        color:#f2fff9 !important;
        background:transparent !important;
        font-size:.92rem !important;
        line-height:1.55 !important;
    }
    .ai-scope-note {
        display:flex;
        align-items:flex-start;
        gap:.55rem;
        margin:.15rem 0 .65rem;
        padding:.62rem .7rem;
        border:1px solid rgba(127,255,213,.14);
        border-radius:13px;
        color:#b8d2c8;
        background:rgba(26,92,70,.11);
        font-size:.76rem;
        line-height:1.5;
    }
    .ai-scope-note span { color:var(--teal); font-size:.82rem; filter:drop-shadow(0 0 6px rgba(57,230,189,.42)); }
    .composer-guidance { margin:.5rem .15rem .15rem; color:#a6bfb6; font-size:.72rem; line-height:1.45; }

    /* Persistent AI task launcher */
    .agent-launcher {
        position:fixed;
        z-index:999990;
        right:1.2rem;
        bottom:1.15rem;
        display:flex;
        align-items:center;
        gap:.65rem;
        min-width:172px;
        min-height:58px;
        padding:.55rem .78rem .55rem .58rem;
        border:1px solid rgba(139,255,222,.52);
        border-radius:19px;
        color:#effff9 !important;
        text-decoration:none !important;
        background:linear-gradient(135deg,rgba(5,52,38,.97),rgba(3,28,21,.98));
        box-shadow:0 20px 55px rgba(0,0,0,.48),0 0 30px rgba(57,230,189,.16),inset 0 1px 0 rgba(255,255,255,.11);
        backdrop-filter:none;
        -webkit-backdrop-filter:none;
        transform:translateZ(0);
        transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease,background .22s ease;
    }
    .agent-launcher::before {
        content:"";
        position:absolute;
        inset:-5px;
        z-index:-1;
        border:1px solid rgba(90,255,207,.18);
        border-radius:23px;
        opacity:.45;
    }
    .agent-launcher-icon {
        position:relative;
        display:grid;
        place-items:center;
        flex:0 0 auto;
        width:42px;
        height:42px;
        border-radius:14px;
        color:#032019;
        background:linear-gradient(135deg,#62efc3,#9affdf);
        box-shadow:0 8px 22px rgba(34,209,157,.25);
    }
    .agent-launcher-icon svg { width:25px; height:25px; fill:none; stroke:currentColor; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
    .agent-launcher-copy { display:flex; flex-direction:column; gap:.04rem; line-height:1.18; }
    .agent-launcher-copy strong { color:#f5fffb; font-size:.84rem; font-weight:850; }
    .agent-launcher-copy small { color:#a7c8bc; font-size:.67rem; }
    .agent-launcher-status {
        position:absolute;
        top:6px;
        left:43px;
        width:8px;
        height:8px;
        border:2px solid #073023;
        border-radius:50%;
        background:#7fffe1;
        box-shadow:0 0 10px rgba(127,255,225,.72);
    }
    .agent-launcher:hover {
        transform:translateY(-4px) scale(1.015);
        border-color:rgba(167,255,231,.82);
        background:linear-gradient(135deg,rgba(8,72,52,.98),rgba(4,38,28,.99));
        box-shadow:0 25px 68px rgba(0,0,0,.55),0 0 40px rgba(57,230,189,.24),inset 0 1px 0 rgba(255,255,255,.15);
    }
    .agent-launcher:hover::before { animation:agentBeacon .8s ease-out both; }
    .agent-launcher:focus-visible { outline:3px solid #9affdf; outline-offset:4px; }
    .agent-launcher.active { border-color:rgba(127,255,225,.78); }
    @keyframes agentBeacon { 0%{transform:scale(.96);opacity:.65} 72%,100%{transform:scale(1.12);opacity:0} }

    .agent-task-receipt {
        display:grid;
        grid-template-columns:repeat(5,minmax(0,1fr));
        gap:.42rem;
        margin:.45rem 0 .8rem;
        padding:.55rem;
        border:1px solid rgba(127,255,213,.17);
        border-radius:17px;
        background:rgba(3,27,20,.7);
    }
    .agent-task-receipt span { display:flex; align-items:center; gap:.34rem; color:#b9d2c9; font-size:.67rem; font-weight:720; }
    .agent-task-receipt i { display:grid; place-items:center; width:1.15rem; height:1.15rem; border-radius:50%; color:#032019; background:#7fffe1; font-style:normal; font-size:.62rem; font-weight:900; }

    /* Aurora command hero inspired by the supplied Aether reference */
    .app-hero {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        min-height: 270px;
        margin-bottom: 1rem;
        padding: clamp(1.6rem, 3.2vw, 2.8rem);
        border: 1px solid rgba(139, 255, 215, .25);
        border-radius: 24px;
        color: white;
        background:
            radial-gradient(ellipse at 75% 30%, rgba(79, 255, 193, .24), transparent 28%),
            radial-gradient(ellipse at 88% 112%, rgba(49, 190, 144, .22), transparent 32%),
            linear-gradient(135deg, rgba(2, 13, 10, .98), rgba(5, 32, 24, .94));
        box-shadow: 0 30px 90px rgba(0, 0, 0, .58), 0 0 55px rgba(50, 236, 176, .08), inset 0 1px 0 rgba(255, 255, 255, .08);
        -webkit-backdrop-filter: none;
        backdrop-filter: none;
    }
    .app-hero::before {
        content: "";
        position: absolute;
        z-index: -1;
        width: 72%;
        height: 160%;
        right: -8%;
        top: -74%;
        transform: rotate(-9deg) skewX(-18deg);
        background: linear-gradient(90deg, transparent 12%, rgba(73, 255, 192, .06) 38%, rgba(105, 255, 210, .25) 49%, rgba(42, 177, 134, .05) 67%, transparent 83%);
        filter: blur(18px);
        opacity:.86;
    }
    .app-hero::after {
        content: "·  ·       ·    ·      ·";
        position: absolute;
        right: 5%;
        top: 21%;
        color: rgba(194, 255, 233, .48);
        font-size: 1.1rem;
        letter-spacing: .75rem;
    }
    .app-hero.compact {
        min-height: 0;
        padding: 1rem 1.25rem;
        border-radius: 22px;
    }
    .app-hero.compact::after { width: 26%; opacity: .65; }
    .app-hero.compact .app-eyebrow { display: none; }
    .app-hero.compact .app-title { font-size: clamp(1.45rem, 2.4vw, 2rem); }
    .app-hero.compact .app-subtitle { display: none; }
    .app-hero.compact .hero-pills { margin-top: .65rem; }
    .app-hero.compact .hero-pill:nth-child(n+4) { display: none; }
    .app-eyebrow, .section-kicker {
        margin-bottom: .5rem;
        color: #7fffdc;
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: .17em;
        text-transform: uppercase;
    }
    .app-title { margin: 0; max-width: 980px; color: white; font-size: clamp(2rem, 4vw, 3.5rem); font-weight: 800; letter-spacing: -.045em; line-height: 1.04; }
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
    .hero-terrain {
        position: absolute;
        z-index: -1;
        left: -2%;
        right: -2%;
        bottom: -1px;
        height: 38%;
        opacity: .82;
        background:
            linear-gradient(180deg, rgba(9, 33, 23, .35), #010503 78%),
            repeating-linear-gradient(104deg, rgba(121, 255, 211, .13) 0 1px, transparent 1px 11px);
        clip-path: polygon(0 77%, 6% 53%, 12% 68%, 20% 42%, 28% 72%, 38% 49%, 47% 74%, 58% 35%, 65% 56%, 73% 44%, 82% 69%, 91% 38%, 100% 63%, 100% 100%, 0 100%);
        filter: drop-shadow(0 -14px 21px rgba(68, 255, 193, .08));
    }
    .app-hero.compact .hero-terrain { height: 28%; opacity: .42; }

    /* Custom components */
    .sidebar-brand { padding: .25rem .08rem 1rem; }
    .sidebar-home-link {
        display: flex;
        align-items: center;
        gap: .8rem;
        padding: .45rem;
        margin: -.35rem -.35rem .2rem;
        border: 1px solid transparent;
        border-radius: 18px;
        color: inherit !important;
        text-decoration: none !important;
        transition: background .2s ease, border-color .2s ease, transform .2s ease;
    }
    .sidebar-home-link:hover {
        border-color: rgba(126,255,211,.18);
        background: rgba(48,193,146,.08);
        transform: translateY(-1px);
    }
    .sidebar-home-link:focus-visible { outline: 3px solid rgba(127,255,225,.58) !important; }
    .sidebar-mark {
        width: 46px;
        height: 46px;
        display: grid;
        place-items: center;
        flex: 0 0 auto;
        border: 0;
        border-radius: 16px;
        background: transparent;
        color: white;
        font-weight: 800;
        box-shadow: 0 10px 30px rgba(34, 164, 222, .22);
    }
    .sidebar-mark svg { width: 100%; height: 100%; display: block; }
    .sidebar-title { color: white; font-size: 1.08rem; font-weight: 700; line-height: 1.2; }
    .sidebar-subtitle { margin-top: .3rem; color: #88a2b9; font-size: .78rem; }
    .sidebar-live { display:flex; align-items:center; gap:.5rem; margin:.8rem 0 .2rem; color:#a8bfd2; font-size:.72rem; }

    /* Top workspace navigation */
    .st-key-top_navigation {
        position: sticky;
        z-index: 90;
        top: .45rem;
        margin: 0 0 .8rem;
        padding: .7rem .78rem .78rem;
        border: 1px solid rgba(130,255,215,.18);
        border-radius: 18px;
        background: linear-gradient(120deg, rgba(2,14,10,.985), rgba(6,35,26,.97));
        box-shadow: 0 16px 45px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.05);
        -webkit-backdrop-filter: none;
        backdrop-filter: none;
        transform:translateZ(0);
    }
    .st-key-top_navigation > div {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        gap: .38rem;
    }
    .top-nav-label {
        display: inline-flex;
        align-items: center;
        min-height: 30px;
        padding: 0 .55rem;
        color: #7fffdc;
        font-size: .7rem;
        font-weight: 800;
        letter-spacing: .16em;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .st-key-top_navigation [data-testid="stRadio"] { width:100%; min-width:0; }
    .st-key-top_navigation [role="radiogroup"] {
        display: grid !important;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        align-items: stretch;
        gap: .5rem !important;
        width: 100%;
        overflow: visible !important;
        padding: .1rem;
    }
    .st-key-top_navigation [role="radiogroup"] label {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        min-width: 0;
        min-height: 58px;
        padding: .72rem .58rem;
        border: 1px solid rgba(127,255,225,.09);
        border-radius: 16px;
        background: rgba(5,37,28,.36);
        cursor: pointer;
        transition: color .2s ease, background .2s ease, border-color .2s ease, transform .2s cubic-bezier(.2,.8,.2,1), box-shadow .2s ease;
    }
    .st-key-top_navigation [role="radiogroup"] label:hover {
        border-color: rgba(130,255,215,.32);
        background: linear-gradient(120deg, rgba(58,202,154,.16), rgba(25,111,88,.13));
        transform: perspective(500px) translateY(-3px) translateZ(8px);
        box-shadow: 0 10px 24px rgba(0,0,0,.24), 0 0 18px rgba(72,239,185,.08);
    }
    .st-key-top_navigation [role="radiogroup"] label[data-selected="true"] {
        border-color: rgba(127,255,225,.46);
        background: linear-gradient(120deg, rgba(45,189,143,.34), rgba(17,103,78,.4));
        box-shadow: inset 0 1px 0 rgba(255,255,255,.1), 0 9px 24px rgba(0,0,0,.24), 0 0 20px rgba(57,230,189,.07);
    }
    .st-key-top_navigation [role="radiogroup"] label p {
        display:flex;
        align-items:center;
        justify-content:center;
        gap:.52rem;
        width:100%;
        margin:0;
        color:#cbe3da;
        font-size:.92rem;
        font-weight:700;
        letter-spacing:-.01em;
        line-height:1.2;
        text-align:center;
        white-space:normal;
        text-wrap:balance;
    }
    .st-key-top_navigation [role="radiogroup"] label p::before {
        content:"";
        width:1.18rem;
        height:1.18rem;
        flex:0 0 1.18rem;
        background:currentColor;
        -webkit-mask-position:center;
        mask-position:center;
        -webkit-mask-repeat:no-repeat;
        mask-repeat:no-repeat;
        -webkit-mask-size:contain;
        mask-size:contain;
        transition:transform .2s ease, filter .2s ease;
    }
    .st-key-top_navigation [role="radiogroup"] label:nth-of-type(1) p::before {
        -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='black' d='M4 4h7v7H4V4Zm9 0h7v7h-7V4ZM4 13h7v7H4v-7Zm9 0h7v7h-7v-7Z'/%3E%3C/svg%3E");
        mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='black' d='M4 4h7v7H4V4Zm9 0h7v7h-7V4ZM4 13h7v7H4v-7Zm9 0h7v7h-7v-7Z'/%3E%3C/svg%3E");
    }
    .st-key-top_navigation [role="radiogroup"] label:nth-of-type(2) p::before {
        -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' d='M4 18 9 12l4 3 7-9M4 20h16'/%3E%3C/svg%3E");
        mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' d='M4 18 9 12l4 3 7-9M4 20h16'/%3E%3C/svg%3E");
    }
    .st-key-top_navigation [role="radiogroup"] label:nth-of-type(3) p::before {
        -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='black' d='m12 2 1.45 4.05L17.5 7.5l-4.05 1.45L12 13l-1.45-4.05L6.5 7.5l4.05-1.45L12 2Zm6 10 1.05 2.95L22 16l-2.95 1.05L18 20l-1.05-2.95L14 16l2.95-1.05L18 12ZM6 13l1.05 2.95L10 17l-2.95 1.05L6 21l-1.05-2.95L2 17l2.95-1.05L6 13Z'/%3E%3C/svg%3E");
        mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='black' d='m12 2 1.45 4.05L17.5 7.5l-4.05 1.45L12 13l-1.45-4.05L6.5 7.5l4.05-1.45L12 2Zm6 10 1.05 2.95L22 16l-2.95 1.05L18 20l-1.05-2.95L14 16l2.95-1.05L18 12ZM6 13l1.05 2.95L10 17l-2.95 1.05L6 21l-1.05-2.95L2 17l2.95-1.05L6 13Z'/%3E%3C/svg%3E");
    }
    .st-key-top_navigation [role="radiogroup"] label:nth-of-type(4) p::before {
        -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='black' stroke-width='2.1' stroke-linecap='round' stroke-linejoin='round' d='m12 3 8 6-8 6-8-6 8-6Zm-8 11 8 6 8-6'/%3E%3C/svg%3E");
        mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='black' stroke-width='2.1' stroke-linecap='round' stroke-linejoin='round' d='m12 3 8 6-8 6-8-6 8-6Zm-8 11 8 6 8-6'/%3E%3C/svg%3E");
    }
    .st-key-top_navigation [role="radiogroup"] label:nth-of-type(5) p::before {
        -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' d='M12 3 5 6v5c0 4.6 2.9 8.2 7 10 4.1-1.8 7-5.4 7-10V6l-7-3Zm-3 9 2 2 4-5'/%3E%3C/svg%3E");
        mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round' d='M12 3 5 6v5c0 4.6 2.9 8.2 7 10 4.1-1.8 7-5.4 7-10V6l-7-3Zm-3 9 2 2 4-5'/%3E%3C/svg%3E");
    }
    .st-key-top_navigation [role="radiogroup"] label:nth-of-type(6) p::before {
        -webkit-mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='black' stroke-width='2.1' stroke-linecap='round' stroke-linejoin='round' d='M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8m-6-8v6h6M12 15l7-7m-4 0h4v4'/%3E%3C/svg%3E");
        mask-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='none' stroke='black' stroke-width='2.1' stroke-linecap='round' stroke-linejoin='round' d='M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8m-6-8v6h6M12 15l7-7m-4 0h4v4'/%3E%3C/svg%3E");
    }
    .st-key-top_navigation [role="radiogroup"] label:hover p::before { transform:translateY(-1px) scale(1.08); }
    .st-key-top_navigation [role="radiogroup"] label[data-selected="true"] p::before { filter:drop-shadow(0 0 7px rgba(127,255,225,.38)); }
    .st-key-top_navigation [role="radiogroup"] label[data-selected="true"] p { color:#f5fffb; }
    .st-key-top_navigation [role="radiogroup"] label:focus-within { border-color:rgba(127,255,225,.5); box-shadow:0 0 0 3px rgba(127,255,225,.12); }
    .st-key-top_navigation [data-testid="stRadioOption"] > div > div > div:first-child { display:none !important; }

    .section-shell {
        margin: .2rem 0 1.1rem;
        padding: 1.15rem 1.25rem;
        border: 1px solid rgba(133, 211, 255, .16);
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(13, 39, 62, .65), rgba(8, 26, 43, .55));
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .05);
    }
    .section-title { margin: 0; color: #f6fbff; font-size: clamp(1.55rem, 2.5vw, 2.15rem); font-weight: 700; line-height: 1.1; }
    .section-description { margin: .5rem 0 0; max-width: 850px; color: #9eb3c7; font-size: .9rem; line-height: 1.55; }
    .viz-ribbon {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: .7rem;
        margin: .2rem 0 1.05rem;
        perspective: 1000px;
    }
    .viz-feature {
        position: relative;
        overflow: hidden;
        min-height: 92px;
        padding: .9rem 1rem;
        border: 1px solid rgba(128, 255, 213, .15);
        border-radius: 17px;
        background: linear-gradient(145deg, rgba(8, 40, 30, .79), rgba(3, 20, 15, .88));
        box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 18px 42px rgba(0,0,0,.22);
        transform-style: preserve-3d;
        animation: telemetryLaunch .62s cubic-bezier(.2,.8,.2,1) both;
    }
    .viz-feature:nth-child(2) { animation-delay: .06s; }
    .viz-feature:nth-child(3) { animation-delay: .12s; }
    .viz-feature:nth-child(4) { animation-delay: .18s; }
    .viz-feature::after {
        content: "";
        position: absolute;
        width: 80px;
        height: 80px;
        right: -38px;
        bottom: -45px;
        border-radius: 50%;
        background: rgba(78, 245, 188, .13);
        filter: blur(8px);
    }
    .viz-feature::before {
        content: "";
        position: absolute;
        z-index: 0;
        inset: 0;
        width: 42%;
        pointer-events: none;
        opacity: 0;
        background: linear-gradient(100deg, transparent, rgba(151,255,222,.12), transparent);
        transform: translateX(-180%) skewX(-15deg);
    }
    .viz-feature b { display:block; color:#f0fff9; font-size:.85rem; margin-bottom:.3rem; }
    .viz-feature span { color:#8db3a5; font-size:.71rem; line-height:1.45; }
    .viz-feature b, .viz-feature span, .telemetry-rail { position:relative; z-index:1; }
    .telemetry-rail, .kpi-meter {
        overflow: hidden;
        height: 4px;
        border-radius: 999px;
        background: rgba(126,255,211,.08);
        box-shadow: inset 0 1px 2px rgba(0,0,0,.42);
    }
    .telemetry-rail { margin-top:.72rem; }
    .telemetry-rail i, .kpi-meter i {
        position: relative;
        display: block;
        width: var(--meter, 0%);
        height: 100%;
        border-radius: inherit;
        transform-origin: left center;
        background: linear-gradient(90deg, #24b98d, #7fffe1 72%, #e4fff7);
        box-shadow: 0 0 12px rgba(84,255,202,.55);
    }
    .telemetry-rail i::after, .kpi-meter i::after {
        content: "";
        position: absolute;
        top: 50%;
        right: -1px;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #eafff9;
        box-shadow: 0 0 10px #7fffe1, 0 0 20px rgba(127,255,225,.7);
        transform: translateY(-50%);
    }

    /* Data-driven KPI telemetry */
    .kpi-card {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        min-height: 136px;
        padding: 1rem 1.05rem .9rem;
        border: 1px solid rgba(132,255,213,.2);
        border-radius: 22px;
        background:
            radial-gradient(circle at 112% 112%, rgba(78,245,188,.17), transparent 38%),
            linear-gradient(145deg, rgba(8,40,30,.88), rgba(3,20,15,.94));
        box-shadow: var(--glass-shadow);
        transform-style: preserve-3d;
        animation: telemetryLaunch .68s var(--delay, 0ms) cubic-bezier(.2,.8,.2,1) both;
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        z-index: 0;
        top: 0;
        left: 10%;
        width: 80%;
        height: 1px;
        opacity: .7;
        background: linear-gradient(90deg, transparent, rgba(127,255,225,.78), transparent);
        filter: drop-shadow(0 0 7px rgba(127,255,225,.62));
    }
    .kpi-card::after {
        content: "";
        position: absolute;
        z-index: -1;
        width: 110px;
        height: 110px;
        right: -55px;
        bottom: -68px;
        border-radius: 50%;
        background: rgba(94,244,192,.2);
        filter: blur(14px);
    }
    .kpi-scan {
        position: absolute;
        z-index: 0;
        inset: 0;
        width: 38%;
        pointer-events: none;
        opacity: 0;
        background: linear-gradient(100deg, transparent, rgba(167,255,226,.12), transparent);
        transform: translateX(-190%) skewX(-15deg);
    }
    .kpi-label, .kpi-value, .kpi-delta, .kpi-meter { position:relative; z-index:1; }
    .kpi-label { color:#a8c4ba; font-size:.78rem; font-weight:720; letter-spacing:-.01em; }
    .kpi-value {
        margin:.55rem 0 .34rem;
        color:#f8fffc;
        font-size:clamp(1.65rem,2.6vw,2.25rem);
        font-weight:800;
        letter-spacing:-.055em;
        line-height:1;
        text-shadow:0 0 24px rgba(127,255,225,.06);
    }
    .kpi-delta {
        align-self:flex-start;
        padding:.23rem .46rem;
        border:1px solid rgba(150,255,216,.12);
        border-radius:999px;
        color:#b8d0c7;
        background:rgba(92,132,118,.15);
        font-size:.69rem;
        font-weight:760;
        line-height:1.15;
    }
    .kpi-card.positive .kpi-delta { color:#b9fdd7; background:rgba(29,164,96,.24); border-color:rgba(103,255,170,.15); }
    .kpi-card.negative .kpi-delta { color:#ffd2d7; background:rgba(184,65,79,.25); border-color:rgba(255,114,133,.18); }
    .kpi-card.negative .kpi-meter i { background:linear-gradient(90deg,#a7394c,#ff7285 72%,#ffd7dd); box-shadow:0 0 12px rgba(255,114,133,.5); }
    .kpi-card.neutral .kpi-meter i { background:linear-gradient(90deg,#408c7b,#9ed9cb); box-shadow:0 0 9px rgba(158,217,203,.28); }
    .kpi-meter { margin-top:auto; }
    .ai-workspace-intro { margin:.1rem 0 .8rem; padding:.35rem .15rem; }
    .ai-workspace-intro h2 { margin:.18rem 0 .25rem; color:#f6fbff; font-size:clamp(1.65rem,2.6vw,2.2rem); line-height:1.1; }
    .ai-workspace-intro p { margin:0; max-width:920px; color:#9eb3c7; font-size:.88rem; line-height:1.5; }
    .demo-strip { margin:.7rem 0; padding:.62rem .85rem; border:1px solid rgba(230,201,99,.24); border-radius:14px; color:#f1e5b9; background:rgba(130,108,36,.22); font-size:.78rem; line-height:1.45; }
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
    .build-marker {
        display:flex;
        justify-content:flex-end;
        align-items:center;
        gap:.45rem;
        margin:2.2rem 0 -2.4rem;
        padding:.55rem .15rem;
        color:#718b82;
        font-size:.68rem;
        letter-spacing:.035em;
    }
    .build-marker::before {
        content:"";
        width:.38rem;
        height:.38rem;
        border-radius:50%;
        background:var(--teal);
        box-shadow:0 0 10px rgba(57,230,189,.42);
    }
    .mode-card {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: .9rem;
        align-items: center;
        margin: .4rem 0 1.15rem;
        padding: 1rem 1.1rem;
        border: 1px solid rgba(127, 255, 213, .24);
        border-radius: 22px;
        background: radial-gradient(circle at 96% 110%, rgba(57,230,189,.2), transparent 23%), linear-gradient(135deg, rgba(4,29,21,.94), rgba(7,48,35,.8));
        box-shadow: var(--glass-shadow);
    }
    .mode-orb { position:relative; width:46px; height:46px; display:grid; place-items:center; border-radius:16px; background:transparent; color:#02111c; font-size:1.25rem; box-shadow:0 0 30px rgba(77,202,255,.28); transform-style:preserve-3d; }
    .mode-orb svg { width: 100%; height: 100%; display: block; }
    .mode-orb::after { content:""; position:absolute; inset:5px; border:1px solid rgba(255,255,255,.22); border-radius:12px; transform:translateZ(8px); pointer-events:none; }
    .mode-card strong { color: #f5fbff; font-size: .95rem; }
    .mode-card span { color: #b3cbc2; font-size: .82rem; line-height: 1.5; }
    .mode-meta { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:.55rem; }
    .mode-meta b { padding:.28rem .55rem; border:1px solid rgba(127,255,213,.18); border-radius:999px; color:#caffed; background:rgba(57,230,189,.08); font-size:.7rem; font-weight:700; }
    .answer-card {
        position: relative;
        overflow: hidden;
        margin: .65rem 0 1rem;
        padding: 1.25rem 1.35rem;
        border: 1px solid rgba(127, 255, 213, .3);
        border-radius: 24px;
        background: radial-gradient(circle at 96% 120%, rgba(57,230,189,.2), transparent 25%), linear-gradient(145deg, rgba(5,35,25,.95), rgba(3,22,16,.94));
        box-shadow: var(--glass-shadow), 0 0 38px rgba(57,230,189,.07);
    }
    .answer-card h3 { margin: .15rem 0 .45rem; color: #f7fcff; font-size: 1.3rem; line-height: 1.25; }
    .answer-card p { margin: 0 0 .85rem; max-width: 950px; color: #c0d5cd; line-height: 1.62; }
    .answer-eyebrow { color:#7fffe1; font-size:.69rem; font-weight:800; letter-spacing:.15em; text-transform:uppercase; }
    .response-heading {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:1rem;
        margin:.15rem 0 .65rem;
    }
    .response-heading h3 { margin:.12rem 0 0; color:#f5fffB; font-size:1.22rem; }
    .ai-chat-thread { display:flex; flex-direction:column; gap:.7rem; margin:.2rem 0 .9rem; }
    .ai-chat-turn { display:flex; align-items:flex-start; gap:.65rem; }
    .ai-chat-turn.user { justify-content:flex-end; }
    .ai-chat-avatar {
        display:grid;
        place-items:center;
        flex:0 0 auto;
        width:2rem;
        height:2rem;
        border:1px solid rgba(127,255,213,.27);
        border-radius:11px;
        color:#032019;
        background:linear-gradient(135deg,#62efc3,#8affdf);
        font-size:.72rem;
        font-weight:900;
        box-shadow:0 7px 18px rgba(21,165,121,.16);
    }
    .ai-chat-bubble {
        max-width:min(88%,760px);
        padding:.72rem .85rem;
        border:1px solid rgba(127,255,213,.2);
        border-radius:17px 17px 5px 17px;
        color:#eafff7;
        background:linear-gradient(135deg,rgba(23,105,80,.38),rgba(8,58,43,.42));
        box-shadow:0 10px 26px rgba(0,0,0,.2);
    }
    .ai-chat-label { display:block; margin-bottom:.25rem; color:#97bdb0; font-size:.65rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
    .ai-chat-bubble p { margin:0; color:#effff9; font-size:.88rem; line-height:1.55; }
    .ai-chat-assistant { display:grid; grid-template-columns:2.2rem minmax(0,1fr); gap:.85rem; align-items:start; }
    .ai-chat-assistant .ai-chat-avatar { color:#032019; border-radius:12px; }
    .ai-chat-assistant-content { min-width:0; }
    .trust-pill { padding:.3rem .58rem; color:#b6d7e8; font-size:.69rem; }
    .trust-pill.safe { color:#a7f5d2; border-color:rgba(85,230,165,.24); background:rgba(32,171,117,.09); }
    .ai-guide {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .7rem;
        margin: .2rem 0 1rem;
    }
    .ai-guide > div {
        display: grid;
        grid-template-columns: 2rem 1fr;
        gap: .15rem .65rem;
        align-items: center;
        padding: .78rem .85rem;
        border: 1px solid rgba(127,255,213,.16);
        border-radius: 16px;
        background: rgba(5,35,25,.66);
    }
    .ai-guide span {
        grid-row: 1 / span 2;
        display: grid;
        place-items: center;
        width: 2rem;
        height: 2rem;
        border-radius: 10px;
        color: #03171d;
        background: linear-gradient(135deg, var(--teal), var(--cyan));
        font-weight: 900;
    }
    .ai-guide strong { color:#eefaff; font-size:.78rem; }
    .ai-guide small { color:#a9c1b8; font-size:.67rem; line-height:1.4; }
    .capability-note {
        margin: -.48rem .55rem .7rem;
        padding: .1rem .35rem .48rem;
        border-bottom: 1px solid rgba(125, 220, 255, .08);
        color: #a9c1b8;
        font-size: .69rem;
        line-height: 1.42;
    }
    .ai-pipeline {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(122px, 1fr));
        gap: .55rem;
        margin: .25rem 0 1rem;
        padding: .72rem;
        border: 1px solid rgba(127,255,213,.17);
        border-radius: 18px;
        background: rgba(4,27,20,.78);
    }
    .ai-stage {
        position: relative;
        display: grid;
        grid-template-columns: 1.75rem 1fr;
        align-items: center;
        gap: .2rem .45rem;
        min-width: 0;
        padding: .55rem;
        border-radius: 13px;
        background: linear-gradient(145deg, rgba(18, 53, 79, .72), rgba(9, 35, 57, .75));
    }
    .ai-stage span {
        grid-row: 1 / span 2;
        display: grid;
        place-items: center;
        width: 1.65rem;
        height: 1.65rem;
        border-radius: 9px;
        color: #04151d;
        background: var(--teal);
        font-size: .76rem;
        font-weight: 900;
    }
    .ai-stage strong { color:#effaff; font-size:.73rem; line-height:1.25; }
    .ai-stage small { color:#a6c0b7; font-size:.62rem; line-height:1.3; }
    .ai-response-empty {
        display: grid;
        place-items: center;
        align-content: center;
        min-height: 350px;
        padding: 2rem;
        text-align: center;
        border: 1px dashed rgba(125, 220, 255, .24);
        border-radius: 22px;
        background:
            radial-gradient(circle at 50% 40%, rgba(45, 212, 191, .09), transparent 13rem),
            rgba(4, 18, 31, .46);
    }
    .ai-response-empty span { color:var(--teal); font-size:2.4rem; filter:drop-shadow(0 0 16px rgba(45,212,191,.45)); }
    .ai-response-empty h3 { margin:.55rem 0 .25rem; color:#f4fbff; font-size:1.35rem; }
    .ai-response-empty p { max-width:580px; margin:0; color:#91a9bc; line-height:1.65; }
    .empty-hint { margin-top:1rem; padding:.55rem .8rem; border:1px solid rgba(98,220,255,.17); border-radius:999px; color:#bdefff; background:rgba(40,127,180,.1); font-size:.74rem; }
    .empty-state {
        padding: 1.4rem;
        text-align: center;
        border: 1px dashed rgba(129, 211, 255, .28);
        border-radius: 22px;
        background: rgba(10, 32, 51, .55);
        color: #9fb7ca;
    }
    .empty-icon { display:block; margin-bottom:.4rem; color:#6edfff; font-size:1.45rem; }

    @keyframes auroraDrift { 0% { transform:translate3d(-3%, -2%, 0) rotate(8deg) skewX(-9deg); opacity:.62; } 100% { transform:translate3d(5%, 4%, 0) rotate(12deg) skewX(-4deg); opacity:1; } }
    @keyframes heroAurora { 0% { transform:translate3d(-6%,0,0) rotate(-9deg) skewX(-18deg); opacity:.72; } 100% { transform:translate3d(7%,4%,0) rotate(-4deg) skewX(-10deg); opacity:1; } }
    @keyframes revealUp { from { opacity:0; transform:translate3d(0,12px,-12px); } to { opacity:1; transform:translate3d(0,0,0); } }
    @keyframes telemetryLaunch {
        from { opacity:0; filter:blur(5px); transform:perspective(900px) translate3d(0,16px,-16px) rotateX(5deg); }
        to { opacity:1; filter:blur(0); transform:perspective(900px) translate3d(0,0,0) rotateX(0); }
    }
    @keyframes railGrow { from { transform:scaleX(0); } to { transform:scaleX(1); } }
    @keyframes scanSweep {
        0%, 64% { opacity:0; transform:translateX(-190%) skewX(-15deg); }
        72% { opacity:.72; }
        100% { opacity:0; transform:translateX(340%) skewX(-15deg); }
    }
    @keyframes edgePulse { 0%,100% { opacity:.42; } 50% { opacity:1; } }
    @keyframes hoverScan {
        from { opacity:0; transform:translateX(-190%) skewX(-15deg); }
        42% { opacity:.82; }
        to { opacity:0; transform:translateX(340%) skewX(-15deg); }
    }
    @keyframes hoverCharge {
        0%,100% { filter:brightness(1); }
        50% { filter:brightness(1.35) drop-shadow(0 0 7px rgba(127,255,225,.42)); }
    }
    @keyframes softFloat { 0%,100% { transform:translate3d(0,0,0) rotateX(0); } 50% { transform:translate3d(0,-3px,8px) rotateX(4deg); } }
    [data-testid="stMetric"], .kpi-card, .viz-feature { animation: revealUp .38s ease both; }
    @media (prefers-reduced-motion: no-preference) {
        .telemetry-rail i { animation:railGrow .95s .28s cubic-bezier(.2,.8,.2,1) both; }
        .kpi-meter i { animation:railGrow .9s calc(var(--delay, 0ms) + .28s) cubic-bezier(.2,.8,.2,1) both; }
        .viz-feature::before, .kpi-scan, .kpi-card::before { animation:none; opacity:0; }
    }
    @media (hover: hover) and (pointer: fine) {
        [data-testid="stMetric"]:hover,
        [data-testid="stVerticalBlockBorderWrapper"]:hover, .viz-feature:hover, .kpi-card:hover {
            animation: none !important;
        }
        [data-testid="stMetric"], .mode-card, .answer-card, [data-testid="stDataFrame"],
        [data-testid="stExpander"], [data-testid="stAlert"], .viz-feature, .kpi-card, .ai-guide > div, .ai-stage,
        .ai-response-empty, .demo-strip, .hero-pill, .filter-pill, .trust-pill {
            transform: perspective(900px) translateZ(0);
            transition: transform .24s cubic-bezier(.2,.8,.2,1), border-color .24s ease, box-shadow .24s ease, filter .24s ease, background .24s ease;
        }
        [data-testid="stPlotlyChart"] {
            transform: none !important;
            transition: border-color .2s ease, box-shadow .2s ease;
        }
        [data-testid="stMetric"]:hover, .mode-card:hover, .answer-card:hover, .ai-response-empty:hover {
            transform: perspective(900px) translateY(-3px) translateZ(6px) rotateX(1deg);
            border-color: rgba(137, 223, 255, .42);
            box-shadow: 0 30px 80px rgba(0,0,0,.46), 0 0 34px rgba(42,170,235,.09), inset 0 1px 0 rgba(255,255,255,.1);
        }
        [data-testid="stDataFrame"]:hover {
            transform:perspective(1000px) translateY(-4px) translateZ(8px);
            border-color:rgba(127,255,225,.42);
            box-shadow:0 30px 78px rgba(0,0,0,.45),0 0 34px rgba(61,231,177,.1),inset 0 1px 0 rgba(255,255,255,.08);
        }
        [data-testid="stPlotlyChart"]:hover {
            transform:none !important;
            border-color:rgba(127,255,225,.42);
            filter:none;
            box-shadow:0 20px 52px rgba(0,0,0,.38),0 0 22px rgba(61,231,177,.07),inset 0 1px 0 rgba(255,255,255,.08);
        }
        [data-testid="stExpander"]:hover, [data-testid="stAlert"]:hover, .ai-guide > div:hover, .ai-stage:hover, .demo-strip:hover {
            transform:perspective(700px) translateY(-2px) translateZ(5px);
            border-color:rgba(127,255,225,.32) !important;
            box-shadow:0 18px 42px rgba(0,0,0,.3),0 0 24px rgba(61,231,177,.07);
        }
        .hero-pill:hover, .filter-pill:hover, .trust-pill:hover {
            transform:translateY(-3px) scale(1.025);
            border-color:rgba(127,255,225,.4);
            background:rgba(67,207,161,.16);
            box-shadow:0 9px 22px rgba(0,0,0,.22),0 0 18px rgba(61,231,177,.08);
        }
        .viz-feature:hover {
            transform: perspective(900px) translateY(-4px) translateZ(10px) rotateX(2deg);
            border-color: rgba(132,255,214,.38);
            box-shadow: 0 25px 58px rgba(0,0,0,.35), 0 0 30px rgba(61,231,177,.08), inset 0 1px 0 rgba(255,255,255,.08);
        }
        .kpi-card:hover {
            transform:perspective(900px) translateY(-5px) translateZ(11px) rotateX(2deg);
            border-color:rgba(132,255,214,.45);
            box-shadow:0 30px 82px rgba(0,0,0,.46),0 0 35px rgba(61,231,177,.1),inset 0 1px 0 rgba(255,255,255,.1);
        }
        .kpi-card:hover .kpi-value { text-shadow:0 0 22px rgba(127,255,225,.22); }
        .kpi-card:hover .kpi-scan, .viz-feature:hover::before { animation:hoverScan .85s ease-out both; }
        .kpi-card:hover .kpi-meter i, .viz-feature:hover .telemetry-rail i { animation:hoverCharge .8s ease-in-out both; }
    }
    @supports not ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {
        [data-testid="stHeader"], .app-hero, .hero-pill { background-color: #0a2034; }
        .mode-card, .answer-card, [data-testid="stMetric"], .kpi-card { background-color: #0b2237; }
    }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; scroll-behavior:auto !important; } }
    @media (forced-colors: active) {
        .app-hero, .mode-card, .answer-card, .kpi-card, .viz-feature, [data-testid="stMetric"], [data-testid="stPlotlyChart"] { border: 1px solid CanvasText; }
        .status-dot { background: Highlight; box-shadow: none; }
        .telemetry-rail, .kpi-meter { border:1px solid CanvasText; background:Canvas; }
        .telemetry-rail i, .kpi-meter i { background:Highlight; box-shadow:none; }
    }
    @media (max-width: 1200px) {
        .block-container { max-width: 100%; padding-left: 1rem; padding-right: 1rem; }
        .app-title { font-size: clamp(1.9rem, 4.4vw, 3rem); }
        .st-key-top_navigation [role="radiogroup"] { grid-template-columns:repeat(3,minmax(0,1fr)); }
    }
    @media (max-width: 900px) {
        .stApp { background-attachment:scroll; }
        .stApp::before, .app-hero::before { animation:none !important; filter:blur(12px); }
        [data-testid="stHeader"], .st-key-top_navigation, .agent-launcher { -webkit-backdrop-filter:none; backdrop-filter:none; }
        .block-container { padding: .85rem .75rem 3rem; }
        .st-key-top_navigation { position:relative; top:auto; border-radius:15px; padding:.48rem; }
        .st-key-top_navigation > div { gap:.15rem; }
        .top-nav-label { display:none; }
        .st-key-top_navigation [role="radiogroup"] { grid-template-columns:repeat(3,minmax(0,1fr)); gap:.4rem !important; overflow:visible !important; }
        .st-key-top_navigation [role="radiogroup"] label { min-height:54px; }
        .st-key-top_navigation [role="radiogroup"] label p { font-size:.86rem; }
        .app-hero { padding: 1.3rem; border-radius: 23px; }
        .app-hero::after { display: none; }
        [data-testid="stMetric"] { min-height: 105px; border-radius: 18px; }
        .kpi-card { min-height:122px; border-radius:18px; }
        .section-shell { padding: 1rem; }
        [data-testid="stTabs"] [role="tablist"] { border-radius: 16px; }
        [data-testid="stTabs"] button[role="tab"] { min-width: max-content; }
        [data-testid="stButtonGroup"] [role="radiogroup"] { grid-template-columns:repeat(3,minmax(0,1fr)); }
        .ai-guide { grid-template-columns: 1fr; }
        .ai-pipeline { grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); }
        .ai-response-empty { min-height: 300px; }
        .capability-note { margin-left:.2rem; margin-right:.2rem; }
        .viz-ribbon { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .st-key-animation_workspace { padding:.58rem; border-radius:18px; }
        .st-key-animation_workspace [data-testid="stPlotlyChart"] { min-height:600px; }
        .agent-task-receipt { grid-template-columns:repeat(3,minmax(0,1fr)); }
    }
    @media (max-width: 640px) {
        .block-container { padding-left: .55rem; padding-right: .55rem; }
        .st-key-top_navigation [role="radiogroup"] { grid-template-columns:repeat(2,minmax(0,1fr)); }
        .st-key-top_navigation [role="radiogroup"] label { min-height:52px; padding:.58rem .45rem; }
        .st-key-top_navigation [role="radiogroup"] label p { font-size:.82rem; }
        [data-testid="stButtonGroup"] [role="radiogroup"] { grid-template-columns:repeat(2,minmax(0,1fr)); }
        [data-testid="stButtonGroup"] button[role="radio"] { padding:.45rem .35rem; font-size:.8rem; }
        .app-hero { padding: 1.15rem; border-radius: 20px; }
        .app-title { font-size: clamp(1.85rem, 10vw, 2.55rem); line-height: 1.05; overflow-wrap: anywhere; }
        .app-subtitle { font-size: .9rem; }
        .hero-pill { font-size: .7rem; padding: .36rem .6rem; }
        .mode-card { grid-template-columns: 1fr; }
        .mode-orb { width: 42px; height: 42px; }
        .answer-card { padding: 1rem; border-radius: 20px; }
        .response-heading { align-items:flex-start; }
        .ai-chat-bubble { max-width:calc(100% - 2.65rem); }
        .ai-chat-assistant { grid-template-columns:1.9rem minmax(0,1fr); gap:.65rem; }
        .ai-chat-avatar { width:1.9rem; height:1.9rem; border-radius:10px; }
        .ai-pipeline { grid-template-columns: 1fr; }
        [data-testid="stDataFrame"], [data-testid="stPlotlyChart"] { border-radius: 18px; }
        .stButton > button, .stDownloadButton > button { width: 100%; min-height: 46px; }
        .viz-ribbon { grid-template-columns: 1fr; }
        .st-key-exploration_workspace > [data-testid="stLayoutWrapper"]:has(h2#data-exploration) > [data-testid="stVerticalBlock"] { padding:.68rem .75rem !important; }
        .st-key-animation_workspace [data-testid="stHorizontalBlock"] { gap:.35rem !important; }
        .animation-header strong { font-size:.92rem; }
        .animation-header small { font-size:.7rem; }
        .st-key-animation_workspace [data-testid="stPlotlyChart"] { min-height:570px; }
        .agent-launcher { right:.72rem; bottom:.72rem; min-width:58px; width:58px; height:58px; padding:.48rem; border-radius:18px; }
        .agent-launcher-copy { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }
        .agent-launcher-status { left:42px; top:5px; }
        .agent-task-receipt { grid-template-columns:repeat(2,minmax(0,1fr)); }
        .kpi-card { min-height:116px; padding:.9rem; }
        .kpi-value { font-size:clamp(1.55rem,8vw,2rem); }
    }

    /* v1.14 Midnight Analytics theme
       Reference direction: near-black financial dashboard, cyan data light,
       restrained depth, compact controls, and repaint-safe interaction. */
    :root {
        --canvas: #03070b;
        --canvas-soft: #070d13;
        --panel: rgba(8, 15, 21, .94);
        --panel-strong: rgba(10, 18, 25, .98);
        --panel-soft: rgba(16, 29, 38, .78);
        --text: #f4f8fb;
        --muted: #9aabb7;
        --cyan: #70ddff;
        --cyan-soft: #c7f3ff;
        --blue: #4cbfe8;
        --teal: #70ddff;
        --green: #72e3bd;
        --amber: #f2c96d;
        --danger: #ff7d91;
        --line: rgba(139, 202, 225, .17);
        --line-bright: rgba(112, 221, 255, .48);
        --glass-shadow: 0 18px 48px rgba(0, 0, 0, .38), inset 0 1px 0 rgba(255, 255, 255, .045);
    }

    ::selection { color:#021017; background:#70ddff; }
    .stApp {
        background:
            radial-gradient(ellipse at 84% -10%, rgba(87, 202, 236, .20), transparent 29rem),
            radial-gradient(ellipse at 12% 88%, rgba(30, 105, 133, .10), transparent 34rem),
            linear-gradient(145deg, #020508 0%, #050b10 54%, #03070b 100%);
    }
    .stApp::before {
        inset:0 0 auto 0;
        height:31rem;
        opacity:.55;
        filter:none;
        transform:none;
        background:
            linear-gradient(165deg, transparent 0 57%, rgba(96, 212, 244, .045) 57.2% 57.55%, transparent 57.8%),
            radial-gradient(circle at 86% 5%, rgba(120, 225, 255, .16), transparent 23rem);
    }
    .stApp::after {
        inset:auto 0 0;
        height:18rem;
        opacity:.17;
        clip-path:none;
        filter:none;
        background-image:
            linear-gradient(rgba(112,221,255,.055) 1px, transparent 1px),
            linear-gradient(90deg, rgba(112,221,255,.055) 1px, transparent 1px);
        background-size:32px 32px;
        mask-image:linear-gradient(to top, #000, transparent 84%);
    }
    [data-testid="stHeader"] {
        background:rgba(3,7,11,.96);
        border-bottom:1px solid rgba(112,221,255,.08);
    }
    [data-testid="stToolbar"] { color:#a5b9c6; }
    .block-container { max-width:1540px; }
    h1, h2, h3 { letter-spacing:-.035em; }
    a { color:#86e4ff; }
    a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible, [tabindex]:focus-visible {
        outline:3px solid #8be5ff !important;
        outline-offset:3px !important;
    }

    /* App rail and filters */
    [data-testid="stSidebar"] {
        background:linear-gradient(180deg,#03080c 0%,#060d12 100%);
        border-right:1px solid rgba(112,221,255,.14);
        box-shadow:18px 0 46px rgba(0,0,0,.24);
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:#8499a6 !important; }
    [data-testid="stSidebar"] hr { border-color:rgba(112,221,255,.11) !important; }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border-color:rgba(112,221,255,.18) !important;
        background:linear-gradient(145deg,rgba(11,22,29,.98),rgba(6,14,20,.99)) !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 12px 30px rgba(0,0,0,.2);
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:rgba(112,221,255,.055); }
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div,
    [data-testid="stDateInput"] > div > div,
    [data-testid="stFileUploaderDropzone"] {
        background:#081119 !important;
        border-color:rgba(125,190,214,.22) !important;
        border-radius:13px !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.035);
    }
    input::placeholder, textarea::placeholder { color:#8196a5 !important; }
    [data-baseweb="popover"], [data-baseweb="menu"] { background:#09131b !important; }
    [role="option"] { color:#e8f3f8 !important; }
    [role="option"]:hover { background:rgba(112,221,255,.12) !important; }
    [data-testid="stSlider"] [role="slider"] { background:#70ddff !important; box-shadow:0 0 14px rgba(112,221,255,.42); }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"][data-rac] {
        border-color:rgba(112,221,255,.19) !important;
        color:#eef9fc !important;
        background:#071018 !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.03);
    }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [role="group"][data-rac][data-focus-within="true"] {
        border-color:rgba(112,221,255,.68) !important;
        background:#0a1720 !important;
        box-shadow:0 0 0 3px rgba(112,221,255,.11);
    }
    [data-testid="stSidebar"] [data-tag] {
        color:#021017 !important;
        border-color:rgba(199,243,255,.45) !important;
        background:linear-gradient(120deg,#68d8fb,#a3ebff) !important;
        box-shadow:0 5px 14px rgba(65,183,221,.18),inset 0 1px 0 rgba(255,255,255,.48);
    }
    [data-testid="stSidebar"] [data-tag] > span,
    [data-testid="stSidebar"] [data-tag] button { color:#021017 !important; }
    [data-testid="stMultiSelectDropdown"] {
        border-color:rgba(112,221,255,.26) !important;
        color:#eef9fc !important;
        background:#08131b !important;
        box-shadow:0 22px 55px rgba(0,0,0,.52),0 0 24px rgba(77,195,233,.07) !important;
    }
    [data-testid="stMultiSelectDropdown"] [role="option"] { color:#e4f3f8 !important; }
    [data-testid="stMultiSelectDropdown"] [role="option"]:hover,
    [data-testid="stMultiSelectDropdown"] [role="option"][data-focused="true"] { background:rgba(112,221,255,.12) !important; }
    [data-testid="stMultiSelectDropdown"] [role="option"][aria-selected="true"] { color:#bfefff !important; background:rgba(70,173,207,.17) !important; }

    /* Controls use dark pills; cyan is reserved for selected/primary actions. */
    .stButton > button, .stDownloadButton > button, [data-testid="stBaseButton-secondary"] {
        border-color:rgba(129,185,205,.25) !important;
        color:#e8f3f8 !important;
        background:linear-gradient(145deg,#111b23,#0b141b) !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.055),0 8px 20px rgba(0,0,0,.20);
    }
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stBaseButton-secondary"]:hover {
        color:#f7fcff !important;
        border-color:rgba(112,221,255,.62) !important;
        background:linear-gradient(145deg,#152630,#0c1b24) !important;
        box-shadow:0 11px 26px rgba(0,0,0,.24),0 0 18px rgba(86,202,238,.08);
    }
    [data-testid^="stBaseButton-primary"] {
        border-color:#8be5ff !important;
        color:#031118 !important;
        background:linear-gradient(120deg,#67d7f8,#a1ebff) !important;
        box-shadow:0 10px 26px rgba(70,188,226,.20),inset 0 1px 0 rgba(255,255,255,.55) !important;
    }
    [data-testid^="stBaseButton-primary"] p,
    [data-testid^="stBaseButton-primary"] span,
    [data-testid^="stBaseButton-primary"] svg { color:#031118 !important; }
    [data-testid^="stBaseButton-primary"]:hover {
        border-color:#c7f3ff !important;
        background:linear-gradient(120deg,#85e3ff,#c7f3ff) !important;
        box-shadow:0 14px 30px rgba(70,188,226,.25),inset 0 1px 0 rgba(255,255,255,.65) !important;
    }
    [data-testid^="stBaseButton-primary"]:hover p,
    [data-testid^="stBaseButton-primary"]:hover span,
    [data-testid^="stBaseButton-primary"]:hover svg { color:#031118 !important; }

    /* Reference-inspired workspace header and navigation */
    .sidebar-home-link:hover { border-color:rgba(112,221,255,.32); background:rgba(112,221,255,.055); }
    .sidebar-mark { border-color:rgba(112,221,255,.34); background:linear-gradient(145deg,#0c2530,#07131a); box-shadow:0 0 22px rgba(112,221,255,.11); }
    .sidebar-title { font-size:1.12rem; letter-spacing:-.025em; }
    .sidebar-subtitle { color:#839aa8; }
    .sidebar-live { color:#92a8b5; }
    .status-dot { background:#70ddff; box-shadow:0 0 0 4px rgba(112,221,255,.10),0 0 13px rgba(112,221,255,.60); }
    .st-key-top_navigation {
        background:linear-gradient(145deg,rgba(8,15,21,.98),rgba(5,11,16,.98));
        border-color:rgba(112,221,255,.15);
        box-shadow:0 16px 42px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.04);
    }
    .top-nav-label { color:#8fdff8; }
    .st-key-top_navigation [role="radiogroup"] label {
        border-color:transparent;
        color:#a6b6c0;
        background:transparent;
    }
    .st-key-top_navigation [role="radiogroup"] label:hover {
        border-color:rgba(112,221,255,.17);
        background:#0e1921;
        box-shadow:none;
    }
    .st-key-top_navigation [role="radiogroup"] label[data-selected="true"] {
        border-color:rgba(112,221,255,.44);
        background:linear-gradient(145deg,#18252d,#0f1b22);
        box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 0 18px rgba(112,221,255,.08);
    }
    .st-key-top_navigation [role="radiogroup"] label p { color:#b3c1ca; }
    .st-key-top_navigation [role="radiogroup"] label[data-selected="true"] p { color:#f6fbfd; }
    .st-key-top_navigation [role="radiogroup"] label p::before { color:#70ddff; }

    .app-hero {
        border-color:rgba(112,221,255,.18);
        border-radius:24px;
        background:
            linear-gradient(155deg,rgba(10,18,24,.98) 0 64%,rgba(12,37,47,.94) 100%),
            #071018;
        box-shadow:0 22px 58px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.045);
    }
    .app-hero::before {
        opacity:.74;
        filter:none;
        background:radial-gradient(ellipse at 85% 15%,rgba(112,221,255,.20),transparent 19rem);
        transform:none;
    }
    .app-hero::after {
        opacity:.2;
        background:linear-gradient(90deg,transparent,rgba(112,221,255,.65),transparent);
        clip-path:none;
        height:1px;
        top:auto;
        bottom:0;
    }
    .app-eyebrow,.section-kicker,.answer-eyebrow,.animation-header span { color:#78defd; }
    .stApp h1.app-title { color:#f7fbfd; font-size:clamp(2rem,4.1vw,3.2rem) !important; letter-spacing:-.055em; }
    .app-subtitle { color:#a7b8c3; max-width:880px; }
    .hero-pill,.trust-pill,.filter-pill {
        border-color:rgba(126,190,214,.22);
        color:#dce9ef;
        background:#0b151c;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.035);
    }
    .hero-terrain { display:none; }
    .section-shell,
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stMetric"],
    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"],
    [data-testid="stJson"],
    .kpi-card,.viz-feature,.answer-card,.mode-card,.ai-response-empty,.empty-state {
        border-color:rgba(130,190,212,.17);
        background:linear-gradient(145deg,rgba(10,18,24,.96),rgba(6,12,17,.97));
        box-shadow:var(--glass-shadow);
    }
    [data-testid="stMetric"]::after { background:rgba(112,221,255,.12); }
    [data-testid="stMetricLabel"],.kpi-label { color:#a3b4bf; }
    [data-testid="stMetricValue"],.kpi-value { color:#f7fbfd; }
    .section-title { color:#f7fbfd; }
    .section-description { color:#94a8b5; }
    .viz-feature span { color:#91a7b3; }
    .telemetry-rail,.kpi-meter { background:#111c23; border-color:rgba(112,221,255,.13); }
    .telemetry-rail i,.kpi-meter i { background:linear-gradient(90deg,#2b91b4,#70ddff 72%,#d2f6ff); }
    .telemetry-rail i::after,.kpi-meter i::after { background:#effcff; box-shadow:0 0 10px #70ddff,0 0 18px rgba(112,221,255,.55); }
    .kpi-card::before { background:linear-gradient(90deg,transparent,rgba(112,221,255,.45),transparent); }
    .kpi-card::after { background:rgba(112,221,255,.09); }
    .kpi-delta { color:#afc0ca; background:rgba(113,140,153,.12); }
    .kpi-card.positive .kpi-delta { color:#aaf3d6; background:rgba(44,157,117,.18); }
    .kpi-card.negative .kpi-delta { color:#ffd0d8; background:rgba(185,69,86,.19); }
    [data-testid="stButtonGroup"] [role="radiogroup"],
    [data-testid="stTabs"] [role="tablist"] { border-color:rgba(112,221,255,.15); background:#081219; }
    [data-testid="stButtonGroup"] button[role="radio"] { border-color:rgba(112,221,255,.08); color:#9eb1bd; background:#0b151c; }
    [data-testid="stButtonGroup"] button[role="radio"]:hover { border-color:rgba(112,221,255,.30); background:#10202a; }
    [data-testid="stButtonGroup"] button[role="radio"][aria-checked="true"],
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color:#f6fbfd;
        border-color:rgba(112,221,255,.43);
        background:linear-gradient(145deg,#18303c,#10212a);
        box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 7px 18px rgba(0,0,0,.22);
    }
    [data-testid="stTabs"] button[role="tab"] { color:#96a9b5; }
    [data-testid="stExpander"],[data-testid="stStatusWidget"],[data-testid="stAlert"] { border-color:rgba(126,190,214,.18) !important; background:#09131a !important; }
    [data-testid="stAlert"] p { color:#dfeaf0 !important; }
    .demo-strip { border-color:rgba(236,195,89,.22); color:#efdfae; background:rgba(110,88,30,.18); }
    .scope-note { color:#8499a6; }

    /* AI workspace and floating assistant */
    .mode-card,.answer-card { border-color:rgba(112,221,255,.17); }
    .mode-orb,.ai-chat-avatar,.ai-stage span,.agent-task-receipt i {
        color:#031118;
        background:linear-gradient(145deg,#6bd9fa,#a6edff);
        box-shadow:0 0 22px rgba(112,221,255,.17);
    }
    .mode-card span,.answer-card p,.ai-guide small,.ai-stage small { color:#9fb1bc; }
    .mode-meta b { color:#bceeff; border-color:rgba(112,221,255,.18); background:rgba(112,221,255,.065); }
    .answer-eyebrow,.ai-chat-label { color:#76ddfc; }
    .ai-chat-bubble { border-color:rgba(112,221,255,.16); background:#0b151c; }
    .ai-chat-bubble p { color:#eaf3f7; }
    .ai-guide > div,.ai-stage { background:linear-gradient(145deg,#0e1b23,#09131a); border-color:rgba(112,221,255,.13); }
    .ai-response-empty { background:radial-gradient(circle at 50% 38%,rgba(112,221,255,.075),transparent 13rem),#071018; }
    .ai-response-empty span,.empty-icon { color:#70ddff; filter:drop-shadow(0 0 14px rgba(112,221,255,.32)); }
    .empty-hint { color:#c2effc; border-color:rgba(112,221,255,.18); background:rgba(67,157,188,.08); }
    .agent-launcher {
        border-color:rgba(112,221,255,.34);
        background:linear-gradient(145deg,rgba(15,28,36,.98),rgba(7,15,21,.99));
        box-shadow:0 16px 44px rgba(0,0,0,.48),0 0 24px rgba(112,221,255,.10),inset 0 1px 0 rgba(255,255,255,.07);
    }
    .agent-launcher:hover { border-color:rgba(112,221,255,.70); background:linear-gradient(145deg,#152a35,#0a1820); }
    .agent-launcher-icon { color:#031118; background:linear-gradient(145deg,#70ddff,#b7f1ff); }
    .agent-launcher-copy strong { color:#f4fafc; }
    .agent-launcher-copy small { color:#94aab6; }
    .agent-launcher-status { border-color:#071018; background:#70ddff; }

    /* Repaint-safe hover depth: no blur, filter, parallax, or perpetual motion. */
    @media (hover:hover) and (pointer:fine) {
        [data-testid="stMetric"]:hover,.mode-card:hover,.answer-card:hover,.ai-response-empty:hover,
        [data-testid="stDataFrame"]:hover,.viz-feature:hover,.kpi-card:hover {
            border-color:rgba(112,221,255,.40);
            box-shadow:0 24px 58px rgba(0,0,0,.42),0 0 22px rgba(112,221,255,.065),inset 0 1px 0 rgba(255,255,255,.075);
        }
        [data-testid="stPlotlyChart"]:hover { border-color:rgba(112,221,255,.36); box-shadow:0 20px 48px rgba(0,0,0,.36),0 0 18px rgba(112,221,255,.05); }
        .hero-pill:hover,.filter-pill:hover,.trust-pill:hover { border-color:rgba(112,221,255,.36); background:#10212a; }
    }
    @media (max-width:900px) {
        .stApp::after { background-size:24px 24px; }
        .app-hero { border-radius:20px; }
        .stApp h1.app-title { font-size:clamp(2rem,5.2vw,2.55rem) !important; }
    }
    @media (max-width:640px) {
        .stApp { background:linear-gradient(145deg,#020508,#050b10 62%,#03070b); }
        .stApp::before,.stApp::after { opacity:.10; }
        .app-hero { border-radius:18px; }
        .stApp h1.app-title { font-size:clamp(2rem,9.2vw,2.35rem) !important; letter-spacing:-.045em; }
    }
    @media (forced-colors:active) {
        .agent-launcher,.st-key-top_navigation,[data-testid="stSidebar"] [data-testid="stExpander"] { border:1px solid CanvasText; }
    }
</style>
"""


def inject_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)
    st.markdown('<a class="skip-link" href="#main-content">Skip to main content</a>', unsafe_allow_html=True)


def render_agent_launcher(*, active: bool = False) -> None:
    """Render an always-visible, keyboard-accessible shortcut to the AI agent."""
    href = "#ai-task-composer" if active else "?assistant=1"
    label = "Jump to the AI task composer" if active else "Open the AI analytics agent"
    state_class = " active" if active else ""
    icon = (
        '<svg viewBox="0 0 24 24" aria-hidden="true">'
        '<path d="M5 17.5 3.5 21l4.2-1.6A9 9 0 1 0 5 17.5Z"/>'
        '<path d="M8 11h.01M12 11h.01M16 11h.01"/>'
        "</svg>"
    )
    st.markdown(
        f'<a class="agent-launcher{state_class}" href="{href}" target="_self" aria-label="{label}" title="{label}">'
        f'<span class="agent-launcher-icon">{icon}</span><span class="agent-launcher-status" aria-hidden="true"></span>'
        '<span class="agent-launcher-copy"><strong>Ask the AI agent</strong><small>Give me an analytics task</small></span></a>',
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.sidebar.markdown(
        f"""<div class="sidebar-brand"><a class="sidebar-home-link" href="?home=1" target="_self" aria-label="Go to Overview home" title="Go to Overview"><div class="sidebar-mark">{inline_brand_icon('sidebar-brand-icon')}</div><div><div class="sidebar-title">E-Commerce Analytics</div><div class="sidebar-subtitle">Secure intelligence workspace</div></div></a><div class="sidebar-live"><span class="status-dot"></span> Analytics engine online</div></div>""",
        unsafe_allow_html=True,
    )


def render_top_navigation(pages: list[str]) -> str:
    """Render the primary workspace navigation above the analytical canvas."""
    friendly_labels = {
        "Overview": "Overview",
        "Data Exploration": "Explore data",
        "AI Assistant": "Ask AI",
        "Advanced Analytics": "Advanced",
        "Data Quality & Performance": "Quality & speed",
        "Report Export": "Export reports",
    }
    with st.container(key="top_navigation"):
        st.markdown('<span class="top-nav-label">Workspace</span>', unsafe_allow_html=True)
        return st.radio(
            "Workspace navigation",
            pages,
            key="current_section",
            horizontal=True,
            format_func=lambda item: friendly_labels.get(item, item),
            label_visibility="collapsed",
        )


def render_app_header(
    bundle: DatasetBundle,
    active_rows: int,
    settings: Settings,
    pipeline: NLQueryPipeline,
    *,
    compact: bool = False,
) -> None:
    source = "Demo dataset" if bundle.metadata.is_demo else "Uploaded dataset"
    readiness = "Presentation ready" if bundle.metadata.official_demo_ready else "Development mode"
    st.markdown(
        f"""<section id="main-content" tabindex="-1" class="app-hero{' compact' if compact else ''}" aria-label="Application summary"><div class="hero-terrain" aria-hidden="true"></div><div class="app-eyebrow">AI decision intelligence</div><h1 class="app-title">{escape(settings.app_name)}</h1><p class="app-subtitle">Turn raw transactions into interactive evidence. Explore the business, ask questions in natural language, validate every query, and export decision-ready findings.</p><div class="hero-pills"><span class="hero-pill"><span class="status-dot"></span>{escape(pipeline.mode_label)} · {escape(pipeline.model_label)}</span><span class="hero-pill">{source}</span><span class="hero-pill">{active_rows:,} active rows</span><span class="hero-pill">{bundle.metadata.columns} source columns</span><span class="hero-pill">{readiness}</span></div></section>""",
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


def render_build_marker(release: str) -> None:
    """Expose a subtle, machine-verifiable production release marker."""
    safe_release = escape(release)
    st.markdown(
        f'<footer class="build-marker" data-app-version="{safe_release}" aria-label="Application build {safe_release}">Build {safe_release} · Public analytics workspace</footer>',
        unsafe_allow_html=True,
    )


def render_section_intro(kicker: str, title: str, description: str) -> None:
    with st.container(border=True):
        st.markdown(f'<div class="section-kicker">{escape(kicker)}</div>', unsafe_allow_html=True)
        st.header(title)
        st.caption(description)
