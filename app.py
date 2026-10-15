"""
FinTrack – Green Finance Dashboard
Streamlit application: Dashboard · Transactions · Budgets · Goals ·
Analytics · Reports · Settings — all powered by MongoDB Atlas.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date, timezone

from database.transactions import (
    add_transaction, get_transactions, update_transaction, delete_transaction,
    add_goal, get_goals, seed_sample_data_if_empty,
)
from database.connection import client as _db_client, db as _db, check_connection
from database.budgets import set_or_update_budget, get_all_budgets, delete_budget
from database.savings_goals import (
    add_savings_goal, get_all_savings_goals,
    update_goal_progress, delete_savings_goal,
)
from database.analytics import get_total_spent_by_category_for_month
from ai.insights import generate_ai_financial_insights, chat_with_finance_ai

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FINTRACK | Green Finance Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── Chrome / header / decoration (Remove all top viewport gap) ── */
#MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* ── App background (Matching Screenshot: Soft Mint Gradient across all pages) ── */
.stApp,
[data-testid="stAppViewContainer"],
section.main {
    background: linear-gradient(135deg, #d8eee2 0%, #e4f2eb 100%) !important;
}

/* Target the main content container and remove default top padding */
.block-container,
.main .block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
    max-width: 100% !important;
}

/* ── Card columns (row-level) ─────────────────────────────────────────────── */
/* Target top-level columns in the main area (supports both stColumn and column) */
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    background-color: #f6fbf8 !important;
    border: 1.5px solid #b8d8c8 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 6px rgba(15, 81, 50, 0.05) !important;
    padding: 14px 16px !important;
}

/* Prevent nested columns inside cards from getting duplicate outer borders/background */
div[data-testid="stColumn"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
div[data-testid="column"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Standalone forms across pages */
[data-testid="stForm"] {
    background-color: #f6fbf8 !important;
    border: 1.5px solid #b8d8c8 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 6px rgba(15, 81, 50, 0.05) !important;
    padding: 16px 20px !important;
}

/* ── SIDEBAR & PERMANENT LOCK (Pure White Background & Mint Border) ──────── */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
    min-width: 230px !important;
    max-width: 230px !important;
    transform: none !important;
    visibility: visible !important;
    background-color: #ffffff !important;
    border-right: 1px solid #d0e4da !important;
}

/* Remove all sidebar header, collapse button, and top gap */
[data-testid="stSidebarHeader"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[kind="header"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Pull left sidebar higher up toward the top of viewport */
[data-testid="stSidebar"] > div:first-child,
section[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"],
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] .block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin-top: 0 !important;
    height: 100% !important;
}

/* Sidebar flex container spanning full viewport height */
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: calc(100vh - 12px) !important;
    height: calc(100vh - 12px) !important;
    justify-content: flex-start !important;
    box-sizing: border-box !important;
}

/* 1. Logo with exact 2px gap from top */
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:first-child {
    padding-top: 2px !important;
    margin-top: 0 !important;
    margin-bottom: 2px !important;
}

/* 2. Middle elements: navigation radio menu */
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:nth-child(2) {
    margin-top: 2px !important;
    margin-bottom: auto !important;
}

/* 3. Last small card pushed down to the very bottom */
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:last-child {
    margin-top: auto !important;
    margin-bottom: 12px !important;
    padding-bottom: 0 !important;
}

/* ── NAVIGATION STYLING (MATCHING REFERENCE DESIGN) ───────────────────────── */
[data-testid="stSidebar"] [data-testid="stRadio"] > label,
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-testid="stWidgetLabel"] {
    display: none !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"],
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
    padding: 0 10px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    border-radius: 10px !important;
    padding: 8px 14px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    margin: 0 !important;
    background: transparent !important;
    box-sizing: border-box !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
    display: none !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label input[type="radio"],
[data-testid="stSidebar"] [data-testid="stRadio"] label span[role="radio"],
[data-testid="stSidebar"] [data-testid="stRadio"] label div[role="radio"] {
    display: none !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
    position: absolute !important;
    pointer-events: none !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label::before,
[data-testid="stSidebar"] [data-testid="stRadio"] label::after {
    display: none !important;
    content: none !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label > div:last-child {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #334155 !important;
    margin: 0 !important;
    line-height: 1.4 !important;
    letter-spacing: -0.1px !important;
    transition: color 0.15s ease !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #f0fdf4 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover p {
    color: #16a34a !important;
    font-weight: 600 !important;
}

/* Active / Selected item state: soft green pill with dark green text */
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background-color: #cde8d9 !important;
    border-radius: 10px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
    color: #0f5132 !important;
    font-weight: 700 !important;
}

/* ── QUICK ACTIONS BUTTON STYLES ─────────────────────────────────────────── */
div.st-key-qa_add > button {
    background: #dcfce7 !important;
    border: 1.5px solid #86efac !important;
    color: #15803d !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 10px 8px !important;
    height: 64px !important;
}
div.st-key-qa_budget > button {
    background: #e0f2fe !important;
    border: 1.5px solid #7dd3fc !important;
    color: #0284c7 !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 10px 8px !important;
    height: 64px !important;
}
div.st-key-qa_goal > button {
    background: #f3e8ff !important;
    border: 1.5px solid #d8b4fe !important;
    color: #7e22ce !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 10px 8px !important;
    height: 64px !important;
}
div.st-key-qa_reports > button {
    background: #ffe4e6 !important;
    border: 1.5px solid #fecdd3 !important;
    color: #be123c !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 10px 8px !important;
    height: 64px !important;
}

div.st-key-btn_view_all > button {
    background: transparent !important;
    border: none !important;
    color: #0284c7 !important;
    font-weight: 600 !important;
    font-size: 12.5px !important;
    padding: 0 !important;
    margin: 0 !important;
    box-shadow: none !important;
    min-height: unset !important;
}

/* ── BUTTONS ─────────────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.18s ease !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; }
button[kind="primary"] {
    background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%) !important;
    color: white !important;
    border: none !important;
}

/* ── FORM ELEMENTS ───────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
    border-radius: 10px !important;
    border: 1.5px solid #b8d8c8 !important;
    background: #ffffff !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-baseweb="select"] > div {
    border-radius: 10px !important;
    border: 1.5px solid #b8d8c8 !important;
    background: #ffffff !important;
}

/* ── ALERTS ──────────────────────────────────────────────────────────────── */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 12px !important;
    border: 1.5px solid #b8d8c8 !important;
}

/* ── DATAFRAME ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1.5px solid #b8d8c8 !important;
    background: #ffffff !important;
}

/* ── DIVIDER ─────────────────────────────────────────────────────────────── */
hr { border-color: #b8d8c8 !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

NAV_OPTIONS = [
    "🏠 Dashboard",
    "📋 Transactions",
    "🕒 Budgets",
    "🎯 Goals",
    "📊 Analytics",
    "📄 Reports",
    "🤖 AI Assistant",
    "👤 Profile",
    "⚙️ Settings",
]

CATEGORY_EMOJIS = {
    "Food": "🍔", "Shopping": "🛒", "Transport": "🚌",
    "Bills & Utilities": "💡", "Entertainment": "🎬",
    "Salary": "💰", "Freelance": "💻", "Business": "🏢",
    "Investment": "📈", "Others": "📦", "Other": "📦",
}

CATEGORY_COLORS = {
    "Food": "#4ade80", "Shopping": "#818cf8", "Transport": "#60a5fa",
    "Bills & Utilities": "#fb923c", "Entertainment": "#facc15",
    "Others": "#a78bfa", "Other": "#a78bfa",
    "Salary": "#34d399", "Freelance": "#38bdf8",
    "Business": "#f472b6", "Investment": "#c084fc",
}

BAR_COLORS = ["#22c55e", "#818cf8", "#60a5fa", "#fb923c", "#facc15"]

EXPENSE_CATS = ["Food", "Shopping", "Transport", "Bills & Utilities", "Entertainment", "Others"]
INCOME_CATS  = ["Salary", "Freelance", "Business", "Investment", "Others"]

MONTHS_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


# ── HELPERS ───────────────────────────────────────────────────────────────────

def fmt_inr(amount):
    try:
        return f"₹{amount:,.0f}"
    except Exception:
        return f"₹{amount}"

def cat_emoji(cat):
    return CATEGORY_EMOJIS.get(cat, "💳")

def cat_color(cat):
    return CATEGORY_COLORS.get(cat, "#94a3b8")

def month_label(dt):
    try:
        return dt.strftime("%b")
    except Exception:
        return "?"

def month_num(dt):
    try:
        return dt.month
    except Exception:
        return 0


def compute_month_delta(txns, txn_type, ref_dt=None):
    """
    Compute the percentage change in total `txn_type` ('income'/'expense'/'savings')
    between the current calendar month and the previous calendar month.

    Returns a tuple (delta_pct: float | None, direction: str).
    `delta_pct` is None when there is no prior-month data (avoids misleading numbers).
    `direction` is '+' for increase, '-' for decrease, or '' when N/A.
    """
    if ref_dt is None:
        ref_dt = datetime.now()

    cur_year, cur_month = ref_dt.year, ref_dt.month
    if cur_month == 1:
        prev_year, prev_month = cur_year - 1, 12
    else:
        prev_year, prev_month = cur_year, cur_month - 1

    def total_for(year, month, t_type):
        total = 0.0
        for t in txns:
            dt = t.get("date")
            if dt is None:
                continue
            try:
                ty, tm = dt.year, dt.month
            except AttributeError:
                continue
            if ty == year and tm == month:
                if t_type in ("income", "expense"):
                    if t.get("type") == t_type:
                        total += t.get("amount", 0)
                elif t_type == "savings":
                    if t.get("type") == "income":
                        total += t.get("amount", 0)
                    elif t.get("type") == "expense":
                        total -= t.get("amount", 0)
        return total

    cur_val  = total_for(cur_year,  cur_month,  txn_type)
    prev_val = total_for(prev_year, prev_month, txn_type)

    if prev_val == 0:
        return None, ""

    delta_pct = ((cur_val - prev_val) / abs(prev_val)) * 100
    direction = "+" if delta_pct >= 0 else "-"
    return abs(delta_pct), direction


def render_delta_badge(delta_pct, direction, color_up="#16a34a", color_down="#dc2626"):
    """Return an HTML snippet for the month-over-month delta badge, or empty string if N/A."""
    if delta_pct is None:
        return '<p style="font-size:11px;color:#94a3b8;margin:3px 0 0;font-weight:500;">vs. last month: N/A</p>'
    arrow   = "▲" if direction == "+" else "▼"
    color   = color_up if direction == "+" else color_down
    label   = "vs. last month"
    return (f'<p style="font-size:11px;color:{color};margin:3px 0 0;font-weight:600;">'
            f'{arrow} {direction}{delta_pct:.1f}% {label}</p>')


# ── DATA LOADING (CACHED) ─────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_txns():
    try:
        return get_transactions()
    except Exception as e:
        st.error(f"DB error loading transactions: {e}")
        return []

@st.cache_data(ttl=30)
def load_goals_data():
    try:
        return get_goals()
    except Exception as e:
        st.error(f"DB error loading goals: {e}")
        return []

@st.cache_data(ttl=30)
def load_budgets_data():
    try:
        return get_all_budgets()
    except Exception as e:
        st.error(f"DB error loading budgets: {e}")
        return []

@st.cache_data(ttl=30)
def load_savings_goals_data():
    try:
        return get_all_savings_goals()
    except Exception as e:
        st.error(f"DB error loading savings goals: {e}")
        return []

def refresh():
    load_txns.clear()
    load_goals_data.clear()
    load_budgets_data.clear()
    load_savings_goals_data.clear()


# ── NAVIGATION SESSION STATE ──────────────────────────────────────────────────

if "nav_radio" not in st.session_state:
    st.session_state["nav_radio"] = NAV_OPTIONS[0]

if st.session_state.get("pending_nav"):
    st.session_state["nav_radio"] = st.session_state.pop("pending_nav")


# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Branding (Logo 2px from top, headings in middle)
    st.markdown("""<div style="margin-top:0px;padding:2px 10px 8px;text-align:center;border-bottom:1px solid #e8f5e9;margin-bottom:6px;">
<div style="display:flex;justify-content:center;margin-top:0px;margin-bottom:0px;">
<svg width="74" height="74" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
<ellipse cx="50" cy="86" rx="34" ry="6" fill="#e2e8f0" opacity="0.6"/>
<path d="M28 85 C32 79, 68 79, 72 85 C68 89, 32 89, 28 85 Z" fill="#8c7853" opacity="0.9"/>
<path d="M25 76 C25 79.5, 43 79.5, 43 76 L43 80.5 C43 84, 25 84, 25 80.5 Z" fill="#d97706" stroke="#0f5132" stroke-width="1.2"/>
<ellipse cx="34" cy="76" rx="9" ry="3.6" fill="#facc15" stroke="#0f5132" stroke-width="1.2"/>
<path d="M25 70.5 C25 74, 43 74, 43 70.5 L43 75 C43 78.5, 25 78.5, 25 75 Z" fill="#d97706" stroke="#0f5132" stroke-width="1.2"/>
<ellipse cx="34" cy="70.5" rx="9" ry="3.6" fill="#fde047" stroke="#0f5132" stroke-width="1.2"/>
<ellipse cx="34" cy="70.5" rx="6.5" ry="2.4" fill="none" stroke="#eab308" stroke-width="0.8"/>
<path d="M43 74.5 C43 78, 63 78, 63 74.5 L63 79 C63 82.5, 43 82.5, 43 79 Z" fill="#d97706" stroke="#0f5132" stroke-width="1.2"/>
<ellipse cx="53" cy="74.5" rx="10" ry="3.8" fill="#facc15" stroke="#0f5132" stroke-width="1.2"/>
<path d="M43 68.5 C43 72, 63 72, 63 68.5 L63 73 C63 76.5, 43 76.5, 43 73 Z" fill="#d97706" stroke="#0f5132" stroke-width="1.2"/>
<ellipse cx="53" cy="68.5" rx="10" ry="3.8" fill="#facc15" stroke="#0f5132" stroke-width="1.2"/>
<path d="M43 62.5 C43 66, 63 66, 63 62.5 L63 67 C63 70.5, 43 70.5, 43 67 Z" fill="#d97706" stroke="#0f5132" stroke-width="1.2"/>
<ellipse cx="53" cy="62.5" rx="10" ry="3.8" fill="#fde047" stroke="#0f5132" stroke-width="1.2"/>
<ellipse cx="53" cy="62.5" rx="7.5" ry="2.6" fill="none" stroke="#ca8a04" stroke-width="0.9"/>
<path d="M44 66 Q46 44 48 28" fill="none" stroke="#16a34a" stroke-width="3.6" stroke-linecap="round"/>
<path d="M45 46 C34 42, 23 46, 25 54 C31 59, 42 54, 45 48 Z" fill="#4ade80" stroke="#0f5132" stroke-width="1.2"/>
<path d="M47 32 C41 18, 20 17, 19 30 C21 43, 40 40, 47 34 Z" fill="#22c55e" stroke="#0f5132" stroke-width="1.3"/>
<path d="M47 33 Q33 28 23 29" fill="none" stroke="#15803d" stroke-width="1" stroke-linecap="round"/>
<path d="M47 33 C55 22, 77 19, 79 32 C77 45, 56 42, 47 36 Z" fill="#16a34a" stroke="#0f5132" stroke-width="1.3"/>
<path d="M47 35 Q61 30 73 31" fill="none" stroke="#14532d" stroke-width="1" stroke-linecap="round"/>
</svg>
</div>
<div style="font-size:1.6rem;font-weight:800;color:#0b4f2f;letter-spacing:0.5px;margin-top:3px;line-height:1.1;">FINTRACK</div>
<div style="font-size:0.76rem;font-weight:500;color:#334155;margin-top:3px;margin-bottom:2px;">Track Today, Build Tomorrow</div>
</div>""", unsafe_allow_html=True)

    selected = st.radio(
        "nav",
        NAV_OPTIONS,
        key="nav_radio",
        label_visibility="collapsed",
    )

    # Bottom motivational card (pinned down at the bottom)
    st.markdown("""
    <div style="background:linear-gradient(180deg, #e4f4ec 0%, #ccead9 100%);border-radius:14px;padding:12px 10px 0px;margin:8px 10px 6px;text-align:center;border:1.5px solid #b8d8c8;box-shadow:0 2px 6px rgba(15,81,50,0.05);overflow:hidden;position:relative;">
        <div style="display:flex;justify-content:center;margin-bottom:6px;">
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
                <ellipse cx="16" cy="26" rx="7" ry="2.5" fill="#ca8a04"/>
                <path d="M16 25 Q16 17 16 11" stroke="#16a34a" stroke-width="2.2" stroke-linecap="round"/>
                <path d="M16 16 C12 12, 5 13, 7 19 C10 21, 15 19, 16 17 Z" fill="#22c55e"/>
                <path d="M16 13 C20 8, 27 9, 25 15 C22 17, 18 15, 16 14 Z" fill="#4ade80"/>
            </svg>
        </div>
        <p style="font-size:12px;color:#1e293b;font-weight:600;margin:0 0 10px;line-height:1.4;">
            Small steps today,<br>bigger dreams tomorrow!
        </p>
        <svg width="100%" height="32" viewBox="0 0 160 32" fill="none" preserveAspectRatio="none" style="display:block;">
            <path d="M0 32 C30 18, 60 26, 90 20 C120 14, 140 24, 160 18 L160 32 Z" fill="#a7f3d0" opacity="0.8"/>
            <path d="M0 32 C40 24, 80 16, 120 22 C140 25, 150 20, 160 25 L160 32 Z" fill="#34d399" opacity="0.6"/>
            <path d="M78 28 Q80 18 82 12" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M82 12 C78 9, 72 10, 74 15 C76 17, 80 15, 82 13 Z" fill="#15803d"/>
            <path d="M82 12 C86 9, 92 10, 90 15 C88 17, 84 15, 82 13 Z" fill="#22c55e"/>
        </svg>
    </div>
    """, unsafe_allow_html=True)


# ── QUICK-NAV HELPER ──────────────────────────────────────────────────────────

def set_nav(page_name):
    st.session_state["pending_nav"] = page_name

def go_to(page_name):
    st.session_state["pending_nav"] = page_name
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def render_dashboard():
    txns  = load_txns()
    goals = load_goals_data()


    # ── Hero Banner ───────────────────────────────────────────────────────────
    st.markdown("""<div style="border-radius:14px;background:#f6fbf8;border:1.5px solid #b8d8c8;box-shadow:0 2px 6px rgba(15,81,50,0.05);padding:14px 24px;position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
<div style="display:flex;align-items:center;">
<div style="width:44px;height:44px;border-radius:50%;background:#e2f5ea;display:flex;align-items:center;justify-content:center;margin-right:16px;flex-shrink:0;">
<svg width="26" height="26" viewBox="0 0 32 32" fill="none">
<ellipse cx="16" cy="25" rx="6" ry="2.2" fill="#facc15" stroke="#ca8a04" stroke-width="1"/>
<path d="M16 24 Q16 17 16 12" stroke="#16a34a" stroke-width="2" stroke-linecap="round"/>
<path d="M16 16 C12 12, 6 13, 8 18 C11 20, 15 18, 16 17 Z" fill="#22c55e"/>
<path d="M16 14 C19 9, 26 10, 24 16 C21 18, 17 16, 16 15 Z" fill="#4ade80"/>
</svg>
</div>
<div>
<div style="font-size:1.75rem;font-weight:800;color:#0f2942;line-height:1.2;margin:0;">Welcome to FINTRACK <span style="font-size:1.55rem;vertical-align:middle;">💚</span></div>
<div style="font-size:0.95rem;font-weight:400;color:#5a6e7f;margin-top:4px;">Track your income, expenses and goals — all in one place.</div>
</div>
</div>
<div style="flex-shrink:0;margin-left:16px;">
<svg width="340" height="95" viewBox="0 0 340 95" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M0 95 Q60 62, 130 68 T260 72 Q300 66, 340 74 L340 95 Z" fill="#d1fae5" opacity="0.6"/>
<path d="M0 95 Q80 72, 170 80 T340 84 L340 95 Z" fill="#a7f3d0" opacity="0.75"/>
<path d="M0 95 Q110 82, 220 84 T340 87 L340 95 Z" fill="#86efac" opacity="0.5"/>
<path d="M40 87 Q40 78 40 74" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round"/>
<path d="M40 78 C35 74, 29 76, 31 80 C34 82, 39 80, 40 79 Z" fill="#22c55e"/>
<path d="M40 76 C44 72, 50 73, 49 78 C46 80, 41 78, 40 77 Z" fill="#4ade80"/>
<path d="M85 89 Q85 82 85 78" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round"/>
<path d="M85 82 C81 79, 76 80, 78 84 C80 86, 84 84, 85 83 Z" fill="#16a34a"/>
<path d="M85 80 C89 77, 94 78, 93 82 C91 84, 86 82, 85 81 Z" fill="#22c55e"/>
<rect x="150" y="65" width="13" height="26" rx="3" fill="#86efac"/>
<rect x="171" y="50" width="13" height="41" rx="3" fill="#4ade80"/>
<rect x="192" y="35" width="13" height="56" rx="3" fill="#22c55e"/>
<rect x="213" y="20" width="13" height="71" rx="3" fill="#16a34a"/>
<path d="M140 68 L160 56 L181 60 L202 42 L223 18" fill="none" stroke="#f97316" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
<polygon points="223,18 214,19 220,26" fill="#f97316"/>
<path d="M265 92 Q265 52 268 18" fill="none" stroke="#15803d" stroke-width="2.5" stroke-linecap="round"/>
<path d="M265 74 C255 70, 244 76, 247 82 C254 84, 263 79, 265 76 Z" fill="#16a34a"/>
<path d="M265 71 C275 67, 286 73, 284 79 C277 81, 268 76, 265 73 Z" fill="#22c55e"/>
<path d="M266 52 C254 47, 245 54, 248 60 C255 62, 264 57, 266 54 Z" fill="#22c55e"/>
<path d="M267 48 C278 43, 288 49, 286 55 C279 57, 270 52, 267 49 Z" fill="#4ade80"/>
<path d="M267 31 C257 25, 250 32, 253 38 C259 40, 266 35, 267 33 Z" fill="#22c55e"/>
<path d="M268 28 C278 22, 287 27, 285 33 C279 35, 271 31, 268 29 Z" fill="#4ade80"/>
<path d="M268 18 C265 10, 274 4, 277 11 C278 15, 272 18, 268 18 Z" fill="#22c55e"/>
</svg>
</div>
</div>""", unsafe_allow_html=True)

    if len(txns) == 0:
        c_seed, _ = st.columns([1, 4])
        with c_seed:
            if st.button("🌱 Load Sample Data", type="primary", use_container_width=True):
                with st.spinner("Seeding realistic 6-month data…"):
                    seeded = seed_sample_data_if_empty()
                refresh()
                if seeded:
                    st.success("Sample data loaded!")
                    st.rerun()
                else:
                    st.info("Data already exists.")

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    total_income   = sum(t["amount"] for t in txns if t.get("type") == "income")
    total_expenses = sum(t["amount"] for t in txns if t.get("type") == "expense")
    total_savings  = total_income - total_expenses
    total_goals    = len(goals)
    active_goals   = sum(1 for g in goals if not g.get("completed", False))
    goal_pct       = int((total_goals - active_goals) / total_goals * 100) if total_goals else 0

    # Compute dynamic month-over-month deltas from actual transaction data
    inc_delta,  inc_dir  = compute_month_delta(txns, "income")
    exp_delta,  exp_dir  = compute_month_delta(txns, "expense")
    sav_delta,  sav_dir  = compute_month_delta(txns, "savings")

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        inc_badge = render_delta_badge(inc_delta, inc_dir, color_up="#16a34a", color_down="#dc2626")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="width:46px;height:46px;border-radius:12px;background:#dcfce7;
                      display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/>
              <path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>
            </svg>
          </div>
          <div style="flex:1;min-width:0;">
            <p style="font-size:12px;color:#64748b;margin:0;font-weight:600;">Total Income</p>
            <h3 style="font-size:20px;font-weight:800;color:#0f5132;margin:2px 0 0;line-height:1.1;">{fmt_inr(total_income)}</h3>
            {inc_badge}
          </div>
        </div>""", unsafe_allow_html=True)

    with k2:
        exp_badge = render_delta_badge(exp_delta, exp_dir, color_up="#dc2626", color_down="#16a34a")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="width:46px;height:46px;border-radius:12px;background:#fee2e2;
                      display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="5" width="20" height="14" rx="2"/>
              <line x1="2" y1="10" x2="22" y2="10"/>
            </svg>
          </div>
          <div style="flex:1;min-width:0;">
            <p style="font-size:12px;color:#64748b;margin:0;font-weight:600;">Total Expenses</p>
            <h3 style="font-size:20px;font-weight:800;color:#dc2626;margin:2px 0 0;line-height:1.1;">{fmt_inr(total_expenses)}</h3>
            {exp_badge}
          </div>
        </div>""", unsafe_allow_html=True)

    with k3:
        sav_badge = render_delta_badge(sav_delta, sav_dir, color_up="#16a34a", color_down="#dc2626")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="width:46px;height:46px;border-radius:12px;background:#dbeafe;
                      display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 12a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z"/>
              <path d="M12 9v6m-3-3h6"/>
            </svg>
          </div>
          <div style="flex:1;min-width:0;">
            <p style="font-size:12px;color:#64748b;margin:0;font-weight:600;">Total Savings</p>
            <h3 style="font-size:20px;font-weight:800;color:#0284c7;margin:2px 0 0;line-height:1.1;">{fmt_inr(total_savings)}</h3>
            {sav_badge}
          </div>
        </div>""", unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="width:46px;height:46px;border-radius:12px;background:#f3e8ff;
                      display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#7e22ce" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <circle cx="12" cy="12" r="6"/>
              <circle cx="12" cy="12" r="2"/>
            </svg>
          </div>
          <div style="flex:1;min-width:0;">
            <p style="font-size:12px;color:#64748b;margin:0;font-weight:600;">Active Goals</p>
            <h3 style="font-size:20px;font-weight:800;color:#1e293b;margin:2px 0 4px;line-height:1.1;">{active_goals} / {total_goals}</h3>
            <div style="display:flex;align-items:center;gap:8px;">
              <div style="background:#ede9fe;border-radius:6px;height:6px;flex:1;overflow:hidden;">
                <div style="background:#7c3aed;height:100%;border-radius:6px;width:{goal_pct}%;"></div>
              </div>
              <span style="font-size:11px;font-weight:600;color:#64748b;">{goal_pct}%</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ── Row 2: Bar Chart | Donut Chart | Recent Transactions ─────────────────
    r2a, r2b, r2c = st.columns([1.3, 1.3, 1.1])

    # ── Income vs Expenses Bar Chart ─────────────────────────────────────────
    with r2a:
        st.markdown('<h4 style="font-size:16px;font-weight:700;color:#1e293b;margin:0 0 10px;">Income vs Expenses</h4>', unsafe_allow_html=True)
        if txns:
            df = pd.DataFrame(txns)
            df["m_num"]  = df["date"].apply(month_num)
            df["m_lbl"]  = df["date"].apply(month_label)
            agg = df.groupby(["m_num", "m_lbl", "type"])["amount"].sum().reset_index()
            months_sorted = sorted(df["m_num"].unique())
            inc_map = agg[agg["type"] == "income"].set_index("m_num")["amount"].to_dict()
            exp_map = agg[agg["type"] == "expense"].set_index("m_num")["amount"].to_dict()
            lbls = [MONTHS_ORDER[m - 1] for m in months_sorted]
            inc_v = [inc_map.get(m, 0) for m in months_sorted]
            exp_v = [exp_map.get(m, 0) for m in months_sorted]

            fig = go.Figure()
            fig.add_trace(go.Bar(name="Income",   x=lbls, y=inc_v, marker_color="#22c55e", marker_cornerradius=4))
            fig.add_trace(go.Bar(name="Expenses", x=lbls, y=exp_v, marker_color="#f87171", marker_cornerradius=4))
            fig.update_layout(
                barmode="group", height=262,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=1.15, x=1, xanchor="right", font=dict(size=12)),
                margin=dict(l=0, r=0, t=28, b=0),
                yaxis=dict(gridcolor="#e2e8f0", gridwidth=1, tickfont=dict(size=11)),
                xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=11)),
                bargap=0.22, bargroupgap=0.06,
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<p style="color:#9ca3af;text-align:center;padding:70px 0;font-size:13px;">No data yet — click "Load Sample Data".</p>', unsafe_allow_html=True)

    # ── Expense Breakdown Donut ───────────────────────────────────────────────
    with r2b:
        st.markdown('<h4 style="font-size:16px;font-weight:700;color:#1e293b;margin:0 0 10px;">Expense Breakdown</h4>', unsafe_allow_html=True)
        exp_txns = [t for t in txns if t.get("type") == "expense"]
        if exp_txns:
            cat_totals: dict[str, float] = {}
            for t in exp_txns:
                c = t.get("category", "Others")
                cat_totals[c] = cat_totals.get(c, 0) + t["amount"]

            cats   = list(cat_totals.keys())
            vals   = list(cat_totals.values())
            # Palette matching screenshot
            PALETTE = ["#0ea5e9", "#f97316", "#eab308", "#a855f7", "#c084fc", "#38bdf8"]
            colors = [PALETTE[i % len(PALETTE)] for i in range(len(cats))]
            total_exp = sum(vals)

            fig2 = go.Figure(go.Pie(
                labels=cats, values=vals, hole=0.62,
                marker=dict(colors=colors, line=dict(color="white", width=2)),
                textinfo="percent", textfont=dict(size=11),
                showlegend=True,
            ))
            fig2.add_annotation(
                text=f"<b>{fmt_inr(total_exp)}</b><br><span style='font-size:10px;color:#6b7280'>Total Expenses</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="#1e293b"),
            )
            fig2.update_layout(
                height=285,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=10),
                legend=dict(orientation="v", x=0.78, y=0.5, yanchor="middle", font=dict(size=11)),
                font=dict(family="Inter"),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<p style="color:#9ca3af;text-align:center;padding:70px 0;font-size:13px;">No expense data yet.</p>', unsafe_allow_html=True)

    # ── Recent Transactions ───────────────────────────────────────────────────
    with r2c:
        hd, vw = st.columns([3, 1])
        with hd:
            st.markdown('<h4 style="font-size:16px;font-weight:700;color:#1e293b;margin:0 0 6px;">Recent Transactions</h4>', unsafe_allow_html=True)
        with vw:
            if st.button("View All", key="btn_view_all", on_click=set_nav, args=("📋 Transactions",)):
                go_to("📋 Transactions")

        recent = txns[:5]
        if recent:
            rows = ""
            for t in recent:
                c      = t.get("category", "Others")
                emoji  = cat_emoji(c)
                bg     = cat_color(c) + "22"
                sign   = "−" if t.get("type") == "expense" else "+"
                ac     = "#dc2626" if t.get("type") == "expense" else "#16a34a"
                title  = (t.get("title") or "Transaction")[:22]
                try:
                    ds = t["date"].strftime("%b %d, %Y")
                except Exception:
                    ds = "—"
                amt_str = f"{sign} {fmt_inr(t['amount'])}"
                rows += f"""
                <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #eef3f0;">
                  <div style="width:34px;height:34px;border-radius:10px;background:{bg};
                              display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">{emoji}</div>
                  <div style="flex:1;min-width:0;">
                    <p style="font-size:13px;font-weight:600;color:#1e293b;margin:0;
                               white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{title}</p>
                    <p style="font-size:11px;color:#94a3b8;margin:1px 0 0;">{ds}</p>
                  </div>
                  <span style="font-size:13px;font-weight:700;color:{ac};white-space:nowrap;">{amt_str}</span>
                </div>"""
            st.markdown(rows, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#9ca3af;text-align:center;padding:30px 0;font-size:13px;">No transactions yet.</p>', unsafe_allow_html=True)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ── Row 3: Trend Line | Top Categories | Quick Actions ───────────────────
    r3a, r3b, r3c = st.columns([1.3, 1.3, 1.1])

    # ── Monthly Spending Trend ────────────────────────────────────────────────
    with r3a:
        st.markdown("""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <h4 style="font-size:16px;font-weight:700;color:#1e293b;margin:0;">Monthly Spending Trend</h4>
          <span style="background:#ffffff;border:1px solid #b8d8c8;border-radius:8px;padding:3px 10px;font-size:11.5px;color:#475569;font-weight:500;">This Year ▾</span>
        </div>
        """, unsafe_allow_html=True)
        exp_list = [t for t in txns if t.get("type") == "expense"]
        if exp_list:
            df_e = pd.DataFrame(exp_list)
            df_e["m_num"] = df_e["date"].apply(month_num)
            df_e["m_lbl"] = df_e["date"].apply(month_label)
            m_agg = df_e.groupby(["m_num", "m_lbl"])["amount"].sum().reset_index().sort_values("m_num")

            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=m_agg["m_lbl"].tolist(), y=m_agg["amount"].tolist(),
                mode="lines+markers",
                line=dict(color="#16a34a", width=2.5, shape="spline"),
                marker=dict(size=7, color="#16a34a", line=dict(color="white", width=2)),
                fill="tozeroy", fillcolor="rgba(22,163,74,0.12)",
            ))
            fig3.update_layout(
                height=232,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(gridcolor="#e2e8f0", gridwidth=1, tickfont=dict(size=11)),
                xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=11)),
                showlegend=False, font=dict(family="Inter"),
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<p style="color:#9ca3af;text-align:center;padding:50px 0;font-size:13px;">No expense data yet.</p>', unsafe_allow_html=True)

    # ── Top Spending Categories ───────────────────────────────────────────────
    with r3b:
        st.markdown('<h4 style="font-size:16px;font-weight:700;color:#1e293b;margin:0 0 14px;">Top Spending Categories</h4>', unsafe_allow_html=True)
        exp_list2 = [t for t in txns if t.get("type") == "expense"]
        if exp_list2:
            cat_map: dict[str, float] = {}
            for t in exp_list2:
                c = t.get("category", "Others")
                cat_map[c] = cat_map.get(c, 0) + t["amount"]
            top5 = sorted(cat_map.items(), key=lambda x: x[1], reverse=True)[:5]
            max_v = top5[0][1] if top5 else 1
            BAR_PALETTE = ["#16a34a", "#6366f1", "#0284c7", "#ea580c", "#ca8a04"]
            bars_html = ""
            for i, (cat, amt) in enumerate(top5):
                pct   = int(amt / max_v * 100)
                color = BAR_PALETTE[i % len(BAR_PALETTE)]
                bars_html += f"""
                <div style="margin-bottom:12px;">
                  <div style="display:flex;justify-content:space-between;font-size:13px;
                               font-weight:500;color:#374151;margin-bottom:5px;">
                    <span>{cat}</span>
                    <span style="color:#1e293b;font-weight:700;">{fmt_inr(amt)}</span>
                  </div>
                  <div style="background:#eef3f0;border-radius:6px;height:7px;overflow:hidden;">
                    <div style="background:{color};height:100%;border-radius:6px;width:{pct}%;"></div>
                  </div>
                </div>"""
            st.markdown(bars_html, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#9ca3af;text-align:center;padding:50px 0;font-size:13px;">No expense data yet.</p>', unsafe_allow_html=True)

    # ── Quick Actions ─────────────────────────────────────────────────────────
    with r3c:
        st.markdown('<h4 style="font-size:16px;font-weight:700;color:#1e293b;margin:0 0 14px;">Quick Actions</h4>', unsafe_allow_html=True)

        qa1, qa2 = st.columns(2)
        with qa1:
            if st.button("➕\nAdd Transaction", key="qa_add", use_container_width=True, on_click=set_nav, args=("📋 Transactions",)):
                go_to("📋 Transactions")
        with qa2:
            if st.button("🎯\nSet Budget", key="qa_budget", use_container_width=True, on_click=set_nav, args=("🕒 Budgets",)):
                go_to("🕒 Budgets")

        qa3, qa4 = st.columns(2)
        with qa3:
            if st.button("📈\nCreate Goal", key="qa_goal", use_container_width=True, on_click=set_nav, args=("🎯 Goals",)):
                go_to("🎯 Goals")
        with qa4:
            if st.button("📄\nView Reports", key="qa_reports", use_container_width=True, on_click=set_nav, args=("📄 Reports",)):
                go_to("📄 Reports")

    # ── AI Insights Card ──────────────────────────────────────────────────────────
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color:#f6fbf8;border:1.5px solid #b8d8c8;border-radius:16px;
                 padding:18px 22px;box-shadow:0 2px 8px rgba(15,81,50,0.07);">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
        <div style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#d1fae5,#a7f3d0);
                     display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;"></div>
        <div>
          <p style="font-size:16px;font-weight:800;color:#0f5132;margin:0;line-height:1.2;">&#x1F916; FINTRACK AI Spending Insights</p>
          <p style="font-size:12px;color:#64748b;margin:2px 0 0;">Powered by Llama 3.3 · Your live MongoDB data</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    ai_col, btn_col = st.columns([4, 1])
    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        gen_btn = st.button("✨ Generate New Insights", key="dash_gen_insights", use_container_width=True, type="primary")

    with ai_col:
        # Auto-generate on first load; regenerate if button pressed
        if gen_btn or "ai_insights_cache" not in st.session_state:
            with st.spinner("🤖 Analyzing your finances with AI…"):
                insight_text = generate_ai_financial_insights(force_refresh=True)
        else:
            insight_text = st.session_state.get("ai_insights_cache", "")

        if insight_text:
            # Render each bullet as a styled block
            lines = [l.strip() for l in insight_text.split("\n") if l.strip()]
            bullets_html = ""
            for line in lines:
                if line.startswith(("*", "-", "•")) or (len(line) > 1 and line[0] in "💡📊⚠✅🎯💰✔📉📈ℹ🔍💡⛏✨📌"):
                    clean = line.lstrip("*-• ")
                    bullets_html += f"""
                    <div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;
                                 border-bottom:1px solid #e8f5e9;">
                      <div style="width:7px;height:7px;border-radius:50%;background:#16a34a;
                                   margin-top:7px;flex-shrink:0;"></div>
                      <p style="font-size:13.5px;color:#1e293b;margin:0;line-height:1.6;">{clean}</p>
                    </div>"""
                else:
                    bullets_html += f'<p style="font-size:13.5px;color:#374151;margin:6px 0;">{line}</p>'
            st.markdown(
                f'<div style="background:#f6fbf8;border-radius:12px;padding:14px 18px;'
                f'border:1.5px solid #b8d8c8;margin-top:6px;">{bullets_html}</div>',
                unsafe_allow_html=True,
            )
        if st.button("🤖 Open AI Chat Assistant", key="dash_open_ai", on_click=set_nav, args=("🤖 AI Assistant",)):
            go_to("🤖 AI Assistant")


# ══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════════

def render_transactions():
    st.markdown('<h2 style="font-size:22px;font-weight:800;color:#0f5132;margin-bottom:4px;">📋 Transactions</h2>', unsafe_allow_html=True)

    all_txns = load_txns()

    # ── ➕ Add New Transaction (expander at top) ───────────────────────────────
    with st.expander("➕ Add New Transaction", expanded=False):
        with st.form("add_txn_form", clear_on_submit=True):
            a1, a2, a3 = st.columns(3)
            with a1:
                title    = st.text_input("Title *", placeholder="e.g. Grocery Shopping")
            with a2:
                amount   = st.number_input("Amount (₹) *", min_value=0.01, step=1.0, format="%.2f")
            with a3:
                txn_type = st.selectbox("Type *", ["expense", "income"])
            a4, a5, a6 = st.columns(3)
            with a4:
                cats     = EXPENSE_CATS if txn_type == "expense" else INCOME_CATS
                category = st.selectbox("Category *", cats)
            with a5:
                txn_date = st.date_input("Date *", value=date.today())
            with a6:
                notes = st.text_input("Notes", placeholder="Optional…")
            saved = st.form_submit_button("💾 Save Transaction", type="primary", use_container_width=True)
            if saved:
                try:
                    add_transaction(
                        title=title, amount=amount,
                        transaction_type=txn_type, category=category,
                        notes=notes, date=txn_date,
                    )
                    refresh()
                    st.success("✅ Transaction saved!")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {e}")
                except Exception as e:
                    st.error(f"❌ Database error: {e}")

    # ── Filter Bar ────────────────────────────────────────────────────────────
    st.markdown('<p style="font-size:14px;font-weight:700;color:#1e293b;margin:10px 0 6px;">🔍 Filter Transactions</p>', unsafe_allow_html=True)
    with st.form("filter_form", clear_on_submit=False):
        f1, f2, f3, f4, f5 = st.columns([1.1, 1.1, 1.2, 1.5, 0.8])
        with f1:
            start_date = st.date_input("Start Date", value=None, key="flt_start")
        with f2:
            end_date   = st.date_input("End Date",   value=None, key="flt_end")
        with f3:
            all_cats   = ["All"] + sorted(set(t.get("category", "") for t in all_txns if t.get("category")))
            flt_cat    = st.selectbox("Category", all_cats, key="flt_cat")
        with f4:
            flt_type   = st.radio("Type", ["All", "Income", "Expense"], horizontal=True, key="flt_type")
        with f5:
            st.markdown("<br>", unsafe_allow_html=True)
            apply_btn  = st.form_submit_button("Apply", use_container_width=True)

    search_q = st.text_input("🔎 Search by title", placeholder="Type to search…", key="flt_search", label_visibility="collapsed")

    # Apply filters
    filtered = list(all_txns)
    if start_date:
        filtered = [t for t in filtered if hasattr(t.get("date"), "date") and t["date"].date() >= start_date]
    if end_date:
        filtered = [t for t in filtered if hasattr(t.get("date"), "date") and t["date"].date() <= end_date]
    if flt_cat != "All":
        filtered = [t for t in filtered if t.get("category") == flt_cat]
    if flt_type != "All":
        filtered = [t for t in filtered if t.get("type", "").lower() == flt_type.lower()]
    if search_q:
        sq = search_q.lower()
        filtered = [t for t in filtered if sq in (t.get("title") or "").lower()]

    # ── Action row: stats + CSV download ─────────────────────────────────────
    ac1, ac2, ac3 = st.columns([2, 2, 1])
    with ac1:
        total_shown = sum(t["amount"] for t in filtered)
        st.markdown(
            f'<p style="font-size:13px;color:#475569;margin:2px 0;">'
            f'Showing <b>{len(filtered)}</b> of <b>{len(all_txns)}</b> transactions &nbsp;|&nbsp; '
            f'Total: <b style="color:#0f5132;">{fmt_inr(total_shown)}</b></p>',
            unsafe_allow_html=True,
        )
    with ac3:
        if filtered:
            csv_rows = []
            for t in filtered:
                try:
                    ds = t["date"].strftime("%Y-%m-%d")
                except Exception:
                    ds = ""
                csv_rows.append({
                    "Date":     ds,
                    "Title":    t.get("title", ""),
                    "Type":     t.get("type", ""),
                    "Category": t.get("category", ""),
                    "Amount":   t.get("amount", 0),
                    "Notes":    t.get("notes", ""),
                })
            csv_bytes = pd.DataFrame(csv_rows).to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 CSV",
                data=csv_bytes,
                file_name=f"fintrack_txns_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # ── Transactions Table ────────────────────────────────────────────────────
    if filtered:
        rows = []
        for t in filtered:
            try:
                ds = t["date"].strftime("%b %d, %Y")
            except Exception:
                ds = "—"
            sign = "−" if t.get("type") == "expense" else "+"
            rows.append({
                "Date":     ds,
                "Title":    t.get("title", ""),
                "Category": f"{cat_emoji(t.get('category',''))} {t.get('category','')}",
                "Type":     t.get("type", "").capitalize(),
                "Amount":   f"{sign}₹{t.get('amount', 0):,.0f}",
                "_id":      str(t["_id"]),
            })
        df_show = pd.DataFrame(rows)
        st.dataframe(df_show.drop(columns=["_id"]), use_container_width=True, height=300, hide_index=True)

        # ── Update / Delete ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<p style="font-size:14px;font-weight:700;color:#1e293b;margin-bottom:8px;">✏️ Update or Delete</p>', unsafe_allow_html=True)

        ids    = [str(t["_id"]) for t in filtered]
        labels = []
        for t in filtered:
            try:
                ds2 = t["date"].strftime("%b %d")
            except Exception:
                ds2 = ""
            labels.append(f"{t.get('title', 'Unknown')} ({ds2})")

        uc1, uc2 = st.columns(2)
        with uc1:
            sel_label = st.selectbox("Select Transaction", labels, key="sel_txn")
            sel_idx   = labels.index(sel_label)
            sel_id    = ids[sel_idx]
            sel_txn   = filtered[sel_idx]
            new_amt   = st.number_input(
                "New Amount (₹)", min_value=0.01, step=1.0,
                value=float(sel_txn["amount"]), key="new_amt",
            )
            if st.button("💾 Update Amount", use_container_width=True):
                try:
                    cnt = update_transaction(sel_id, new_amt)
                    refresh()
                    st.success("✅ Updated!" if cnt else "No changes made.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

        with uc2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#f6fbf8;border-radius:10px;padding:12px 14px;margin-bottom:10px;
                        border:1.5px solid #b8d8c8;">
              <p style="font-size:12px;color:#6b7280;margin:0 0 4px;">Selected</p>
              <p style="font-size:14px;font-weight:600;color:#1e293b;margin:0;">{sel_txn.get('title','')}</p>
              <p style="font-size:13px;color:#374151;margin:4px 0 0;">
                {cat_emoji(sel_txn.get('category',''))} {sel_txn.get('category','')} &nbsp;·&nbsp;
                <span style="color:{'#dc2626' if sel_txn.get('type')=='expense' else '#15803d'};font-weight:700;">
                  {fmt_inr(sel_txn['amount'])}
                </span>
              </p>
            </div>""", unsafe_allow_html=True)
            if st.button("🗑️ Delete Transaction", use_container_width=True):
                try:
                    cnt = delete_transaction(sel_id)
                    refresh()
                    st.success("✅ Deleted!" if cnt else "Not found.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
    else:
        st.markdown('<p style="color:#9ca3af;text-align:center;padding:40px 0;font-size:13px;">No transactions match your filters.</p>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BUDGETS
# ══════════════════════════════════════════════════════════════════════════════

def render_budgets():
    st.markdown('<h2 style="font-size:22px;font-weight:800;color:#0f5132;margin-bottom:4px;">🕒 Budgets</h2>', unsafe_allow_html=True)

    now       = datetime.now()
    cur_year  = now.year
    cur_month = now.month

    # ── Set / Update Budget Form ───────────────────────────────────────────────
    with st.expander("➕ Set / Update a Budget Limit", expanded=False):
        with st.form("budget_form", clear_on_submit=True):
            bc1, bc2, bc3 = st.columns([2, 2, 1])
            with bc1:
                bcat  = st.selectbox("Category", EXPENSE_CATS, key="bcat_sel")
            with bc2:
                blimit = st.number_input("Monthly Limit (₹)", min_value=100.0, step=500.0, format="%.0f")
            with bc3:
                st.markdown("<br>", unsafe_allow_html=True)
                bsub  = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
            if bsub:
                try:
                    set_or_update_budget(bcat, blimit)
                    load_budgets_data.clear()
                    st.success(f"✅ Budget set for {bcat}: {fmt_inr(blimit)}/month")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

    # ── Load DB budgets + fallback defaults ───────────────────────────────────
    db_budgets = load_budgets_data()
    budget_map: dict[str, float] = {
        "Food": 12000, "Shopping": 8000, "Transport": 5000,
        "Bills & Utilities": 4000, "Entertainment": 4000, "Others": 5000,
    }
    for b in db_budgets:
        budget_map[b["category"]] = b["monthly_limit"]

    st.markdown(
        f'<p style="font-size:14px;color:#374151;margin:10px 0 14px;">'
        f'Current month spending vs. budget limits — <b>{now.strftime("%B %Y")}</b></p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    for i, (cat, budget) in enumerate(budget_map.items()):
        # Live spend from DB for current month
        try:
            spent = get_total_spent_by_category_for_month(cat, cur_year, cur_month)
        except Exception:
            spent = 0.0

        raw_pct  = (spent / budget * 100) if budget else 0
        bar_pct  = min(int(raw_pct), 100)
        remaining = max(budget - spent, 0)
        if raw_pct >= 100:
            bar_color = "#ef4444"
            status    = "⚠️ Over budget!"
            sc        = "#ef4444"
        elif raw_pct >= 80:
            bar_color = "#f97316"
            status    = f"{int(raw_pct)}% used — watch out"
            sc        = "#ea580c"
        else:
            bar_color = "#22c55e"
            status    = f"{int(raw_pct)}% used"
            sc        = "#16a34a"

        is_db  = cat in [b["category"] for b in db_budgets]
        badge  = (' <span style="background:#dbeafe;color:#1d4ed8;font-size:10px;'
                  'padding:1px 6px;border-radius:20px;">custom</span>' if is_db else "")

        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
            <div style="background-color:#f6fbf8;border-radius:14px;padding:14px 16px;margin-bottom:12px;
                         box-shadow:0 2px 6px rgba(15,81,50,0.05);border:1.5px solid #b8d8c8;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
                <span style="font-size:14px;font-weight:700;color:#1e293b;">{cat_emoji(cat)} {cat}{badge}</span>
                <span style="font-size:12px;color:{sc};font-weight:600;">{status}</span>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:12px;color:#6b7280;margin-bottom:8px;">
                <span>Spent: <b style="color:#1e293b;">{fmt_inr(spent)}</b></span>
                <span>Limit: <b style="color:#1e293b;">{fmt_inr(budget)}</b></span>
                <span>Left: <b style="color:#0f5132;">{fmt_inr(remaining)}</b></span>
              </div>
              <div style="background:#eef3f0;border-radius:6px;height:8px;overflow:hidden;">
                <div style="background:{bar_color};height:100%;border-radius:6px;width:{bar_pct}%;"></div>
              </div>
            </div>""", unsafe_allow_html=True)
            if is_db:
                if st.button(f"🗑️ Remove limit", key=f"del_budget_{cat}", use_container_width=True):
                    try:
                        delete_budget(cat)
                        load_budgets_data.clear()
                        st.success(f"Removed custom budget for {cat}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")


# ══════════════════════════════════════════════════════════════════════════════
# GOALS
# ══════════════════════════════════════════════════════════════════════════════

def render_goals():
    st.markdown('<h2 style="font-size:22px;font-weight:800;color:#0f5132;margin-bottom:4px;">🎯 Savings Goals</h2>', unsafe_allow_html=True)

    # ── Create New Goal (expander) ────────────────────────────────────────────
    with st.expander("➕ Create New Savings Goal", expanded=False):
        with st.form("add_goal_form", clear_on_submit=True):
            g1, g2, g3, g4 = st.columns([2, 1.5, 1.5, 1.5])
            with g1:
                g_name   = st.text_input("Goal Name *", placeholder="e.g. Family Vacation")
            with g2:
                g_target = st.number_input("Target Amount (₹) *", min_value=1.0, step=500.0)
            with g3:
                g_init   = st.number_input("Initial Deposit (₹)", min_value=0.0, step=500.0)
            with g4:
                g_date   = st.date_input("Target Date", value=None)
            gsub = st.form_submit_button("🎯 Create Goal", type="primary", use_container_width=True)
            if gsub:
                try:
                    add_savings_goal(
                        name=g_name,
                        target_amount=g_target,
                        current_amount=g_init,
                        target_date=g_date,
                    )
                    load_savings_goals_data.clear()
                    st.success("✅ Goal created!")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {e}")
                except Exception as e:
                    st.error(f"❌ {e}")

    # ── Goals Grid ────────────────────────────────────────────────────────────
    st.markdown('<p style="font-size:14px;font-weight:700;color:#1e293b;margin:10px 0 12px;">📊 Your Goals</p>', unsafe_allow_html=True)
    goals = load_savings_goals_data()

    if not goals:
        st.markdown('<p style="color:#9ca3af;text-align:center;padding:60px 0;font-size:13px;">No goals yet — create your first savings goal above! 👆</p>', unsafe_allow_html=True)
        return

    # Show goals in 2-column grid
    col_a, col_b = st.columns(2)
    for i, g in enumerate(goals):
        goal_id   = str(g["_id"])
        target    = g.get("target_amount", 1)
        current   = g.get("current_amount") or g.get("saved_amount") or 0
        remaining = max(target - current, 0)
        pct       = min(int(current / target * 100), 100) if target else 0
        completed = g.get("completed", False)
        badge     = ('<span style="background:#dcfce7;color:#15803d;font-size:11px;'
                     'padding:2px 8px;border-radius:20px;font-weight:700;">✅ Completed</span>'
                     if completed else
                     f'<span style="background:#dbeafe;color:#1d4ed8;font-size:11px;'
                     f'padding:2px 8px;border-radius:20px;font-weight:700;">{pct}% done</span>')
        bar_color = "#22c55e" if completed else "#7c3aed"

        tgt_date_str = ""
        if g.get("target_date"):
            try:
                tgt_date_str = f" &nbsp;·&nbsp; Target: {g['target_date'].strftime('%b %d, %Y')}"
            except Exception:
                pass

        target_col = col_a if i % 2 == 0 else col_b
        with target_col:
            st.markdown(f"""
            <div style="background-color:#f6fbf8;border-radius:14px;padding:16px 18px;
                         margin-bottom:6px;border:1.5px solid #b8d8c8;
                         box-shadow:0 2px 6px rgba(15,81,50,0.05);">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <p style="font-size:15px;font-weight:700;color:#1e293b;margin:0;">🎯 {g.get('name','Goal')}</p>
                {badge}
              </div>
              <div style="display:flex;justify-content:space-between;font-size:12px;color:#6b7280;margin-bottom:4px;">
                <span>Saved: <b style="color:#0f5132;">{fmt_inr(current)}</b></span>
                <span>Target: <b style="color:#1e293b;">{fmt_inr(target)}</b></span>
                <span>Left: <b style="color:#dc2626;">{fmt_inr(remaining)}</b></span>
              </div>
              <p style="font-size:11px;color:#94a3b8;margin:2px 0 8px;">{pct}% complete{tgt_date_str}</p>
              <div style="background:#eef3f0;border-radius:8px;height:10px;overflow:hidden;">
                <div style="background:{bar_color};height:100%;border-radius:8px;width:{pct}%;"></div>
              </div>
            </div>""", unsafe_allow_html=True)

            # Add Funds inline
            if not completed:
                af1, af2 = st.columns([2, 1])
                with af1:
                    add_amt = st.number_input(
                        "Add Funds (₹)", min_value=1.0, step=100.0,
                        key=f"add_funds_{goal_id}", label_visibility="collapsed",
                        placeholder="Add funds (₹)…",
                    )
                with af2:
                    if st.button("💰 Add", key=f"btn_add_{goal_id}", use_container_width=True):
                        try:
                            update_goal_progress(goal_id, add_amt)
                            load_savings_goals_data.clear()
                            st.success(f"✅ {fmt_inr(add_amt)} added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")

            if st.button("🗑️ Delete Goal", key=f"del_goal_{goal_id}", use_container_width=True):
                try:
                    delete_savings_goal(goal_id)
                    load_savings_goals_data.clear()
                    st.success("✅ Goal deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

def render_analytics():
    st.markdown('<h2 style="font-size:22px;font-weight:800;color:#0f5132;margin-bottom:18px;">📊 Analytics</h2>', unsafe_allow_html=True)

    txns = load_txns()
    if not txns:
        st.info("💡 Add transactions (or load sample data from the Dashboard) to see analytics.")
        return

    # ── Line chart: Income · Expenses · Savings over months ──────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">📅 Monthly Overview</p>', unsafe_allow_html=True)
        df = pd.DataFrame(txns)
        df["m_num"] = df["date"].apply(month_num)
        df["m_lbl"] = df["date"].apply(month_label)
        agg     = df.groupby(["m_num", "m_lbl", "type"])["amount"].sum().reset_index()
        ms      = sorted(df["m_num"].unique())
        inc_map = agg[agg["type"] == "income"].set_index("m_num")["amount"].to_dict()
        exp_map = agg[agg["type"] == "expense"].set_index("m_num")["amount"].to_dict()
        lbls    = [MONTHS_ORDER[m - 1] for m in ms]
        inc_v   = [inc_map.get(m, 0) for m in ms]
        exp_v   = [exp_map.get(m, 0) for m in ms]
        sav_v   = [i - e for i, e in zip(inc_v, exp_v)]

        fig_ov = go.Figure()
        for name, vals, color in [("Income", inc_v, "#22c55e"),
                                   ("Expenses", exp_v, "#f87171"),
                                   ("Savings", sav_v, "#60a5fa")]:
            fig_ov.add_trace(go.Scatter(
                x=lbls, y=vals, name=name,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=7),
            ))
        fig_ov.update_layout(
            height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=28, b=0),
            yaxis=dict(gridcolor="#f0f0f0"), xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            legend=dict(orientation="h", y=1.15, x=1, xanchor="right", font=dict(size=11)),
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig_ov, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown('<p style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">🗂️ Category Breakdown</p>', unsafe_allow_html=True)
        exp_list = [t for t in txns if t.get("type") == "expense"]
        if exp_list:
            cat_map: dict[str, float] = {}
            for t in exp_list:
                c = t.get("category", "Others")
                cat_map[c] = cat_map.get(c, 0) + t["amount"]
            fig_pie = go.Figure(go.Pie(
                labels=list(cat_map.keys()), values=list(cat_map.values()),
                hole=0.4,
                marker=dict(colors=[CATEGORY_COLORS.get(k, "#94a3b8") for k in cat_map]),
                textinfo="label+percent", textfont=dict(size=11),
                showlegend=False,
            ))
            fig_pie.update_layout(
                height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0), font=dict(family="Inter"),
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    # ── Summary Metrics ───────────────────────────────────────────────────────
    st.markdown("---")
    total_inc = sum(t["amount"] for t in txns if t.get("type") == "income")
    total_exp = sum(t["amount"] for t in txns if t.get("type") == "expense")
    sav_rate  = int((total_inc - total_exp) / total_inc * 100) if total_inc else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total Transactions", len(txns))
    with m2: st.metric("Total Income",       fmt_inr(total_inc))
    with m3: st.metric("Total Expenses",     fmt_inr(total_exp))
    with m4: st.metric("Savings Rate",       f"{sav_rate}%")


# ══════════════════════════════════════════════════════════════════════════════
# REPORTS
# ══════════════════════════════════════════════════════════════════════════════

def render_reports():
    st.markdown('<h2 style="font-size:22px;font-weight:800;color:#0f5132;margin-bottom:18px;">📄 Reports</h2>', unsafe_allow_html=True)

    txns = load_txns()
    if not txns:
        st.info("💡 Add transactions to generate reports.")
        return

    df = pd.DataFrame(txns)
    df["m_num"] = df["date"].apply(month_num)
    df["m_lbl"] = df["date"].apply(month_label)
    df["year"]  = df["date"].apply(lambda x: x.year if hasattr(x, "year") else 0)

    agg   = df.groupby(["year", "m_num", "m_lbl", "type"])["amount"].sum().reset_index()
    agg   = agg.sort_values(["year", "m_num"])
    inc_m = agg[agg["type"] == "income"][["year","m_num","m_lbl","amount"]].rename(columns={"amount":"Income"})
    exp_m = agg[agg["type"] == "expense"][["year","m_num","m_lbl","amount"]].rename(columns={"amount":"Expenses"})
    rep   = inc_m.merge(exp_m, on=["year","m_num","m_lbl"], how="outer").fillna(0)
    rep["Savings"] = rep["Income"] - rep["Expenses"]
    rep["Rate"]    = (rep["Savings"] / rep["Income"].replace(0, 1) * 100).round(1).astype(str) + "%"
    rep.rename(columns={"m_lbl": "Month", "year": "Year"}, inplace=True)
    for col in ["Income", "Expenses", "Savings"]:
        rep[col] = rep[col].apply(fmt_inr)

    st.markdown('<p style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">📊 Monthly Summary</p>', unsafe_allow_html=True)
    st.dataframe(
        rep[["Year", "Month", "Income", "Expenses", "Savings", "Rate"]].rename(columns={"Rate": "Savings Rate"}),
        use_container_width=True, hide_index=True,
    )

    st.markdown("---")
    st.markdown('<p style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">📥 Export Transactions</p>', unsafe_allow_html=True)
    export = pd.DataFrame([{
        "Date":     t["date"].strftime("%Y-%m-%d") if hasattr(t.get("date"), "strftime") else "",
        "Title":    t.get("title", ""),
        "Type":     t.get("type", ""),
        "Category": t.get("category", ""),
        "Amount":   t.get("amount", 0),
        "Notes":    t.get("notes", ""),
    } for t in txns])
    csv = export.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=f"fintrack_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        type="primary",
    )


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

def render_settings():
    st.markdown('<h2 style="font-size:22px;font-weight:800;color:#0f5132;margin-bottom:18px;">⚙️ Settings</h2>', unsafe_allow_html=True)

    s1, s2 = st.columns(2)

    with s1:
        st.markdown('<p style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">🔌 Database</p>', unsafe_allow_html=True)
        if st.button("🔄 Test MongoDB Connection", use_container_width=True):
            with st.spinner("Pinging Atlas…"):
                try:
                    _db_client.admin.command("ping")
                    st.success(f"✅ Connected! Database: **{_db.name}**")
                    st.info(f"Collections: {', '.join(_db.list_collection_names())}")
                except Exception as e:
                    st.error(f"❌ {e}")

        st.markdown("---")
        st.markdown('<p style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">🌱 Sample Data</p>', unsafe_allow_html=True)
        txns  = load_txns()
        goals = load_goals_data()
        st.info(f"📊 **{len(txns)}** transactions  |  **{len(goals)}** goals in database")

        if len(txns) == 0:
            if st.button("🌱 Load Sample Data", type="primary", use_container_width=True):
                with st.spinner("Seeding 6-month sample data…"):
                    seeded = seed_sample_data_if_empty()
                refresh()
                if seeded:
                    st.success("✅ Sample data loaded! Check the Dashboard.")
                    st.rerun()
                else:
                    st.info("Database already has data.")
        else:
            st.warning("⚠️ Sample data is only loaded into an empty database.")

        st.markdown("---")
        st.markdown('<p style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">🔄 Cache</p>', unsafe_allow_html=True)
        if st.button("🗑️ Clear Data Cache", use_container_width=True):
            refresh()
            st.success("✅ Cache cleared. Data will reload on next view.")

    with s2:
        st.markdown('<p style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:10px;">ℹ️ About FINTRACK</p>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background-color:#f6fbf8;border-radius:14px;padding:18px 20px;border:1.5px solid #b8d8c8;box-shadow:0 2px 6px rgba(15,81,50,0.05);">
          <h4 style="color:#0f5132;margin:0 0 12px;font-size:16px;">🌱 FINTRACK v1.0</h4>
          <p style="font-size:13px;color:#374151;margin:0 0 8px;"><b>Stack:</b> Streamlit 1.65 · MongoDB Atlas · PyMongo · Plotly</p>
          <p style="font-size:13px;color:#374151;margin:0 0 8px;"><b>Features:</b> Income &amp; expense tracking · savings goals · analytics · CSV export</p>
          <p style="font-size:13px;color:#374151;margin:0 0 8px;"><b>Theme:</b> Green Finance Dashboard 💚</p>
          <p style="font-size:13px;color:#374151;margin:0;"><b>Design:</b> Glassmorphism-lite · Inter typeface · Plotly charts</p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════════════════════

def render_profile():
    st.markdown('<h2 style="font-size:22px;font-weight:800;color:#0f5132;margin-bottom:18px;">👤 Profile</h2>', unsafe_allow_html=True)
    p1, p2 = st.columns([1, 1.6])
    with p1:
        st.markdown("""
        <div style="background-color:#f6fbf8;border-radius:14px;padding:26px 20px;border:1.5px solid #b8d8c8;text-align:center;box-shadow:0 2px 6px rgba(15,81,50,0.05);">
            <div style="width:74px;height:74px;border-radius:50%;background:#dbe7e2;margin:0 auto 12px;display:flex;align-items:center;justify-content:center;">
                <svg width="38" height="38" viewBox="0 0 24 24" fill="#0f5132"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            </div>
            <h3 style="margin:0 0 4px;font-size:18px;color:#1e293b;">Priya Sharma</h3>
            <p style="margin:0 0 12px;color:#64748b;font-size:13px;">priya.sharma@fintrack.app</p>
            <div style="display:inline-block;background:#dcfce7;color:#15803d;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;">🌱 Pro Member</div>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown("""
        <div style="background-color:#f6fbf8;border-radius:14px;padding:24px 26px;border:1.5px solid #b8d8c8;box-shadow:0 2px 6px rgba(15,81,50,0.05);">
            <h4 style="margin:0 0 14px;color:#0f5132;font-size:16px;">Financial Account Summary</h4>
            <p style="font-size:13px;color:#475569;margin-bottom:8px;"><b>Currency:</b> Indian Rupee (INR - ₹)</p>
            <p style="font-size:13px;color:#475569;margin-bottom:8px;"><b>Monthly Budget Limit:</b> ₹38,000</p>
            <p style="font-size:13px;color:#475569;margin-bottom:8px;"><b>Connected Database:</b> MongoDB Atlas (fintrack_db)</p>
            <p style="font-size:13px;color:#475569;margin-bottom:0;"><b>Financial Health Score:</b> <span style="color:#16a34a;font-weight:700;">92 / 100 (Excellent)</span></p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════

def render_ai_assistant():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="border-radius:16px;background:#f6fbf8;border:1.5px solid #b8d8c8;
                 box-shadow:0 2px 8px rgba(15,81,50,0.07);padding:20px 26px;
                 margin-bottom:18px;display:flex;align-items:center;gap:18px;">
      <div style="width:54px;height:54px;border-radius:14px;
                   background:linear-gradient(135deg,#d1fae5 0%,#a7f3d0 100%);
                   display:flex;align-items:center;justify-content:center;
                   font-size:28px;flex-shrink:0;">&#x1F916;</div>
      <div>
        <h2 style="font-size:22px;font-weight:800;color:#0f5132;margin:0;"></h2>
        <p style="font-size:22px;font-weight:800;color:#0f5132;margin:0;">&#x1F916; FINTRACK AI Assistant</p>
        <p style="font-size:13px;color:#64748b;margin:4px 0 0;">Ask anything about your finances — powered by Llama 3.3 · Live MongoDB data</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Suggested Questions ───────────────────────────────────────────────
    SUGGESTIONS = [
        "🔍 Am I overspending on Food?",
        "💰 What is my savings rate?",
        "🎯 How long to reach my biggest goal?",
        "📊 Give me a 50-30-20 budget plan based on my income",
        "⚠️ Which category is my biggest spending leak?",
        "💡 How can I save ₹5,000 more per month?",
    ]

    st.markdown('<p style="font-size:13px;font-weight:600;color:#475569;margin-bottom:6px;">Suggested questions — click to ask:</p>', unsafe_allow_html=True)
    sq_cols = st.columns(3)
    for i, suggestion in enumerate(SUGGESTIONS):
        with sq_cols[i % 3]:
            if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                # Inject the suggested question into chat
                if "ai_chat_history" not in st.session_state:
                    st.session_state["ai_chat_history"] = []
                st.session_state["ai_chat_history"].append(
                    {"role": "user", "content": suggestion}
                )
                with st.spinner("🤖 Thinking…"):
                    reply = chat_with_finance_ai(
                        suggestion,
                        st.session_state["ai_chat_history"][:-1],
                    )
                st.session_state["ai_chat_history"].append(
                    {"role": "assistant", "content": reply}
                )
                st.rerun()

    st.markdown("---")

    # ── Chat History ───────────────────────────────────────────────────────────
    if "ai_chat_history" not in st.session_state:
        st.session_state["ai_chat_history"] = []

    history = st.session_state["ai_chat_history"]

    if not history:
        st.markdown("""
        <div style="text-align:center;padding:40px 20px;color:#94a3b8;">
          <p style="font-size:36px;margin-bottom:8px;">🤖</p>
          <p style="font-size:14px;font-weight:600;color:#64748b;">Hi! I'm your FINTRACK AI Advisor.</p>
          <p style="font-size:13px;color:#94a3b8;">Ask me anything about your spending, budgets, or goals.</p>
        </div>""", unsafe_allow_html=True)
    else:
        for msg in history:
            with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])

    # ── Chat Input ───────────────────────────────────────────────────────────
    if user_input := st.chat_input("Ask about your spending, goals, or budgets…"):
        st.session_state["ai_chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤖 Analyzing your data…"):
                reply = chat_with_finance_ai(
                    user_input,
                    st.session_state["ai_chat_history"][:-1],
                )
            st.markdown(reply)

        st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})

    # ── Clear Chat ───────────────────────────────────────────────────────────
    if history:
        if st.button("🗑️ Clear Chat", key="clear_ai_chat"):
            st.session_state["ai_chat_history"] = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

if not check_connection():
    st.warning(
        "⚠️ **MongoDB Atlas Connection Notice**: Unable to connect to your database cluster. "
        "If you see an SSL/Handshake error, please add your current public IP to the IP Access List in "
        "**MongoDB Atlas → Network Access → Add IP Address** (or select **Allow Access from Anywhere** `0.0.0.0/0`)."
    )

_page = selected

if   _page == "🏠 Dashboard":      render_dashboard()
elif _page == "📋 Transactions":   render_transactions()
elif _page == "🕒 Budgets":        render_budgets()
elif _page == "🎯 Goals":          render_goals()
elif _page == "📊 Analytics":      render_analytics()
elif _page == "📄 Reports":        render_reports()
elif _page == "🤖 AI Assistant":   render_ai_assistant()
elif _page == "👤 Profile":        render_profile()
elif _page == "⚙️ Settings":       render_settings()
