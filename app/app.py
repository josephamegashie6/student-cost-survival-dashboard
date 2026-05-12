"""
CostCompass — Plan. Manage. Thrive.
=====================================
Your personal financial guide for studying abroad.
Track your money, plan your move, and make smarter decisions about where and how you live.

Author : Joseph Amegashie
Version: 3.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_option_menu import option_menu
from datetime import date, timedelta, datetime
import math
import numpy as np
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(__file__))
from v2_pages import page_decision_planner, page_admit_comparison, page_stress_test, page_movein_shock, render_entry_screen, init_v2_state

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CostCompass — Plan. Manage. Thrive.",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Bloomberg-inspired dark finance aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
.block-container { padding-top: 2.5rem; max-width: 1400px; }
body, .stApp { background: #050a14; color: #e2e8f0; }

/* ── Glass cards ── */
.glass-card {
    background: rgba(10, 20, 40, 0.85);
    border: 1px solid rgba(20, 184, 166, 0.18);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}
.section-header {
    background: linear-gradient(90deg, rgba(20,184,166,0.12) 0%, rgba(5,10,20,0) 100%);
    border-left: 3px solid #14b8a6;
    padding: 0.5rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1rem;
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: #e2e8f0;
}
.page-title {
    font-size: 1.55rem;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: 0.03em;
    margin-bottom: 0.25rem;
}
.page-subtitle {
    font-size: 0.88rem;
    color: #94a3b8;
    margin-bottom: 1.2rem;
    letter-spacing: 0.02em;
}

/* ── KPI tiles ── */
.kpi-tile {
    background: rgba(10, 20, 40, 0.9);
    border: 1px solid rgba(20,184,166,0.22);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    position: relative;
    overflow: hidden;
}
.kpi-tile::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #14b8a6, #f59e0b);
}
.kpi-label { font-size: 0.78rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; }
.kpi-value { font-size: 1.65rem; font-weight: 700; color: #f8fafc; margin: 0.2rem 0; }
.kpi-delta { font-size: 0.82rem; color: #94a3b8; }
.kpi-green { color: #10b981; }
.kpi-red   { color: #ef4444; }
.kpi-gold  { color: #f59e0b; }
.kpi-teal  { color: #14b8a6; }

/* ── Status pills ── */
.pill {
    display: inline-block;
    padding: 0.15rem 0.65rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.pill-green  { background: rgba(16,185,129,0.12); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
.pill-yellow { background: rgba(245,158,11,0.12); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.pill-red    { background: rgba(239,68,68,0.12);  color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
.pill-teal   { background: rgba(20,184,166,0.12); color: #14b8a6; border: 1px solid rgba(20,184,166,0.3); }

/* ── Alert boxes ── */
.alert-warn {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0;
    color: #fbbf24;
    font-size: 0.88rem;
}
.alert-danger {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0;
    color: #f87171;
    font-size: 0.88rem;
}
.alert-ok {
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0;
    color: #34d399;
    font-size: 0.88rem;
}

/* ── Workflow diagram ── */
.workflow-step {
    background: rgba(20,184,166,0.07);
    border: 1px solid rgba(20,184,166,0.2);
    border-radius: 10px;
    padding: 0.65rem 1rem;
    text-align: center;
    font-size: 0.85rem;
    font-weight: 600;
    color: #14b8a6;
    margin: 0.2rem 0;
}
.workflow-arrow { text-align: center; color: #334155; font-size: 1.1rem; margin: 0.1rem 0; }

/* ── Dividers ── */
hr.soft { border: none; border-top: 1px solid rgba(20,184,166,0.12); margin: 1rem 0; }

/* ── Disclaimer ── */
.disclaimer {
    font-size: 0.78rem;
    color: #475569;
    border-top: 1px solid rgba(20,184,166,0.1);
    padding-top: 0.8rem;
    margin-top: 1.5rem;
    font-style: italic;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #070d1a; border-right: 1px solid rgba(20,184,166,0.12); }

/* ── Metric overrides ── */
[data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 1.4rem !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.06em; }

/* ── Tables ── */
.stDataFrame { border: 1px solid rgba(20,184,166,0.15) !important; border-radius: 10px; }

@media (max-width: 768px) {
    .block-container { padding-top: 1.2rem; padding-left: 0.6rem; padding-right: 0.6rem; }
    .kpi-value { font-size: 1.3rem; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY DARK THEME
# ─────────────────────────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(5,10,20,0)",
    plot_bgcolor="rgba(5,10,20,0)",
    font=dict(color="#94a3b8", size=11),
    xaxis=dict(gridcolor="rgba(20,184,166,0.08)", linecolor="rgba(20,184,166,0.15)"),
    yaxis=dict(gridcolor="rgba(20,184,166,0.08)", linecolor="rgba(20,184,166,0.15)"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
)
COLORS = {
    "teal":   "#14b8a6",
    "gold":   "#f59e0b",
    "green":  "#10b981",
    "red":    "#ef4444",
    "blue":   "#3b82f6",
    "purple": "#8b5cf6",
    "slate":  "#64748b",
}

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
CITY_MIN_WAGE = {
    "Saint Louis": 12.30,
    "Chicago":     15.80,
    "New York City": 16.00,
}
CITY_EXPENSE_PRESETS = {
    "Saint Louis":   {"rent": 900,  "utilities": 140, "food": 360, "transport": 90,  "phone_internet": 65, "misc_basic": 130, "discretionary": 200},
    "Chicago":       {"rent": 1350, "utilities": 170, "food": 460, "transport": 125, "phone_internet": 75, "misc_basic": 160, "discretionary": 250},
    "New York City": {"rent": 1750, "utilities": 195, "food": 550, "transport": 148, "phone_internet": 85, "misc_basic": 195, "discretionary": 300},
}
EXPENSE_COLS = ["rent", "utilities", "food", "transport", "phone_internet", "misc_basic"]
INFLATION_RATE = 0.035  # 3.5% annual

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def usd(x):
    try: return f"${float(x):,.0f}"
    except: return "$0"

def pct(x, decimals=1):
    try: return f"{float(x)*100:.{decimals}f}%"
    except: return "0.0%"

def clamp(n, lo, hi): return max(lo, min(hi, n))

def safe_csv(path):
    try: return pd.read_csv(path)
    except: return None

def pill(label, level):
    css = {"green": "pill-green", "yellow": "pill-yellow", "red": "pill-red", "teal": "pill-teal"}.get(level, "pill-teal")
    return f"<span class='pill {css}'>{label}</span>"

def kpi_tile(label, value, delta=None, color="kpi-teal"):
    delta_html = f"<div class='kpi-delta'>{delta}</div>" if delta else ""
    return f"""
    <div class='kpi-tile'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value {color}'>{value}</div>
        {delta_html}
    </div>"""

def alert_html(msg, level="warn"):
    css = {"warn": "alert-warn", "danger": "alert-danger", "ok": "alert-ok"}.get(level, "alert-warn")
    icon = {"warn": "⚠", "danger": "🔴", "ok": "✓"}.get(level, "⚠")
    return f"<div class='{css}'>{icon} {msg}</div>"

def financial_health_score(income, expenses, rent, balance):
    if income <= 0:
        return 0, {}
    rent_ratio   = rent / income
    savings_rate = balance / income
    buffer_months = (balance / expenses) if expenses > 0 else 0.0

    bal_pts  = 40 if balance > 0 else 0
    rent_pts = int(round(clamp(25 * (0.60 - rent_ratio) / 0.25, 0, 25)))
    sav_pts  = int(round(clamp(20 * (savings_rate / 0.10), 0, 20)))
    buf_pts  = int(round(clamp(15 * buffer_months, 0, 15)))
    score    = int(clamp(bal_pts + rent_pts + sav_pts + buf_pts, 0, 100))

    return score, {
        "rent_ratio": rent_ratio, "savings_rate": savings_rate,
        "buffer_months": buffer_months,
        "bal_pts": bal_pts, "rent_pts": rent_pts, "sav_pts": sav_pts, "buf_pts": buf_pts,
    }

def score_label(score):
    if score >= 80: return "Excellent"
    if score >= 60: return "Good"
    if score >= 40: return "Risky"
    return "Critical"

def affordability_score(income, rent, tuition_monthly=0):
    if income <= 0: return 0
    housing_burden = rent / income
    total_burden   = (rent + tuition_monthly) / income
    score = 100 - int(clamp(housing_burden * 120 + total_burden * 40, 0, 100))
    return max(0, score)

def stress_level(score):
    if score >= 75: return "Low",    "green"
    if score >= 50: return "Moderate","yellow"
    if score >= 30: return "High",   "yellow"
    return "Critical", "red"

def forecast_balance(current_balance, monthly_net, months, inflation_rate=0.035):
    rows = []
    bal = current_balance
    for m in range(1, months + 1):
        inflation_adj = (1 + inflation_rate / 12) ** m
        adj_net = monthly_net / inflation_adj
        bal += adj_net
        rows.append({"Month": m, "Projected Balance": round(bal, 2), "Monthly Net (Inflation-Adj)": round(adj_net, 2)})
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_defaults = {
    "calc_ready": False, "calc_history": [],
    "income": 0.0, "expenses": 0.0, "balance": 0.0,
    "rent": 900.0, "utilities": 140.0, "food": 360.0,
    "transport": 90.0, "phone_internet": 65.0, "misc_basic": 130.0,
    "discretionary": 200.0, "tuition_monthly": 0.0,
    "wage": 12.30, "weekly_hours": 20.0, "weeks_per_month": 4.33,
    "stipend": 0.0, "city": "Saint Louis",
    "health_score": 0, "rent_ratio": 0.0, "savings_rate": 0.0, "buffer_months": 0.0,
    "scenarios": [], "active_scenario_id": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 0.8rem 0 1rem 0;'>
        <div style='font-size:1.15rem; font-weight:700; color:#f59e0b; letter-spacing:0.04em;'>
            🧭 CostCompass
        </div>
        <div style='font-size:0.70rem; color:#475569; margin-top:0.2rem; letter-spacing:0.06em;'>
            PLAN. MANAGE. THRIVE.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Handle navigation from entry screen buttons
    init_v2_state()
    if st.session_state.get("_nav_target"):
        _target = st.session_state.pop("_nav_target")
        # We can't change the selected page directly in option_menu, so we store it
        # and use it as the default_index
        _nav_options = ["Home", "My Budget", "Spending Breakdown", "Future Forecast", "What If?", "City Guide", "Decision Planner", "Compare Offers", "Stress Test", "Move-In Planner", "How It Works", "Settings"]
        _nav_default = _nav_options.index(_target) if _target in _nav_options else 0
    else:
        _nav_default = 0

    page = option_menu(
        menu_title=None,
        options=["Home", "My Budget", "Spending Breakdown", "Future Forecast", "What If?", "City Guide", "Decision Planner", "Compare Offers", "Stress Test", "Move-In Planner", "How It Works", "Settings"],
        icons=["house-heart", "wallet2", "pie-chart", "graph-up-arrow", "sliders", "building", "compass", "bar-chart-steps", "activity", "truck", "info-circle", "gear"],
        menu_icon="cast",
        default_index=_nav_default,
        styles={
            "container":      {"background-color": "transparent", "padding": "0"},
            "icon":           {"color": "#14b8a6", "font-size": "0.85rem"},
            "nav-link":       {"font-size": "0.82rem", "color": "#94a3b8", "padding": "0.45rem 0.8rem", "border-radius": "6px"},
            "nav-link-selected": {"background-color": "rgba(20,184,166,0.12)", "color": "#14b8a6", "font-weight": "600"},
        },
    )

    st.markdown("<hr class='soft'>", unsafe_allow_html=True)

    # Quick snapshot
    if st.session_state["calc_ready"]:
        bal = st.session_state["balance"]
        inc = st.session_state["income"]
        exp = st.session_state["expenses"]
        score = st.session_state["health_score"]
        status_label = "SURPLUS" if bal > 0 else ("BREAK-EVEN" if bal == 0 else "DEFICIT")
        status_color = "#10b981" if bal > 0 else ("#f59e0b" if bal == 0 else "#ef4444")
        st.markdown(f"""
        <div style='font-size:0.72rem; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;'>Live Position</div>
        <div style='font-size:1.3rem; font-weight:700; color:{status_color};'>{usd(bal)}<span style='font-size:0.75rem; margin-left:0.4rem;'>/mo net</span></div>
        <div style='font-size:0.78rem; color:{status_color}; margin-bottom:0.6rem;'>{status_label}</div>
        <div style='font-size:0.75rem; color:#64748b;'>Inflows: {usd(inc)} &nbsp;|&nbsp; Outflows: {usd(exp)}</div>
        <div style='font-size:0.75rem; color:#64748b; margin-top:0.2rem;'>Financial Health: {score}/100</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size:0.78rem; color:#475569;'>Go to My Budget to set up your finances.</div>", unsafe_allow_html=True)

    st.markdown("<hr class='soft'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.70rem; color:#334155; text-align:center;'>CostCompass v3.0</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: OVERVIEW / EXECUTIVE SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
if page == "Home":
    st.markdown("<div class='page-title'>Welcome to CostCompass</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Your financial guide for studying abroad · Plan. Manage. Thrive.</div>", unsafe_allow_html=True)

    # ── Onboarding flow for first-time users
    if not st.session_state.get("onboarding_done") and not st.session_state.get("calc_ready"):
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(20,184,166,0.08) 0%,rgba(245,158,11,0.06) 100%);
        border:1px solid rgba(245,158,11,0.25);border-radius:16px;padding:1.6rem 2rem;margin-bottom:1.5rem;'>
            <div style='font-size:1.2rem;font-weight:700;color:#f59e0b;margin-bottom:0.4rem;'>👋 Welcome to CostCompass</div>
            <div style='font-size:0.92rem;color:#94a3b8;line-height:1.7;'>
            CostCompass helps you understand the real cost of studying abroad — before you arrive and after.
            Follow these 3 steps to get your full financial picture:
            </div>
        </div>""", unsafe_allow_html=True)
        ob1, ob2, ob3 = st.columns(3)
        with ob1:
            st.markdown("""
            <div style='background:rgba(10,20,40,0.9);border:1px solid rgba(20,184,166,0.2);
            border-radius:12px;padding:1.2rem;text-align:center;'>
                <div style='font-size:2rem;margin-bottom:0.5rem;'>💰</div>
                <div style='font-size:0.95rem;font-weight:700;color:#14b8a6;margin-bottom:0.3rem;'>Step 1</div>
                <div style='font-size:0.88rem;font-weight:600;color:#e2e8f0;margin-bottom:0.3rem;'>Enter your income</div>
                <div style='font-size:0.78rem;color:#64748b;'>Go to <strong style='color:#94a3b8;'>My Budget</strong> and add your stipend, wages, or family support.</div>
            </div>""", unsafe_allow_html=True)
        with ob2:
            st.markdown("""
            <div style='background:rgba(10,20,40,0.9);border:1px solid rgba(245,158,11,0.2);
            border-radius:12px;padding:1.2rem;text-align:center;'>
                <div style='font-size:2rem;margin-bottom:0.5rem;'>🏠</div>
                <div style='font-size:0.95rem;font-weight:700;color:#f59e0b;margin-bottom:0.3rem;'>Step 2</div>
                <div style='font-size:0.88rem;font-weight:600;color:#e2e8f0;margin-bottom:0.3rem;'>Add your expenses</div>
                <div style='font-size:0.78rem;color:#64748b;'>Enter rent, groceries, transport, and other monthly costs.</div>
            </div>""", unsafe_allow_html=True)
        with ob3:
            st.markdown("""
            <div style='background:rgba(10,20,40,0.9);border:1px solid rgba(16,185,129,0.2);
            border-radius:12px;padding:1.2rem;text-align:center;'>
                <div style='font-size:2rem;margin-bottom:0.5rem;'>🧭</div>
                <div style='font-size:0.95rem;font-weight:700;color:#10b981;margin-bottom:0.3rem;'>Step 3</div>
                <div style='font-size:0.88rem;font-weight:600;color:#e2e8f0;margin-bottom:0.3rem;'>Get your plan</div>
                <div style='font-size:0.78rem;color:#64748b;'>Use <strong style='color:#94a3b8;'>Decision Planner</strong> to check if your city and school are affordable.</div>
            </div>""", unsafe_allow_html=True)
        if st.button("Got it — let's start →", key="onboarding_dismiss", type="primary"):
            st.session_state["onboarding_done"] = True
            st.session_state["_nav_target"] = "My Budget"
            st.rerun()
        st.markdown("<hr class='soft'>", unsafe_allow_html=True)

    # KPI row
    if st.session_state["calc_ready"]:
        inc  = st.session_state["income"]
        exp  = st.session_state["expenses"]
        bal  = st.session_state["balance"]
        rent = st.session_state["rent"]
        score = st.session_state["health_score"]
        rr   = st.session_state["rent_ratio"]
        sr   = st.session_state["savings_rate"]
        bm   = st.session_state["buffer_months"]
        aff  = affordability_score(inc, rent, st.session_state["tuition_monthly"])
        sl, sl_color = stress_level(aff)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            color = "kpi-green" if bal > 0 else "kpi-red"
            st.markdown(kpi_tile("Projected Net Liquidity", usd(bal), f"{'Surplus' if bal>0 else 'Deficit'} position", color), unsafe_allow_html=True)
        with c2:
            st.markdown(kpi_tile("Total Monthly Inflows", usd(inc), "Wage + stipend", "kpi-teal"), unsafe_allow_html=True)
        with c3:
            st.markdown(kpi_tile("Total Monthly Outflows", usd(exp), "All expense categories", "kpi-gold"), unsafe_allow_html=True)
        with c4:
            color = "kpi-green" if score >= 60 else ("kpi-gold" if score >= 40 else "kpi-red")
            st.markdown(kpi_tile("Financial Stability Indicator", f"{score}/100", f"Health score · {score_label(score)}", color), unsafe_allow_html=True)

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            color = "kpi-green" if rr <= 0.30 else ("kpi-gold" if rr <= 0.40 else "kpi-red")
            st.markdown(kpi_tile("Rent Burden Ratio", pct(rr), "Housing cost pressure", color), unsafe_allow_html=True)
        with c6:
            color = "kpi-green" if sr >= 0.10 else ("kpi-gold" if sr >= 0.05 else "kpi-red")
            st.markdown(kpi_tile("Cash Reserve Position", pct(sr), "Savings rate vs income", color), unsafe_allow_html=True)
        with c7:
            color = "kpi-green" if bm >= 2 else ("kpi-gold" if bm >= 1 else "kpi-red")
            st.markdown(kpi_tile("Emergency Fund Coverage", f"{bm:.1f} mo", "Runway if income stops", color), unsafe_allow_html=True)
        with c8:
            color = "kpi-green" if sl == "Low" else ("kpi-gold" if sl in ("Moderate","High") else "kpi-red")
            st.markdown(kpi_tile("Affordability Score", f"{aff}/100", f"Financial stress: {sl}", color), unsafe_allow_html=True)

        # Behavioral alerts
        st.markdown("<hr class='soft'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Your Financial Alerts</div>", unsafe_allow_html=True)
        alerts = []
        if rr > 0.40: alerts.append(("Rent Warning: Your rent is over 40% of your income. This is a high-risk level — consider a cheaper option or a roommate.", "danger"))
        if bal < 0:   alerts.append(("Spending More Than You Earn: Your expenses are higher than your income this month. You need to cut costs or find more income.", "danger"))
        if sr < 0.05: alerts.append(("Low Savings Rate: You are saving less than 5% of your income. Try to build a small buffer each month.", "warn"))
        if bm < 1:    alerts.append(("No Emergency Buffer: Your savings would not cover even one month of expenses if your income stopped. Try to build at least 1 month of reserves.", "warn"))
        disc = st.session_state.get("discretionary", 0)
        if inc > 0 and disc / inc > 0.15: alerts.append(("High Discretionary Spending: More than 15% of your income is going to non-essential spending. Review your social and entertainment budget.", "warn"))
        if not alerts:
            st.markdown(alert_html("You are in good shape. No major financial concerns right now.", "ok"), unsafe_allow_html=True)
        else:
            for msg, lvl in alerts:
                st.markdown(alert_html(msg, lvl), unsafe_allow_html=True)
    # Workflow diagramm
    st.markdown("<div class='section-header'>How CostCompass Works</div>", unsafe_allow_html=True)
    wf_cols = st.columns([1, 0.15, 1, 0.15, 1, 0.15, 1, 0.15, 1, 0.15, 1])
    steps = ["Enter Your Income", "Add Your Expenses", "See Your Budget", "Forecast Your Future", "Check Your Risk", "Make Better Decisions"]
    for i, step in enumerate(steps):
        with wf_cols[i * 2]:
            st.markdown(f"<div class='workflow-step'>{step}</div>", unsafe_allow_html=True)
        if i < len(steps) - 1:
            with wf_cols[i * 2 + 1]:
                st.markdown("<div class='workflow-arrow'>→</div>", unsafe_allow_html=True)

    
    # ── Entry screen: 4-path decision flow
    render_entry_screen()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: CASH FLOW ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "My Budget":
    st.markdown("<div class='page-title'>My Budget</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>See exactly where your money comes from and where it goes each month.</div>", unsafe_allow_html=True)

    with st.form("cashflow_form"):
        st.markdown("<div class='section-header'>Income Parameters</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            city = st.selectbox("City / Market", list(CITY_MIN_WAGE.keys()))
            wage = st.number_input("Hourly wage ($/hr)", min_value=0.0, value=float(CITY_MIN_WAGE.get(city, 12.30)), step=0.25)
        with c2:
            weekly_hours = st.number_input("Weekly work hours", min_value=0.0, max_value=40.0, value=20.0, step=1.0)
            weeks_per_month = st.number_input("Weeks per month", min_value=3.0, max_value=5.0, value=4.33, step=0.01)
        with c3:
            stipend = st.number_input("Monthly stipend / support ($)", min_value=0.0, value=1500.0, step=50.0)
            tuition_monthly = st.number_input("Monthly tuition allocation ($)", min_value=0.0, value=0.0, step=50.0, help="Tuition amortised monthly for affordability analysis")

        st.markdown("<div class='section-header' style='margin-top:1rem;'>Your Monthly Expenses</div>", unsafe_allow_html=True)
        preset = CITY_EXPENSE_PRESETS.get(city, CITY_EXPENSE_PRESETS["Saint Louis"])
        use_preset = st.checkbox("Populate with city benchmark values")

        e1, e2, e3, e4 = st.columns(4)
        def pv(k, fb): return float(preset.get(k, fb)) if use_preset else float(fb)
        with e1:
            rent       = st.number_input("Rent ($)",           min_value=0.0, value=pv("rent",900),        step=25.0)
            utilities  = st.number_input("Utilities ($)",      min_value=0.0, value=pv("utilities",140),   step=10.0)
        with e2:
            food       = st.number_input("Food & Groceries ($)",min_value=0.0, value=pv("food",360),       step=10.0)
            transport  = st.number_input("Transportation ($)", min_value=0.0, value=pv("transport",90),    step=10.0)
        with e3:
            phone_internet = st.number_input("Phone / Internet ($)", min_value=0.0, value=pv("phone_internet",65), step=5.0)
            misc_basic     = st.number_input("Essential Misc ($)",    min_value=0.0, value=pv("misc_basic",130),   step=10.0)
        with e4:
            discretionary = st.number_input("Discretionary Spending ($)", min_value=0.0, value=pv("discretionary",200), step=25.0, help="Non-essential: entertainment, dining out, subscriptions")
            emergency_reserve = st.number_input("Emergency Reserve Target ($)", min_value=0.0, value=500.0, step=50.0)

        submitted = st.form_submit_button("Run Cash Flow Analysis", use_container_width=True)

    if submitted:
        monthly_wage = wage * weekly_hours * weeks_per_month
        total_income = monthly_wage + stipend
        fixed_expenses = rent + utilities + phone_internet
        variable_expenses = food + transport + misc_basic + discretionary
        total_expenses = fixed_expenses + variable_expenses + tuition_monthly
        balance = total_income - total_expenses
        score, breakdown = financial_health_score(total_income, total_expenses, rent, balance)

        # Persist to session
        st.session_state.update({
            "calc_ready": True, "city": city,
            "income": total_income, "expenses": total_expenses, "balance": balance,
            "rent": rent, "utilities": utilities, "food": food,
            "transport": transport, "phone_internet": phone_internet,
            "misc_basic": misc_basic, "discretionary": discretionary,
            "tuition_monthly": tuition_monthly,
            "wage": wage, "weekly_hours": weekly_hours, "weeks_per_month": weeks_per_month,
            "stipend": stipend,
            "health_score": score,
            "rent_ratio": breakdown.get("rent_ratio", 0),
            "savings_rate": breakdown.get("savings_rate", 0),
            "buffer_months": breakdown.get("buffer_months", 0),
        })
        hist = st.session_state["calc_history"]
        hist.append({"ts": str(datetime.now()), "income": total_income, "expenses": total_expenses, "balance": balance, "score": score})
        st.session_state["calc_history"] = hist[-12:]

    if st.session_state["calc_ready"]:
        total_income  = st.session_state["income"]
        total_expenses = st.session_state["expenses"]
        balance       = st.session_state["balance"]
        rent          = st.session_state["rent"]
        utilities     = st.session_state["utilities"]
        food          = st.session_state["food"]
        transport     = st.session_state["transport"]
        phone_internet = st.session_state["phone_internet"]
        misc_basic    = st.session_state["misc_basic"]
        discretionary = st.session_state["discretionary"]
        tuition_monthly = st.session_state["tuition_monthly"]
        score         = st.session_state["health_score"]

        fixed_expenses    = rent + utilities + phone_internet
        variable_expenses = food + transport + misc_basic + discretionary

        st.markdown("<hr class='soft'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Monthly Summary</div>", unsafe_allow_html=True)

        k1, k2, k3, k4 = st.columns(4)
        with k1: st.metric("Total Monthly Inflows",  usd(total_income))
        with k2: st.metric("Total Monthly Outflows", usd(total_expenses))
        with k3:
            delta_color = "normal" if balance >= 0 else "inverse"
            st.metric("Projected Net Liquidity", usd(balance), delta=f"{'Surplus' if balance >= 0 else 'Deficit'}")
        with k4: st.metric("Financial Stability Indicator", f"{score}/100")

        st.markdown("<div class='section-header' style='margin-top:1rem;'>Fixed vs Flexible Spending</div>", unsafe_allow_html=True)

        ch1, ch2 = st.columns(2)
        with ch1:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Total Inflows",  x=["Monthly Position"], y=[total_income],  marker_color=COLORS["teal"],  text=[usd(total_income)],  textposition="outside"))
            fig.add_trace(go.Bar(name="Fixed Outflows", x=["Monthly Position"], y=[fixed_expenses], marker_color=COLORS["gold"],  text=[usd(fixed_expenses)], textposition="outside"))
            fig.add_trace(go.Bar(name="Variable Outflows", x=["Monthly Position"], y=[variable_expenses], marker_color=COLORS["red"], text=[usd(variable_expenses)], textposition="outside"))
            fig.update_layout(title="Inflows vs Fixed vs Variable Outflows", barmode="group", **PLOT_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            labels = ["Rent", "Utilities", "Phone/Internet", "Food", "Transport", "Essential Misc", "Discretionary"]
            if tuition_monthly > 0: labels.append("Tuition")
            values = [rent, utilities, phone_internet, food, transport, misc_basic, discretionary]
            if tuition_monthly > 0: values.append(tuition_monthly)
            colors_pie = [COLORS["red"], COLORS["gold"], COLORS["purple"], COLORS["teal"], COLORS["blue"], COLORS["green"], COLORS["slate"]]
            if tuition_monthly > 0: colors_pie.append("#f97316")
            fig2 = go.Figure(go.Pie(
                labels=labels, values=values,
                hole=0.52,
                marker=dict(colors=colors_pie, line=dict(color="#050a14", width=2)),
                textinfo="label+percent", textfont=dict(size=10),
            ))
            fig2.update_layout(title="Expense Allocation by Category", **PLOT_LAYOUT)
            st.plotly_chart(fig2, use_container_width=True)

        # Savings trajectory
        st.markdown("<div class='section-header'>Your Savings Over the Next 12 Months</div>", unsafe_allow_html=True)
        months_proj = list(range(1, 13))
        cumulative_savings = [max(0, balance) * m for m in months_proj]
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=months_proj, y=cumulative_savings, mode="lines+markers",
                                  line=dict(color=COLORS["teal"], width=2.5),
                                  marker=dict(size=6, color=COLORS["teal"]),
                                  fill="tozeroy", fillcolor="rgba(20,184,166,0.08)",
                                  name="Cumulative Cash Reserve"))
        fig3.update_layout(title="Projected Cash Reserve Accumulation (12 Months, No Inflation Adjustment)",
                           xaxis_title="Month", yaxis_title="Cumulative Balance (USD)", **PLOT_LAYOUT)
        st.plotly_chart(fig3, use_container_width=True)

        


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: COST INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Spending Breakdown":
    st.markdown("<div class='page-title'>Spending Breakdown</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Understand how your spending compares to safe limits — and where the pressure is building.</div>", unsafe_allow_html=True)

    if not st.session_state["calc_ready"]:
        st.info("Run Cash Flow Analysis first to activate cost intelligence modules.")
        st.stop()

    inc  = st.session_state["income"]
    rent = st.session_state["rent"]
    food = st.session_state["food"]
    transport = st.session_state["transport"]
    utilities = st.session_state["utilities"]
    phone_internet = st.session_state["phone_internet"]
    misc_basic = st.session_state["misc_basic"]
    discretionary = st.session_state["discretionary"]
    tuition_monthly = st.session_state["tuition_monthly"]
    exp  = st.session_state["expenses"]
    bal  = st.session_state["balance"]

    # Cost burden ratios
    st.markdown("<div class='section-header'>Where Your Money Is Going</div>", unsafe_allow_html=True)
    burden_data = [
        ("Rent Burden Ratio",          rent / inc if inc > 0 else 0,       0.30, 0.40, "Housing cost as % of inflows"),
        ("Tuition Pressure Indicator", tuition_monthly / inc if inc > 0 else 0, 0.20, 0.35, "Tuition allocation as % of inflows"),
        ("Transportation Expense Ratio", transport / inc if inc > 0 else 0, 0.08, 0.15, "Transport cost as % of inflows"),
        ("Food Cost Ratio",            food / inc if inc > 0 else 0,        0.15, 0.25, "Food spend as % of inflows"),
        ("Discretionary Spending Ratio", discretionary / inc if inc > 0 else 0, 0.10, 0.18, "Non-essential spend as % of inflows"),
    ]

    b1, b2 = st.columns(2)
    for i, (label, ratio, warn_thresh, danger_thresh, desc) in enumerate(burden_data):
        col = b1 if i % 2 == 0 else b2
        with col:
            if ratio <= warn_thresh:   status, color = "Healthy",  "green"
            elif ratio <= danger_thresh: status, color = "Elevated", "yellow"
            else:                       status, color = "Critical", "red"
            st.markdown(f"""
            <div class='glass-card' style='padding:0.9rem 1.1rem; margin-bottom:0.7rem;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <div style='font-size:0.78rem; color:#64748b; text-transform:uppercase; letter-spacing:0.06em;'>{label}</div>
                        <div style='font-size:1.4rem; font-weight:700; color:#f8fafc; margin:0.15rem 0;'>{pct(ratio)}</div>
                        <div style='font-size:0.78rem; color:#64748b;'>{desc}</div>
                    </div>
                    {pill(status, color)}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Financial health indicators
    st.markdown("<div class='section-header'>Your Financial Health</div>", unsafe_allow_html=True)
    score = st.session_state["health_score"]
    rr    = st.session_state["rent_ratio"]
    sr    = st.session_state["savings_rate"]
    bm    = st.session_state["buffer_months"]
    aff   = affordability_score(inc, rent, tuition_monthly)
    sl, sl_color = stress_level(aff)

    h1, h2, h3, h4 = st.columns(4)
    with h1: st.metric("Emergency Fund Coverage", f"{bm:.1f} mo", help="Months of expenses covered by current net balance")
    with h2: st.metric("Affordability Score",     f"{aff}/100",  help="Composite affordability index (higher = more affordable)")
    with h3: st.metric("Financial Stress Level",  sl,            help="Derived from rent burden + tuition pressure")
    with h4: st.metric("Discretionary Ratio",     pct(discretionary / inc if inc > 0 else 0), help="Non-essential spending as % of inflows")

    # Spending anomaly detection
    st.markdown("<div class='section-header'>Spending Warnings</div>", unsafe_allow_html=True)
    hist = pd.DataFrame(st.session_state["calc_history"])
    if len(hist) >= 3:
        hist["balance"] = pd.to_numeric(hist["balance"], errors="coerce")
        hist["expenses"] = pd.to_numeric(hist["expenses"], errors="coerce")
        rolling_avg = hist["expenses"].rolling(3).mean().iloc[-1]
        current_exp = st.session_state["expenses"]
        deviation = (current_exp - rolling_avg) / rolling_avg if rolling_avg > 0 else 0
        if abs(deviation) > 0.10:
            direction = "above" if deviation > 0 else "below"
            st.markdown(alert_html(f"Spending Anomaly Detected: Current outflows are {abs(deviation)*100:.1f}% {direction} the 3-run rolling average ({usd(rolling_avg)}). Review expense categories for unusual activity.", "warn"), unsafe_allow_html=True)
        else:
            st.markdown(alert_html(f"Spending within normal range. Current outflows deviate {abs(deviation)*100:.1f}% from 3-run rolling average ({usd(rolling_avg)}).", "ok"), unsafe_allow_html=True)

        # Budget deviation tracking
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(x=list(range(len(hist))), y=hist["expenses"],
                                      mode="lines+markers", name="Monthly Outflows",
                                      line=dict(color=COLORS["gold"], width=2), marker=dict(size=5)))
        fig_hist.add_trace(go.Scatter(x=list(range(len(hist))), y=hist["expenses"].rolling(3, min_periods=1).mean(),
                                      mode="lines", name="3-Run Rolling Avg",
                                      line=dict(color=COLORS["teal"], width=1.5, dash="dash")))
        fig_hist.update_layout(title="Outflow Trend & Rolling Average", xaxis_title="Run", yaxis_title="USD", **PLOT_LAYOUT)
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Run Cash Flow Analysis at least 3 times to activate anomaly detection and trend tracking.")

    


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: FORECASTING
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Future Forecast":
    st.markdown("<div class='page-title'>Future Forecast</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>See how your finances will look 6 to 12 months from now — including inflation.</div>", unsafe_allow_html=True)

    if not st.session_state["calc_ready"]:
        st.info("Run Cash Flow Analysis first to activate forecasting modules.")
        st.stop()

    inc = st.session_state["income"]
    exp = st.session_state["expenses"]
    bal = st.session_state["balance"]
    monthly_net = inc - exp

    f1, f2, f3 = st.columns(3)
    with f1:
        forecast_months = st.slider("Forecast horizon (months)", 3, 24, 12)
    with f2:
        inflation_override = st.slider("Annual inflation rate (%)", 0.0, 10.0, 3.5, 0.5) / 100
    with f3:
        starting_balance = st.number_input("Starting cash balance ($)", min_value=0.0, value=max(0.0, float(bal)), step=100.0)

    df_forecast = forecast_balance(starting_balance, monthly_net, forecast_months, inflation_override)

    # Summary KPIs
    final_bal = df_forecast["Projected Balance"].iloc[-1]
    min_bal   = df_forecast["Projected Balance"].min()
    avg_net   = df_forecast["Monthly Net (Inflation-Adj)"].mean()

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Projected Balance (End of Period)", usd(final_bal))
    with k2: st.metric("Minimum Projected Balance",         usd(min_bal), delta="Lowest point" if min_bal < starting_balance else None)
    with k3: st.metric("Avg Inflation-Adjusted Monthly Net", usd(avg_net))
    with k4:
        semester_months = 4
        sem_bal = forecast_balance(starting_balance, monthly_net, semester_months, inflation_override)["Projected Balance"].iloc[-1]
        st.metric("Semester Affordability Projection", usd(sem_bal), delta=f"{semester_months}-month horizon")

    # Forecast chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_forecast["Month"], y=df_forecast["Projected Balance"],
        mode="lines+markers", name="Projected Balance",
        line=dict(color=COLORS["teal"], width=2.5),
        marker=dict(size=5), fill="tozeroy", fillcolor="rgba(20,184,166,0.06)",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS["red"], annotation_text="Zero Balance", annotation_font_color=COLORS["red"])
    fig.add_hline(y=starting_balance, line_dash="dot", line_color=COLORS["slate"], annotation_text="Starting Balance", annotation_font_color=COLORS["slate"])
    fig.update_layout(title=f"Inflation-Adjusted Balance Forecast ({forecast_months} Months, {inflation_override*100:.1f}% Annual Inflation)",
                      xaxis_title="Month", yaxis_title="Projected Balance (USD)", **PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # Inflation-adjusted net
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_forecast["Month"], y=df_forecast["Monthly Net (Inflation-Adj)"],
        marker_color=[COLORS["teal"] if v >= 0 else COLORS["red"] for v in df_forecast["Monthly Net (Inflation-Adj)"]],
        name="Monthly Net (Inflation-Adj)",
    ))
    fig2.add_hline(y=0, line_color=COLORS["slate"], line_dash="dash")
    fig2.update_layout(title="Inflation-Adjusted Monthly Net Liquidity Over Time",
                       xaxis_title="Month", yaxis_title="Monthly Net (USD)", **PLOT_LAYOUT)
    st.plotly_chart(fig2, use_container_width=True)

    if min_bal < 0:
        st.markdown(alert_html(f"Liquidity Warning: Projected balance turns negative at month {df_forecast[df_forecast['Projected Balance']<0]['Month'].iloc[0]}. Consider increasing inflows or reducing outflows to maintain positive liquidity.", "danger"), unsafe_allow_html=True)
    else:
        st.markdown(alert_html(f"Positive liquidity maintained throughout the {forecast_months}-month forecast horizon. Projected end balance: {usd(final_bal)}.", "ok"), unsafe_allow_html=True)

    


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5: SCENARIO ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "What If?":
    st.markdown("<div class='page-title'>What If?</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Test how rent increases, income cuts, or extra costs would affect your plan.</div>", unsafe_allow_html=True)

    if not st.session_state["calc_ready"]:
        st.info("Run Cash Flow Analysis first to activate scenario modelling.")
        st.stop()

    base_inc  = st.session_state["income"]
    base_exp  = st.session_state["expenses"]
    base_bal  = st.session_state["balance"]
    base_rent = st.session_state["rent"]

    st.markdown("<div class='section-header'>Set Your Scenario</div>", unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1:
        rent_increase_pct = st.slider("Rent increase (%)",          0, 50, 0, 5)
        tuition_increase  = st.slider("Tuition increase ($/month)", 0, 500, 0, 25)
    with s2:
        income_reduction_pct = st.slider("Income reduction (%)",       0, 50, 0, 5)
        spending_reduction   = st.slider("Spending reduction ($/month)", 0, 500, 0, 25)

    # Compute scenario
    scen_rent = base_rent * (1 + rent_increase_pct / 100)
    scen_inc  = base_inc * (1 - income_reduction_pct / 100)
    scen_exp  = base_exp + (scen_rent - base_rent) + tuition_increase - spending_reduction
    scen_bal  = scen_inc - scen_exp
    delta_bal = scen_bal - base_bal

    st.markdown("<div class='section-header'>How This Scenario Changes Your Plan</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Baseline Net Liquidity",  usd(base_bal))
    with c2: st.metric("Scenario Net Liquidity",  usd(scen_bal), delta=usd(delta_bal))
    with c3: st.metric("Scenario Total Inflows",  usd(scen_inc), delta=usd(scen_inc - base_inc))
    with c4: st.metric("Scenario Total Outflows", usd(scen_exp), delta=usd(scen_exp - base_exp))

    # Waterfall chart
    fig = go.Figure(go.Waterfall(
        name="Impact Analysis",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "relative", "total"],
        x=["Baseline Balance", "Rent Increase", "Tuition Increase", "Income Reduction", "Spending Reduction", "Scenario Balance"],
        y=[base_bal,
           -(scen_rent - base_rent),
           -tuition_increase,
           -(base_inc - scen_inc),
           spending_reduction,
           0],
        connector=dict(line=dict(color=COLORS["slate"])),
        increasing=dict(marker=dict(color=COLORS["teal"])),
        decreasing=dict(marker=dict(color=COLORS["red"])),
        totals=dict(marker=dict(color=COLORS["gold"])),
        text=[usd(base_bal), usd(-(scen_rent - base_rent)), usd(-tuition_increase),
              usd(-(base_inc - scen_inc)), usd(spending_reduction), usd(scen_bal)],
        textposition="outside",
    ))
    fig.update_layout(title="Scenario Impact Waterfall Analysis", yaxis_title="USD", **PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # Scenario risk assessment
    st.markdown("<div class='section-header'>Risk Assessment</div>", unsafe_allow_html=True)
    scen_score, scen_bd = financial_health_score(scen_inc, scen_exp, scen_rent, scen_bal)
    scen_rr = scen_bd.get("rent_ratio", 0)
    scen_sr = scen_bd.get("savings_rate", 0)
    scen_bm = scen_bd.get("buffer_months", 0)

    r1, r2, r3, r4 = st.columns(4)
    with r1: st.metric("Scenario Health Score",    f"{scen_score}/100", delta=f"{scen_score - st.session_state['health_score']:+d} vs baseline")
    with r2: st.metric("Scenario Rent Burden",     pct(scen_rr), delta=pct(scen_rr - st.session_state["rent_ratio"]))
    with r3: st.metric("Scenario Cash Reserve",    pct(scen_sr), delta=pct(scen_sr - st.session_state["savings_rate"]))
    with r4: st.metric("Scenario Fund Coverage",   f"{scen_bm:.1f} mo", delta=f"{scen_bm - st.session_state['buffer_months']:.1f} mo")

    if scen_bal < 0:
        st.markdown(alert_html("Scenario results in a cashflow deficit. This combination of changes is financially unsustainable without additional income or significant expense reduction.", "danger"), unsafe_allow_html=True)
    elif scen_bal < base_bal * 0.5:
        st.markdown(alert_html("Scenario significantly reduces net liquidity. Financial resilience is materially weakened under these conditions.", "warn"), unsafe_allow_html=True)
    else:
        st.markdown(alert_html("Scenario remains financially viable. Net liquidity is positive and within acceptable parameters.", "ok"), unsafe_allow_html=True)

    # Recurring expense monitoring
    st.markdown("<div class='section-header'>Recurring Expenses</div>", unsafe_allow_html=True)
    recurring = {
        "Rent": st.session_state["rent"],
        "Utilities": st.session_state["utilities"],
        "Phone/Internet": st.session_state["phone_internet"],
    }
    variable = {
        "Food": st.session_state["food"],
        "Transport": st.session_state["transport"],
        "Essential Misc": st.session_state["misc_basic"],
        "Discretionary": st.session_state["discretionary"],
    }
    rec_total = sum(recurring.values())
    var_total = sum(variable.values())

    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown(f"**Fixed / Recurring Outflows** — {usd(rec_total)} ({pct(rec_total / base_inc if base_inc > 0 else 0)} of inflows)")
        for k, v in recurring.items():
            st.markdown(f"- {k}: **{usd(v)}** ({pct(v / base_inc if base_inc > 0 else 0)})")
    with rc2:
        st.markdown(f"**Variable Outflows** — {usd(var_total)} ({pct(var_total / base_inc if base_inc > 0 else 0)} of inflows)")
        for k, v in variable.items():
            st.markdown(f"- {k}: **{usd(v)}** ({pct(v / base_inc if base_inc > 0 else 0)})")

    


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 6: CITY ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "City Guide":
    st.markdown("<div class='page-title'>City Guide</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Compare the real cost of living across cities — rent, food, transport, and more.</div>", unsafe_allow_html=True)

    data = safe_csv("data/student_costs.csv")
    if data is None:
        data = safe_csv("../data/student_costs.csv")
    if data is None:
        st.error("Could not load data/student_costs.csv.")
        st.stop()

    data["month_dt"] = pd.to_datetime(data["month"], format="%Y-%m", errors="coerce")
    data["total_income"]   = data["campus_job_income"] + data["stipend_income"]
    data["total_expenses"] = data[EXPENSE_COLS].sum(axis=1)
    if "discretionary" in data.columns:
        data["total_expenses"] += data["discretionary"]
    if "emergency_expense" in data.columns:
        data["total_expenses"] += data["emergency_expense"]
    if "tuition_monthly" in data.columns:
        data["total_expenses"] += data["tuition_monthly"]
    data["balance"] = data["total_income"] - data["total_expenses"]
    data["rent_burden"] = data["rent"] / data["total_income"]

    cities = sorted(data["city"].dropna().unique().tolist())
    months = sorted(data["month"].dropna().unique().tolist())

    f1, f2, f3 = st.columns(3)
    with f1: sel_cities = st.multiselect("Cities", cities, default=cities)
    with f2: start_m    = st.selectbox("From", months, index=0)
    with f3: end_m      = st.selectbox("To",   months, index=len(months)-1)

    mask = (data["city"].isin(sel_cities)) & (data["month"] >= start_m) & (data["month"] <= end_m)
    df = data[mask].copy()

    if df.empty:
        st.warning("No data for selected filters.")
        st.stop()

    # Summary KPIs per city
    st.markdown("<div class='section-header'>City Comparison Summary</div>", unsafe_allow_html=True)
    summary = df.groupby("city").agg(
        Avg_Inflows=("total_income", "mean"),
        Avg_Outflows=("total_expenses", "mean"),
        Avg_Balance=("balance", "mean"),
        Avg_Rent_Burden=("rent_burden", "mean"),
        Min_Balance=("balance", "min"),
    ).reset_index()

    for _, row in summary.iterrows():
        with st.expander(f"📍 {row['city']}", expanded=True):
            cc1, cc2, cc3, cc4, cc5 = st.columns(5)
            cc1.metric("Avg Monthly Inflows",  usd(row["Avg_Inflows"]))
            cc2.metric("Avg Monthly Outflows", usd(row["Avg_Outflows"]))
            cc3.metric("Avg Net Liquidity",    usd(row["Avg_Balance"]))
            cc4.metric("Avg Rent Burden",      pct(row["Avg_Rent_Burden"]))
            cc5.metric("Worst Month Balance",  usd(row["Min_Balance"]))

    # Balance trend
    st.markdown("<div class='section-header'>Monthly Net Position by City</div>", unsafe_allow_html=True)
    fig = px.line(df, x="month", y="balance", color="city",
                  color_discrete_map={"Saint Louis": COLORS["teal"], "Chicago": COLORS["gold"], "New York City": COLORS["red"]},
                  markers=True, title="Monthly Net Liquidity by City")
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS["slate"])
    fig.update_layout(xaxis_title="Month", yaxis_title="Net Liquidity (USD)", **PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # Expense breakdown by city
    ch1, ch2 = st.columns(2)
    with ch1:
        avg_exp = df.groupby("city")[EXPENSE_COLS].mean().reset_index()
        fig2 = px.bar(avg_exp.melt(id_vars="city", var_name="Category", value_name="Amount"),
                      x="city", y="Amount", color="Category", barmode="stack",
                      title="Average Monthly Expense Breakdown by City",
                      color_discrete_sequence=[COLORS["red"], COLORS["gold"], COLORS["teal"], COLORS["blue"], COLORS["purple"], COLORS["green"]])
        fig2.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    with ch2:
        fig3 = px.line(df, x="month", y="rent_burden", color="city",
                       color_discrete_map={"Saint Louis": COLORS["teal"], "Chicago": COLORS["gold"], "New York City": COLORS["red"]},
                       title="Rent Burden Ratio Over Time", markers=True)
        fig3.add_hline(y=0.30, line_dash="dot", line_color=COLORS["green"], annotation_text="30% Healthy")
        fig3.add_hline(y=0.40, line_dash="dot", line_color=COLORS["red"],   annotation_text="40% Critical")
        fig3.update_layout(xaxis_title="Month", yaxis_title="Rent Burden Ratio", **PLOT_LAYOUT)
        st.plotly_chart(fig3, use_container_width=True)

    # Semester phase analysis
    if "semester_phase" in df.columns:
        st.markdown("<div class='section-header'>Semester-by-Semester Breakdown</div>", unsafe_allow_html=True)
        phase_summary = df.groupby(["city", "semester_phase"]).agg(
            Avg_Balance=("balance", "mean"),
            Avg_Outflows=("total_expenses", "mean"),
        ).reset_index()
        fig4 = px.bar(phase_summary, x="semester_phase", y="Avg_Balance", color="city", barmode="group",
                      title="Average Net Liquidity by Semester Phase",
                      color_discrete_map={"Saint Louis": COLORS["teal"], "Chicago": COLORS["gold"], "New York City": COLORS["red"]})
        fig4.add_hline(y=0, line_dash="dash", line_color=COLORS["slate"])
        fig4.update_layout(xaxis_title="Phase", yaxis_title="Avg Net Liquidity (USD)", **PLOT_LAYOUT)
        st.plotly_chart(fig4, use_container_width=True)

    


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 7: CASE STUDY
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Decision Planner":
    page_decision_planner()
elif page == "Compare Offers":
    page_admit_comparison()
elif page == "Stress Test":
    page_stress_test()
elif page == "Move-In Planner":
    page_movein_shock()
elif page == "How It Works":
    st.markdown("<div class='page-title'>How CostCompass Works</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>A quick guide to getting the most out of every feature.</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='glass-card'>
        <div class='section-header'>What CostCompass Does</div>
        <p style='color:#94a3b8; font-size:0.9rem; line-height:1.75;'>
        Students navigating academic and living expenses face compounding financial pressures — rising housing costs,
        tuition obligations, variable income streams, and limited financial planning infrastructure. Without structured
        analytical tools, students lack visibility into their <strong style='color:#e2e8f0;'>affordability position</strong>,
        <strong style='color:#e2e8f0;'>spending behaviour patterns</strong>, and <strong style='color:#e2e8f0;'>long-term financial sustainability</strong>.
        This creates reactive rather than proactive financial decision-making.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='glass-card'>
        <div class='section-header'>How It Helps You</div>
        <p style='color:#94a3b8; font-size:0.9rem; line-height:1.75;'>
        Developed a <strong style='color:#14b8a6;'>financial intelligence platform</strong> combining spending analytics,
        affordability monitoring, inflation-adjusted forecasting, and scenario simulation. The system transforms raw
        financial inputs into structured decision-support outputs — enabling data-driven financial planning aligned
        with institutional analytics standards.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>System Features</div>", unsafe_allow_html=True)
    feat_cols = st.columns(3)
    features = [
        ("📊", "Cash Flow Analysis",      "Monthly inflow/outflow decomposition, fixed vs variable expense categorisation, savings trajectory modelling"),
        ("🔍", "Cost Burden Analysis",     "Rent burden ratio, tuition pressure indicator, transportation and food cost ratios with threshold-based alerts"),
        ("💡", "Financial Health Scoring", "Composite 0–100 stability indicator covering balance position, rent burden, savings rate, and emergency fund coverage"),
        ("📈", "Forecasting Engine",       "Inflation-adjusted 24-month balance projection, semester affordability modelling, liquidity risk detection"),
        ("⚙️", "Scenario Simulation",     "Rent increase, tuition pressure, income reduction, and spending cut scenarios with waterfall impact analysis"),
        ("🏙️", "City Analytics",          "Multi-city cost-of-living comparison across 18 months of realistic data with semester-phase financial analysis"),
    ]
    for i, (icon, title, desc) in enumerate(features):
        with feat_cols[i % 3]:
            st.markdown(f"""
            <div class='glass-card' style='min-height:130px;'>
                <div style='font-size:1.4rem; margin-bottom:0.4rem;'>{icon}</div>
                <div style='font-size:0.88rem; font-weight:600; color:#e2e8f0; margin-bottom:0.4rem;'>{title}</div>
                <div style='font-size:0.80rem; color:#64748b; line-height:1.55;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Technical Architecture</div>", unsafe_allow_html=True)
    tech_data = {
        "Component": ["Language", "Framework", "Data Processing", "Visualisation", "Forecasting Model", "Analytics", "Deployment"],
        "Technology": ["Python 3.11", "Streamlit", "Pandas / NumPy", "Plotly (interactive)", "Inflation-adjusted projection model", "Cost burden ratios, affordability scoring, anomaly detection", "GitHub / Streamlit Cloud"],
        "Purpose": ["Core analytical logic", "Interactive financial dashboard", "Data transformation and aggregation", "Bloomberg-style dark finance charts", "Multi-period balance and liquidity forecasting", "Financial health indicators and behavioural alerts", "Version control and live deployment"],
    }
    st.dataframe(pd.DataFrame(tech_data), use_container_width=True, hide_index=True)

    st.markdown("<div class='section-header'>Impact & Outcomes</div>", unsafe_allow_html=True)
    i1, i2, i3, i4 = st.columns(4)
    with i1: st.markdown(kpi_tile("Financial Visibility", "360°", "Full income-expense-forecast view", "kpi-teal"), unsafe_allow_html=True)
    with i2: st.markdown(kpi_tile("Analytical Depth", "5 Modules", "CF, Cost, Health, Forecast, Scenario", "kpi-gold"), unsafe_allow_html=True)
    with i3: st.markdown(kpi_tile("Data Realism", "18 Months", "3 cities, semester phases, inflation", "kpi-green"), unsafe_allow_html=True)
    with i4: st.markdown(kpi_tile("Decision Support", "Real-time", "Scenario simulation & alerts", "kpi-teal"), unsafe_allow_html=True)

    st.markdown("""
    <div class='glass-card' style='margin-top:1rem;'>
        <div class='section-header'>How CostCompass Works</div>
    """, unsafe_allow_html=True)
    wf2 = st.columns([1, 0.15, 1, 0.15, 1, 0.15, 1, 0.15, 1, 0.15, 1])
    steps2 = ["Enter Your Income", "Add Your Expenses", "See Your Budget", "Forecast Your Future", "Check Your Risk", "Make Better Decisions"]
    for i, step in enumerate(steps2):
        with wf2[i * 2]:
            st.markdown(f"<div class='workflow-step'>{step}</div>", unsafe_allow_html=True)
        if i < len(steps2) - 1:
            with wf2[i * 2 + 1]:
                st.markdown("<div class='workflow-arrow'>→</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Settings":
    st.markdown("<div class='page-title'>Settings</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Personalise CostCompass to match your situation.</div>", unsafe_allow_html=True)

    with st.form("settings_form"):
        st.markdown("<div class='section-header'>Your Profile</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            home_country = st.selectbox(
                "Home country",
                ["Ghana", "Nigeria", "Kenya", "India", "China", "Pakistan", "Bangladesh", "Ethiopia", "South Africa", "Other"],
                index=["Ghana", "Nigeria", "Kenya", "India", "China", "Pakistan", "Bangladesh", "Ethiopia", "South Africa", "Other"].index(
                    st.session_state.get("settings_home_country", "Ghana")
                )
            )
        with c2:
            default_city = st.selectbox(
                "Default city",
                ["St. Louis, MO", "Chicago, IL", "New York, NY", "Boston, MA", "Houston, TX", "Atlanta, GA", "Los Angeles, CA", "Seattle, WA", "Austin, TX", "Other"],
                index=0
            )

        st.markdown("<div class='section-header' style='margin-top:1rem;'>Currency & FX</div>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            home_currency = st.selectbox(
                "Home currency",
                ["GHS (Ghana Cedi)", "NGN (Nigerian Naira)", "KES (Kenyan Shilling)", "INR (Indian Rupee)", "CNY (Chinese Yuan)", "PKR (Pakistani Rupee)", "USD (US Dollar)", "Other"],
                index=["GHS (Ghana Cedi)", "NGN (Nigerian Naira)", "KES (Kenyan Shilling)", "INR (Indian Rupee)", "CNY (Chinese Yuan)", "PKR (Pakistani Rupee)", "USD (US Dollar)", "Other"].index(
                    st.session_state.get("settings_home_currency", "GHS (Ghana Cedi)")
                )
            )
        with c4:
            fx_rate = st.number_input(
                "Exchange rate (1 home unit = ? USD)",
                min_value=0.0001, max_value=100.0,
                value=float(st.session_state.get("settings_fx_rate", 0.067)),
                step=0.001, format="%.4f"
            )

        st.markdown("<div class='section-header' style='margin-top:1rem;'>Display</div>", unsafe_allow_html=True)
        c5, c6 = st.columns(2)
        with c5:
            show_tips = st.toggle("Show financial tips on dashboard", value=st.session_state.get("settings_show_tips", True))
        with c6:
            compact_mode = st.toggle("Compact mode (fewer charts)", value=st.session_state.get("settings_compact", False))

        st.markdown("<div class='section-header' style='margin-top:1rem;'>Data</div>", unsafe_allow_html=True)
        reset_confirm = st.checkbox("I want to reset all my saved data")

        saved = st.form_submit_button("Save Settings", use_container_width=True)

    if saved:
        st.session_state["settings_home_country"] = home_country
        st.session_state["settings_default_city"] = default_city
        st.session_state["settings_home_currency"] = home_currency
        st.session_state["settings_fx_rate"] = fx_rate
        st.session_state["settings_show_tips"] = show_tips
        st.session_state["settings_compact"] = compact_mode
        if reset_confirm:
            keys_to_keep = {k for k in st.session_state if k.startswith("settings_")}
            for k in list(st.session_state.keys()):
                if k not in keys_to_keep:
                    del st.session_state[k]
            st.success("All data has been reset. Your settings have been saved.")
        else:
            st.success("Settings saved.")

    st.markdown("<hr class='soft'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.78rem; color:#475569; text-align:center; padding:1rem 0;'>
        CostCompass v3.0 &nbsp;·&nbsp; Built by Joseph Amegashie &nbsp;·&nbsp;
        <a href='mailto:amegashie@wustl.edu' style='color:#f59e0b; text-decoration:none;'>amegashie@wustl.edu</a>
    </div>
    """, unsafe_allow_html=True)

    



