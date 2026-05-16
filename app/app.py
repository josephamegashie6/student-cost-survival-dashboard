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
    "New York City": 17.0,
    "Los Angeles": 17.0,
    "Chicago": 15.5,
    "Houston": 12.0,
    "Phoenix": 12.0,
    "Philadelphia": 14.0,
    "San Antonio": 12.0,
    "San Diego": 15.5,
    "Dallas": 14.0,
    "San Jose": 17.0,
    "Austin": 14.0,
    "Jacksonville": 12.0,
    "Fort Worth": 12.0,
    "Columbus": 12.0,
    "Charlotte": 12.0,
    "Indianapolis": 12.0,
    "San Francisco": 17.0,
    "Seattle": 15.5,
    "Denver": 14.0,
    "Nashville": 14.0,
    "Oklahoma City": 10.0,
    "El Paso": 10.0,
    "Washington DC": 17.0,
    "Boston": 17.0,
    "Memphis": 10.0,
    "Louisville": 10.0,
    "Portland": 14.0,
    "Las Vegas": 12.0,
    "Milwaukee": 12.0,
    "Albuquerque": 12.0,
    "Tucson": 10.0,
    "Fresno": 12.0,
    "Sacramento": 14.0,
    "Mesa": 12.0,
    "Kansas City": 12.0,
    "Atlanta": 14.0,
    "Omaha": 10.0,
    "Colorado Springs": 12.0,
    "Raleigh": 12.0,
    "Virginia Beach": 12.0,
    "Minneapolis": 14.0,
    "Tampa": 12.0,
    "New Orleans": 12.0,
    "Miami": 15.5,
    "Orlando": 12.0,
    "Baltimore": 14.0,
    "Pittsburgh": 12.0,
    "Cincinnati": 12.0,
    "Cleveland": 10.0,
    "Detroit": 10.0,
    "St. Louis": 12.0,
    "Salt Lake City": 12.0,
    "Hartford": 12.0,
    "Providence": 12.0,
    "Buffalo": 10.0,
    "Rochester": 10.0,
    "Albany": 12.0,
    "Baton Rouge": 12.0,
    "Des Moines": 10.0,
    "Madison": 12.0,
    "Ann Arbor": 14.0,
    "Champaign": 10.0,
    "Amherst": 12.0,
    "College Station": 10.0,
    "Tempe": 12.0,
    "Evanston": 14.0,
    "Durham": 12.0,
    "Chapel Hill": 12.0,
    "Charlottesville": 12.0,
    "Knoxville": 10.0,
    "Gainesville": 12.0,
    "Tallahassee": 10.0,
    "Lexington": 10.0,
    "Richmond": 12.0,
    "Anchorage": 14.0,
    "Honolulu": 15.5,
    "Birmingham": 10.0,
    "Tucson": 10.0,
    "Fayetteville": 10.0,
    "Lincoln": 10.0,
    "Sioux Falls": 10.0,
    "Bismarck": 10.0,
    "Cheyenne": 10.0,
    "Helena": 10.0,
    "Boise": 12.0,
    "Portland": 12.0,
    "Burlington": 12.0,
    "Concord": 12.0,
    "Manchester": 12.0,
    "London": 17.0,
    "Manchester": 14.0,
    "Birmingham": 14.0,
    "Edinburgh": 14.0,
    "Glasgow": 14.0,
    "Leeds": 14.0,
    "Bristol": 14.0,
    "Sheffield": 12.0,
    "Nottingham": 12.0,
    "Southampton": 12.0,
    "Cardiff": 12.0,
    "Oxford": 15.5,
    "Cambridge": 15.5,
    "Coventry": 12.0,
    "Leicester": 12.0,
    "Exeter": 12.0,
    "Newcastle": 12.0,
    "Liverpool": 12.0,
    "Warwick": 12.0,
    "Toronto": 15.5,
    "Vancouver": 15.5,
    "Montreal": 14.0,
    "Calgary": 14.0,
    "Ottawa": 14.0,
    "Edmonton": 12.0,
    "Winnipeg": 12.0,
    "Quebec City": 12.0,
    "Hamilton": 12.0,
    "Waterloo": 12.0,
    "Kingston": 12.0,
    "Halifax": 12.0,
    "Victoria": 14.0,
    "London": 12.0,
    "Saskatoon": 12.0,
    "Guelph": 12.0,
    "St. Catharines": 12.0,
    "Kelowna": 12.0,
}
CITY_EXPENSE_PRESETS = {
    "New York City": {"rent": 2800, "utilities": 160, "food": 480, "transport": 130, "phone_internet": 80, "misc_basic": 180, "discretionary": 280},
    "Los Angeles": {"rent": 2350, "utilities": 130, "food": 400, "transport": 110, "phone_internet": 70, "misc_basic": 160, "discretionary": 260},
    "Chicago": {"rent": 1750, "utilities": 145, "food": 380, "transport": 105, "phone_internet": 70, "misc_basic": 140, "discretionary": 220},
    "Houston": {"rent": 1450, "utilities": 125, "food": 320, "transport": 75, "phone_internet": 65, "misc_basic": 120, "discretionary": 190},
    "Phoenix": {"rent": 1400, "utilities": 120, "food": 310, "transport": 65, "phone_internet": 65, "misc_basic": 115, "discretionary": 185},
    "Philadelphia": {"rent": 1700, "utilities": 140, "food": 360, "transport": 85, "phone_internet": 70, "misc_basic": 135, "discretionary": 210},
    "San Antonio": {"rent": 1200, "utilities": 118, "food": 300, "transport": 60, "phone_internet": 65, "misc_basic": 112, "discretionary": 175},
    "San Diego": {"rent": 2150, "utilities": 128, "food": 390, "transport": 100, "phone_internet": 70, "misc_basic": 150, "discretionary": 235},
    "Dallas": {"rent": 1500, "utilities": 122, "food": 325, "transport": 70, "phone_internet": 65, "misc_basic": 118, "discretionary": 190},
    "San Jose": {"rent": 2600, "utilities": 140, "food": 420, "transport": 105, "phone_internet": 75, "misc_basic": 170, "discretionary": 270},
    "Austin": {"rent": 1700, "utilities": 135, "food": 340, "transport": 85, "phone_internet": 65, "misc_basic": 130, "discretionary": 210},
    "Jacksonville": {"rent": 1300, "utilities": 118, "food": 295, "transport": 60, "phone_internet": 65, "misc_basic": 110, "discretionary": 170},
    "Fort Worth": {"rent": 1300, "utilities": 120, "food": 300, "transport": 62, "phone_internet": 65, "misc_basic": 112, "discretionary": 172},
    "Columbus": {"rent": 1300, "utilities": 118, "food": 295, "transport": 55, "phone_internet": 65, "misc_basic": 112, "discretionary": 170},
    "Charlotte": {"rent": 1380, "utilities": 120, "food": 305, "transport": 65, "phone_internet": 65, "misc_basic": 115, "discretionary": 180},
    "Indianapolis": {"rent": 1100, "utilities": 115, "food": 285, "transport": 55, "phone_internet": 60, "misc_basic": 108, "discretionary": 165},
    "San Francisco": {"rent": 3100, "utilities": 140, "food": 450, "transport": 120, "phone_internet": 75, "misc_basic": 190, "discretionary": 300},
    "Seattle": {"rent": 2100, "utilities": 150, "food": 390, "transport": 95, "phone_internet": 70, "misc_basic": 155, "discretionary": 240},
    "Denver": {"rent": 1850, "utilities": 138, "food": 350, "transport": 80, "phone_internet": 65, "misc_basic": 135, "discretionary": 215},
    "Nashville": {"rent": 1650, "utilities": 128, "food": 330, "transport": 70, "phone_internet": 65, "misc_basic": 125, "discretionary": 200},
    "Oklahoma City": {"rent": 1000, "utilities": 112, "food": 275, "transport": 55, "phone_internet": 60, "misc_basic": 105, "discretionary": 160},
    "El Paso": {"rent": 950, "utilities": 110, "food": 265, "transport": 52, "phone_internet": 60, "misc_basic": 100, "discretionary": 155},
    "Washington DC": {"rent": 2400, "utilities": 150, "food": 410, "transport": 100, "phone_internet": 75, "misc_basic": 165, "discretionary": 255},
    "Boston": {"rent": 2400, "utilities": 155, "food": 420, "transport": 90, "phone_internet": 75, "misc_basic": 165, "discretionary": 250},
    "Memphis": {"rent": 1000, "utilities": 112, "food": 275, "transport": 55, "phone_internet": 60, "misc_basic": 105, "discretionary": 158},
    "Louisville": {"rent": 1050, "utilities": 113, "food": 278, "transport": 55, "phone_internet": 60, "misc_basic": 106, "discretionary": 160},
    "Portland": {"rent": 1700, "utilities": 140, "food": 365, "transport": 90, "phone_internet": 65, "misc_basic": 130, "discretionary": 210},
    "Las Vegas": {"rent": 1400, "utilities": 125, "food": 315, "transport": 70, "phone_internet": 65, "misc_basic": 115, "discretionary": 182},
    "Milwaukee": {"rent": 1150, "utilities": 118, "food": 285, "transport": 60, "phone_internet": 60, "misc_basic": 108, "discretionary": 165},
    "Albuquerque": {"rent": 1150, "utilities": 118, "food": 285, "transport": 60, "phone_internet": 60, "misc_basic": 108, "discretionary": 165},
    "Tucson": {"rent": 1050, "utilities": 118, "food": 278, "transport": 58, "phone_internet": 60, "misc_basic": 105, "discretionary": 160},
    "Fresno": {"rent": 1150, "utilities": 120, "food": 285, "transport": 60, "phone_internet": 60, "misc_basic": 108, "discretionary": 165},
    "Sacramento": {"rent": 1600, "utilities": 130, "food": 340, "transport": 78, "phone_internet": 65, "misc_basic": 125, "discretionary": 195},
    "Mesa": {"rent": 1300, "utilities": 118, "food": 300, "transport": 62, "phone_internet": 65, "misc_basic": 112, "discretionary": 172},
    "Kansas City": {"rent": 1200, "utilities": 118, "food": 290, "transport": 58, "phone_internet": 60, "misc_basic": 110, "discretionary": 170},
    "Atlanta": {"rent": 1600, "utilities": 130, "food": 330, "transport": 80, "phone_internet": 65, "misc_basic": 125, "discretionary": 200},
    "Omaha": {"rent": 1050, "utilities": 115, "food": 278, "transport": 55, "phone_internet": 60, "misc_basic": 106, "discretionary": 160},
    "Colorado Springs": {"rent": 1300, "utilities": 120, "food": 300, "transport": 62, "phone_internet": 65, "misc_basic": 112, "discretionary": 172},
    "Raleigh": {"rent": 1450, "utilities": 122, "food": 310, "transport": 65, "phone_internet": 65, "misc_basic": 115, "discretionary": 185},
    "Virginia Beach": {"rent": 1380, "utilities": 120, "food": 305, "transport": 62, "phone_internet": 65, "misc_basic": 112, "discretionary": 178},
    "Minneapolis": {"rent": 1500, "utilities": 140, "food": 320, "transport": 70, "phone_internet": 65, "misc_basic": 125, "discretionary": 195},
    "Tampa": {"rent": 1500, "utilities": 125, "food": 320, "transport": 68, "phone_internet": 65, "misc_basic": 118, "discretionary": 185},
    "New Orleans": {"rent": 1250, "utilities": 122, "food": 295, "transport": 62, "phone_internet": 65, "misc_basic": 112, "discretionary": 172},
    "Miami": {"rent": 2100, "utilities": 135, "food": 380, "transport": 85, "phone_internet": 70, "misc_basic": 150, "discretionary": 240},
    "Orlando": {"rent": 1500, "utilities": 125, "food": 320, "transport": 68, "phone_internet": 65, "misc_basic": 118, "discretionary": 185},
    "Baltimore": {"rent": 1500, "utilities": 130, "food": 330, "transport": 70, "phone_internet": 65, "misc_basic": 120, "discretionary": 190},
    "Pittsburgh": {"rent": 1300, "utilities": 120, "food": 300, "transport": 60, "phone_internet": 65, "misc_basic": 115, "discretionary": 175},
    "Cincinnati": {"rent": 1150, "utilities": 115, "food": 285, "transport": 55, "phone_internet": 60, "misc_basic": 108, "discretionary": 165},
    "Cleveland": {"rent": 1050, "utilities": 115, "food": 278, "transport": 55, "phone_internet": 60, "misc_basic": 106, "discretionary": 160},
    "Detroit": {"rent": 1050, "utilities": 118, "food": 278, "transport": 55, "phone_internet": 60, "misc_basic": 106, "discretionary": 160},
    "St. Louis": {"rent": 1200, "utilities": 125, "food": 310, "transport": 65, "phone_internet": 65, "misc_basic": 120, "discretionary": 180},
    "Salt Lake City": {"rent": 1450, "utilities": 122, "food": 315, "transport": 68, "phone_internet": 65, "misc_basic": 115, "discretionary": 182},
    "Hartford": {"rent": 1500, "utilities": 128, "food": 320, "transport": 68, "phone_internet": 65, "misc_basic": 118, "discretionary": 185},
    "Providence": {"rent": 1450, "utilities": 125, "food": 315, "transport": 68, "phone_internet": 65, "misc_basic": 115, "discretionary": 182},
    "Buffalo": {"rent": 1050, "utilities": 118, "food": 278, "transport": 55, "phone_internet": 60, "misc_basic": 106, "discretionary": 160},
    "Rochester": {"rent": 1000, "utilities": 115, "food": 272, "transport": 52, "phone_internet": 60, "misc_basic": 104, "discretionary": 158},
    "Albany": {"rent": 1200, "utilities": 118, "food": 285, "transport": 58, "phone_internet": 60, "misc_basic": 108, "discretionary": 165},
    "Baton Rouge": {"rent": 1200, "utilities": 118, "food": 285, "transport": 58, "phone_internet": 60, "misc_basic": 108, "discretionary": 165},
    "Des Moines": {"rent": 1050, "utilities": 115, "food": 275, "transport": 55, "phone_internet": 60, "misc_basic": 106, "discretionary": 160},
    "Madison": {"rent": 1380, "utilities": 125, "food": 305, "transport": 55, "phone_internet": 65, "misc_basic": 115, "discretionary": 175},
    "Ann Arbor": {"rent": 1500, "utilities": 130, "food": 315, "transport": 55, "phone_internet": 65, "misc_basic": 120, "discretionary": 185},
    "Champaign": {"rent": 1100, "utilities": 115, "food": 280, "transport": 45, "phone_internet": 60, "misc_basic": 105, "discretionary": 160},
    "Amherst": {"rent": 1250, "utilities": 120, "food": 290, "transport": 50, "phone_internet": 65, "misc_basic": 110, "discretionary": 170},
    "College Station": {"rent": 1050, "utilities": 110, "food": 270, "transport": 45, "phone_internet": 60, "misc_basic": 100, "discretionary": 155},
    "Tempe": {"rent": 1450, "utilities": 120, "food": 310, "transport": 65, "phone_internet": 65, "misc_basic": 115, "discretionary": 185},
    "Evanston": {"rent": 1700, "utilities": 138, "food": 345, "transport": 85, "phone_internet": 70, "misc_basic": 130, "discretionary": 205},
    "Durham": {"rent": 1500, "utilities": 122, "food": 315, "transport": 65, "phone_internet": 65, "misc_basic": 118, "discretionary": 185},
    "Chapel Hill": {"rent": 1450, "utilities": 120, "food": 310, "transport": 62, "phone_internet": 65, "misc_basic": 115, "discretionary": 182},
    "Charlottesville": {"rent": 1300, "utilities": 118, "food": 295, "transport": 58, "phone_internet": 65, "misc_basic": 112, "discretionary": 172},
    "Knoxville": {"rent": 1050, "utilities": 115, "food": 275, "transport": 55, "phone_internet": 60, "misc_basic": 106, "discretionary": 160},
    "Gainesville": {"rent": 1150, "utilities": 118, "food": 280, "transport": 58, "phone_internet": 60, "misc_basic": 108, "discretionary": 165},
    "Tallahassee": {"rent": 1050, "utilities": 115, "food": 275, "transport": 55, "phone_internet": 60, "misc_basic": 105, "discretionary": 160},
    "Lexington": {"rent": 1000, "utilities": 113, "food": 272, "transport": 52, "phone_internet": 60, "misc_basic": 104, "discretionary": 158},
    "Richmond": {"rent": 1300, "utilities": 118, "food": 295, "transport": 60, "phone_internet": 65, "misc_basic": 112, "discretionary": 172},
    "Anchorage": {"rent": 1450, "utilities": 175, "food": 380, "transport": 72, "phone_internet": 70, "misc_basic": 130, "discretionary": 195},
    "Honolulu": {"rent": 2200, "utilities": 175, "food": 420, "transport": 85, "phone_internet": 70, "misc_basic": 160, "discretionary": 250},
    "Birmingham": {"rent": 1000, "utilities": 112, "food": 270, "transport": 52, "phone_internet": 60, "misc_basic": 102, "discretionary": 155},
    "Tucson": {"rent": 1050, "utilities": 118, "food": 278, "transport": 58, "phone_internet": 60, "misc_basic": 105, "discretionary": 160},
    "Fayetteville": {"rent": 1000, "utilities": 110, "food": 268, "transport": 50, "phone_internet": 60, "misc_basic": 100, "discretionary": 155},
    "Lincoln": {"rent": 1000, "utilities": 112, "food": 270, "transport": 52, "phone_internet": 60, "misc_basic": 102, "discretionary": 155},
    "Sioux Falls": {"rent": 1000, "utilities": 112, "food": 268, "transport": 50, "phone_internet": 60, "misc_basic": 100, "discretionary": 155},
    "Bismarck": {"rent": 1000, "utilities": 115, "food": 268, "transport": 50, "phone_internet": 60, "misc_basic": 100, "discretionary": 155},
    "Cheyenne": {"rent": 1050, "utilities": 115, "food": 270, "transport": 52, "phone_internet": 60, "misc_basic": 102, "discretionary": 158},
    "Helena": {"rent": 1050, "utilities": 115, "food": 272, "transport": 52, "phone_internet": 60, "misc_basic": 102, "discretionary": 158},
    "Boise": {"rent": 1300, "utilities": 118, "food": 295, "transport": 58, "phone_internet": 60, "misc_basic": 110, "discretionary": 168},
    "Portland": {"rent": 1380, "utilities": 122, "food": 305, "transport": 60, "phone_internet": 65, "misc_basic": 112, "discretionary": 175},
    "Burlington": {"rent": 1380, "utilities": 122, "food": 305, "transport": 58, "phone_internet": 65, "misc_basic": 112, "discretionary": 175},
    "Concord": {"rent": 1300, "utilities": 120, "food": 295, "transport": 55, "phone_internet": 65, "misc_basic": 110, "discretionary": 170},
    "Manchester": {"rent": 1300, "utilities": 120, "food": 295, "transport": 55, "phone_internet": 65, "misc_basic": 110, "discretionary": 170},
    "London": {"rent": 2200, "utilities": 180, "food": 400, "transport": 150, "phone_internet": 70, "misc_basic": 165, "discretionary": 260},
    "Manchester": {"rent": 1200, "utilities": 158, "food": 330, "transport": 105, "phone_internet": 65, "misc_basic": 128, "discretionary": 198},
    "Birmingham": {"rent": 1150, "utilities": 155, "food": 320, "transport": 100, "phone_internet": 65, "misc_basic": 125, "discretionary": 192},
    "Edinburgh": {"rent": 1400, "utilities": 162, "food": 340, "transport": 110, "phone_internet": 65, "misc_basic": 132, "discretionary": 205},
    "Glasgow": {"rent": 1150, "utilities": 155, "food": 320, "transport": 105, "phone_internet": 65, "misc_basic": 125, "discretionary": 192},
    "Leeds": {"rent": 1150, "utilities": 152, "food": 315, "transport": 100, "phone_internet": 65, "misc_basic": 122, "discretionary": 188},
    "Bristol": {"rent": 1300, "utilities": 158, "food": 330, "transport": 105, "phone_internet": 65, "misc_basic": 128, "discretionary": 198},
    "Sheffield": {"rent": 1000, "utilities": 148, "food": 305, "transport": 95, "phone_internet": 60, "misc_basic": 118, "discretionary": 180},
    "Nottingham": {"rent": 1000, "utilities": 148, "food": 302, "transport": 92, "phone_internet": 60, "misc_basic": 116, "discretionary": 178},
    "Southampton": {"rent": 1150, "utilities": 152, "food": 315, "transport": 98, "phone_internet": 65, "misc_basic": 120, "discretionary": 185},
    "Cardiff": {"rent": 1000, "utilities": 148, "food": 302, "transport": 92, "phone_internet": 60, "misc_basic": 116, "discretionary": 178},
    "Oxford": {"rent": 1600, "utilities": 162, "food": 345, "transport": 108, "phone_internet": 70, "misc_basic": 132, "discretionary": 205},
    "Cambridge": {"rent": 1600, "utilities": 160, "food": 342, "transport": 106, "phone_internet": 70, "misc_basic": 130, "discretionary": 202},
    "Coventry": {"rent": 950, "utilities": 145, "food": 295, "transport": 88, "phone_internet": 60, "misc_basic": 112, "discretionary": 172},
    "Leicester": {"rent": 950, "utilities": 145, "food": 295, "transport": 88, "phone_internet": 60, "misc_basic": 112, "discretionary": 172},
    "Exeter": {"rent": 1050, "utilities": 150, "food": 308, "transport": 92, "phone_internet": 60, "misc_basic": 118, "discretionary": 180},
    "Newcastle": {"rent": 1000, "utilities": 148, "food": 305, "transport": 95, "phone_internet": 60, "misc_basic": 118, "discretionary": 180},
    "Liverpool": {"rent": 1000, "utilities": 148, "food": 305, "transport": 98, "phone_internet": 60, "misc_basic": 118, "discretionary": 180},
    "Warwick": {"rent": 1050, "utilities": 150, "food": 308, "transport": 92, "phone_internet": 60, "misc_basic": 118, "discretionary": 180},
    "Toronto": {"rent": 1900, "utilities": 158, "food": 360, "transport": 118, "phone_internet": 70, "misc_basic": 145, "discretionary": 225},
    "Vancouver": {"rent": 2100, "utilities": 142, "food": 375, "transport": 112, "phone_internet": 70, "misc_basic": 152, "discretionary": 238},
    "Montreal": {"rent": 1400, "utilities": 138, "food": 330, "transport": 95, "phone_internet": 65, "misc_basic": 128, "discretionary": 198},
    "Calgary": {"rent": 1500, "utilities": 152, "food": 340, "transport": 100, "phone_internet": 65, "misc_basic": 130, "discretionary": 200},
    "Ottawa": {"rent": 1500, "utilities": 148, "food": 338, "transport": 100, "phone_internet": 65, "misc_basic": 128, "discretionary": 198},
    "Edmonton": {"rent": 1300, "utilities": 155, "food": 325, "transport": 95, "phone_internet": 65, "misc_basic": 122, "discretionary": 188},
    "Winnipeg": {"rent": 1150, "utilities": 145, "food": 312, "transport": 85, "phone_internet": 60, "misc_basic": 115, "discretionary": 175},
    "Quebec City": {"rent": 1150, "utilities": 140, "food": 310, "transport": 82, "phone_internet": 60, "misc_basic": 112, "discretionary": 172},
    "Hamilton": {"rent": 1300, "utilities": 145, "food": 320, "transport": 88, "phone_internet": 65, "misc_basic": 118, "discretionary": 182},
    "Waterloo": {"rent": 1300, "utilities": 142, "food": 318, "transport": 85, "phone_internet": 65, "misc_basic": 116, "discretionary": 178},
    "Kingston": {"rent": 1200, "utilities": 140, "food": 308, "transport": 80, "phone_internet": 60, "misc_basic": 112, "discretionary": 172},
    "Halifax": {"rent": 1200, "utilities": 142, "food": 310, "transport": 82, "phone_internet": 60, "misc_basic": 112, "discretionary": 172},
    "Victoria": {"rent": 1700, "utilities": 140, "food": 348, "transport": 88, "phone_internet": 65, "misc_basic": 130, "discretionary": 200},
    "London": {"rent": 1150, "utilities": 140, "food": 308, "transport": 80, "phone_internet": 60, "misc_basic": 110, "discretionary": 168},
    "Saskatoon": {"rent": 1150, "utilities": 142, "food": 305, "transport": 78, "phone_internet": 60, "misc_basic": 108, "discretionary": 165},
    "Guelph": {"rent": 1250, "utilities": 142, "food": 315, "transport": 82, "phone_internet": 65, "misc_basic": 115, "discretionary": 175},
    "St. Catharines": {"rent": 1200, "utilities": 140, "food": 308, "transport": 78, "phone_internet": 60, "misc_basic": 110, "discretionary": 168},
    "Kelowna": {"rent": 1380, "utilities": 138, "food": 325, "transport": 82, "phone_internet": 65, "misc_basic": 118, "discretionary": 182},
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
            border-radius:16px;padding:1.8rem;margin-bottom:2rem;border:1px solid rgba(20,184,166,0.15);'>
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
    # Workflow diagram
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
        preset = CITY_EXPENSE_PRESETS.get(city, CITY_EXPENSE_PRESETS.get("St. Louis", next(iter(CITY_EXPENSE_PRESETS), {})))
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

        # Visual breakdown
        st.markdown("<div class='section-header'>Expense Distribution</div>", unsafe_allow_html=True)
        v1, v2 = st.columns([1, 1.2])
        with v1:
            labels = ["Rent", "Utilities", "Food", "Transport", "Phone/Internet", "Misc", "Discretionary", "Tuition"]
            values = [rent, utilities, food, transport, phone_internet, misc_basic, discretionary, tuition_monthly]
            fig_pie = px.pie(names=labels, values=values, hole=0.5, title="Monthly Outflows by Category",
                             color_discrete_sequence=[COLORS["red"], COLORS["gold"], COLORS["teal"], COLORS["blue"], COLORS["purple"], COLORS["green"], COLORS["slate"], "#475569"])
            fig_pie.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig_pie, use_container_width=True)
        with v2:
            # Waterfall chart
            fig_wf = go.Figure(go.Waterfall(
                name="Cash Flow", orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=["Total Inflows", "Fixed Expenses", "Variable Expenses", "Net Liquidity"],
                y=[total_income, -fixed_expenses, -variable_expenses, 0],
                connector=dict(line=dict(color=COLORS["slate"])),
                increasing=dict(marker=dict(color=COLORS["teal"])),
                decreasing=dict(marker=dict(color=COLORS["red"])),
                totals=dict(marker=dict(color=COLORS["gold"])),
            ))
            fig_wf.update_layout(title="Monthly Cash Flow Waterfall", **PLOT_LAYOUT)
            st.plotly_chart(fig_wf, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: SPENDING BREAKDOWN
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Spending Breakdown":
    st.markdown("<div class='page-title'>Spending Breakdown</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Detailed analysis of your fixed vs. variable spending.</div>", unsafe_allow_html=True)

    if not st.session_state["calc_ready"]:
        st.info("Run Cash Flow Analysis first to see your breakdown.")
        st.stop()

    rent = st.session_state["rent"]
    util = st.session_state["utilities"]
    food = st.session_state["food"]
    tran = st.session_state["transport"]
    phon = st.session_state["phone_internet"]
    misc = st.session_state["misc_basic"]
    disc = st.session_state["discretionary"]
    tuit = st.session_state["tuition_monthly"]
    inc  = st.session_state["income"]

    fixed = rent + util + phon + tuit
    variable = food + tran + misc + disc
    total = fixed + variable

    st.markdown("<div class='section-header'>Fixed vs. Variable Analysis</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Fixed Expenses** — {usd(fixed)} ({pct(fixed/total if total>0 else 0)} of total)")
        st.markdown(f"- Rent: {usd(rent)}")
        st.markdown(f"- Utilities: {usd(util)}")
        st.markdown(f"- Phone/Internet: {usd(phon)}")
        st.markdown(f"- Tuition: {usd(tuit)}")
    with c2:
        st.markdown(f"**Variable Expenses** — {usd(variable)} ({pct(variable/total if total>0 else 0)} of total)")
        st.markdown(f"- Food: {usd(food)}")
        st.markdown(f"- Transport: {usd(tran)}")
        st.markdown(f"- Essential Misc: {usd(misc)}")
        st.markdown(f"- Discretionary: {usd(disc)}")

    # Sunburst chart
    st.markdown("<div class='section-header'>Hierarchical Spending View</div>", unsafe_allow_html=True)
    data = {
        "labels": ["Total", "Fixed", "Variable", "Rent", "Utilities", "Phone", "Tuition", "Food", "Transport", "Misc", "Disc"],
        "parents": ["", "Total", "Total", "Fixed", "Fixed", "Fixed", "Fixed", "Variable", "Variable", "Variable", "Variable"],
        "values": [total, fixed, variable, rent, util, phon, tuit, food, tran, misc, disc]
    }
    fig_sun = go.Figure(go.Sunburst(labels=data["labels"], parents=data["parents"], values=data["values"], branchvalues="total"))
    fig_sun.update_layout(margin=dict(t=0, l=0, r=0, b=0), **PLOT_LAYOUT)
    st.plotly_chart(fig_sun, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4: FUTURE FORECAST
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Future Forecast":
    st.markdown("<div class='page-title'>Future Forecast</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Project your financial position over the next 12 months.</div>", unsafe_allow_html=True)

    if not st.session_state["calc_ready"]:
        st.info("Run Cash Flow Analysis first to see your forecast.")
        st.stop()

    bal = st.session_state["balance"]
    st.markdown("<div class='section-header'>12-Month Projection</div>", unsafe_allow_html=True)
    months = st.slider("Forecast Horizon (Months)", 1, 24, 12)
    
    # Starting balance input
    start_bal = st.number_input("Current Savings / Starting Balance ($)", min_value=0.0, value=2000.0, step=100.0)
    
    df_forecast = forecast_balance(start_bal, bal, months)
    
    fig_forecast = px.line(df_forecast, x="Month", y="Projected Balance", title="Projected Savings Growth (Inflation-Adjusted)")
    fig_forecast.add_hline(y=0, line_dash="dash", line_color="red")
    fig_forecast.update_traces(line_color=COLORS["teal"], mode="lines+markers")
    fig_forecast.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig_forecast, use_container_width=True)
    
    st.markdown("<div class='section-header'>Forecast Data</div>", unsafe_allow_html=True)
    st.dataframe(df_forecast, use_container_width=True)


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
    st.markdown("<div class='page-subtitle'>Compare the real cost of living across 126 cities in the US, UK, and Canada.</div>", unsafe_allow_html=True)

    from providers import metro_countries, metro_names_by_country, get_metro

    # ── Filters
    fg1, fg2 = st.columns([1, 3])
    with fg1:
        cg_country = st.selectbox("Country", metro_countries(), key="cg_country")
    with fg2:
        all_cg_metros = metro_names_by_country(cg_country)
        default_sel = all_cg_metros[:5] if len(all_cg_metros) >= 5 else all_cg_metros
        sel_cities = st.multiselect("Cities (select up to 10)", all_cg_metros, default=default_sel, key="cg_cities")

    if not sel_cities:
        st.info("Select at least one city to compare.")
        st.stop()

    # Build comparison dataframe from metro benchmarks
    rows = []
    for city_name in sel_cities:
        m = get_metro(city_name)
        if m:
            total_monthly = m.rent_shared + m.groceries + m.utilities + m.transport_monthly + m.internet + m.misc_basic + m.discretionary
            rows.append({
                "City": city_name,
                "Rent (Shared)": m.rent_shared,
                "Rent (1BR)": m.rent_1br,
                "Groceries": m.groceries,
                "Utilities": m.utilities,
                "Transport": m.transport_monthly,
                "Internet": m.internet,
                "Misc Essentials": m.misc_basic,
                "Discretionary": m.discretionary,
                "Total Monthly": total_monthly,
                "Cost Tier": m.cost_tier,
                "Transit Score": m.transit_score,
                "State/Region": m.state,
            })
    if not rows:
        st.warning("No benchmark data available for selected cities.")
        st.stop()

    cg_df = pd.DataFrame(rows)

    # ── KPI summary cards
    st.markdown("<div class='section-header'>Cost of Living Snapshot</div>", unsafe_allow_html=True)
    for _, row in cg_df.iterrows():
        with st.expander(f"📍 {row['City']} — {row['State/Region']} ({row['Cost Tier']})", expanded=len(sel_cities) <= 3):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Monthly Total", usd(row["Total Monthly"]))
            c2.metric("Rent (Shared)", usd(row["Rent (Shared)"]))
            c3.metric("Rent (1BR)", usd(row["Rent (1BR)"]))
            c4.metric("Groceries", usd(row["Groceries"]))
            c5.metric("Transit Score", f"{row['Transit Score']}/10")

    # ── Total monthly cost comparison bar chart
    st.markdown("<div class='section-header'>Monthly Cost Comparison</div>", unsafe_allow_html=True)
    cost_tier_order = {"Very Low": 1, "Low": 2, "Medium": 3, "High": 4, "Very High": 5}
    cg_df["Cost Tier Num"] = cg_df["Cost Tier"].map(cost_tier_order).fillna(3)
    fig_total = px.bar(
        cg_df.sort_values("Total Monthly"),
        x="City", y="Total Monthly",
        color="Cost Tier Num",
        color_continuous_scale=[[0, COLORS["teal"]], [0.5, COLORS["gold"]], [1, COLORS["red"]]],
        title="Estimated Total Monthly Cost (Shared Rent)",
        text="Total Monthly",
    )
    fig_total.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig_total.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig_total, use_container_width=True)

    # ── Expense breakdown stacked bar
    st.markdown("<div class='section-header'>Expense Breakdown by Category</div>", unsafe_allow_html=True)
    breakdown_cols = ["Rent (Shared)", "Groceries", "Utilities", "Transport", "Internet", "Misc Essentials", "Discretionary"]
    # ensure all breakdown cols exist
    breakdown_cols = [c for c in breakdown_cols if c in cg_df.columns]
    melted = cg_df[["City"] + breakdown_cols].melt(id_vars="City", var_name="Category", value_name="Amount")
    fig_breakdown = px.bar(
        melted, x="City", y="Amount", color="Category", barmode="stack",
        title="Monthly Expense Breakdown by City",
        color_discrete_sequence=[COLORS["red"], COLORS["gold"], COLORS["teal"], COLORS["blue"], COLORS["purple"], COLORS["green"], COLORS["slate"]],
    )
    fig_breakdown.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig_breakdown, use_container_width=True)

    # ── Rent burden analysis
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown("<div class='section-header'>Shared Rent vs. 1BR Rent</div>", unsafe_allow_html=True)
        rent_compare = cg_df[["City", "Rent (Shared)", "Rent (1BR)"]].melt(id_vars="City", var_name="Type", value_name="Rent")
        fig_rc = px.bar(
            rent_compare.sort_values("Rent"),
            x="City", y="Rent", color="Type", barmode="group",
            title="Shared vs. 1BR Monthly Rent by City",
            color_discrete_map={"Rent (Shared)": COLORS["teal"], "Rent (1BR)": COLORS["gold"]},
        )
        fig_rc.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(fig_rc, use_container_width=True)
    with ch2:
        st.markdown("<div class='section-header'>Transit Score by City</div>", unsafe_allow_html=True)
        fig_ts = px.bar(
            cg_df.sort_values("Transit Score", ascending=False),
            x="City", y="Transit Score",
            color="Transit Score",
            color_continuous_scale=[[0, COLORS["red"]], [0.5, COLORS["gold"]], [1, COLORS["teal"]]],
            title="Public Transit Score (10 = Best)",
        )
        fig_ts.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(fig_ts, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 7: DECISION PLANNER
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Decision Planner":
    page_decision_planner()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 8: COMPARE OFFERS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Compare Offers":
    page_admit_comparison()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 9: STRESS TEST
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Stress Test":
    page_stress_test()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 10: MOVE-IN PLANNER
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Move-In Planner":
    page_movein_shock()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 11: HOW IT WORKS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "How It Works":
    st.markdown("<div class='page-title'>How CostCompass Works</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Transparency in our data and methodology.</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Our Mission</div>", unsafe_allow_html=True)
    st.markdown("CostCompass was built to solve a specific problem: international students often arrive in a new country with an incomplete understanding of their real daily costs. We provide data-driven transparency to help you plan with confidence.")

    st.markdown("<div class='section-header'>Data Sources</div>", unsafe_allow_html=True)
    st.markdown("""
- **Cost of Living:** Aggregated from Numbeo, Expatistan, and local government statistics (BLS, ONS, StatCan).
- **Rent Benchmarks:** Derived from Zillow, Rightmove, and Rentals.ca market reports.
- **Wages:** Based on statutory minimum wages for international students (20h/week limit).
""")

    st.markdown("<div class='section-header'>Financial Health Logic</div>", unsafe_allow_html=True)
    st.markdown("Our **Financial Stability Indicator** (0-100) is calculated based on four weighted pillars:")
    st.markdown("""
1. **Net Liquidity (40%):** Is your monthly cash flow positive?
2. **Rent Burden (25%):** Is your rent under 30% of your income?
3. **Savings Rate (20%):** Are you building a buffer of at least 10%?
4. **Emergency Runway (15%):** Do you have at least 3 months of coverage?
""")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 12: SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Settings":
    st.markdown("<div class='page-title'>Settings</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Personalise CostCompass to match your situation.</div>", unsafe_allow_html=True)

    with st.form("settings_form"):
        st.markdown("<div class='section-header'>Your Profile</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            home_country = st.selectbox("Home country", ["Ghana", "Nigeria", "India", "China", "Other"])
        with c2:
            default_city = st.selectbox("Default city", list(CITY_MIN_WAGE.keys()), index=list(CITY_MIN_WAGE.keys()).index("St. Louis") if "St. Louis" in CITY_MIN_WAGE else 0)

        st.markdown("<div class='section-header'>Currency & FX</div>", unsafe_allow_html=True)
        f1, f2 = st.columns(2)
        with f1:
            home_currency = st.selectbox("Home currency", ["GHS (Ghana Cedi)", "NGN (Nigerian Naira)", "INR (Indian Rupee)", "CNY (Chinese Yuan)", "Other"])
        with f2:
            fx_rate = st.number_input("Exchange rate (1 home unit = ? USD)", value=0.067, format="%.4f")

        st.markdown("<div class='section-header'>Display</div>", unsafe_allow_html=True)
        d1, d2 = st.columns(2)
        with d1:
            show_tips = st.toggle("Show financial tips on dashboard", value=True)
        with d2:
            compact_mode = st.toggle("Compact mode (fewer charts)", value=False)

        st.markdown("<div class='section-header'>Data</div>", unsafe_allow_html=True)
        reset_data = st.checkbox("I want to reset all my saved data")

        save = st.form_submit_button("Save Settings", use_container_width=True)
        if save:
            if reset_data:
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
            st.success("Settings saved successfully!")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<hr class='soft'>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align:center; padding: 1rem 0;'>
    <div style='font-size:0.75rem; color:#475569;'>
        CostCompass v3.0 · Built by Joseph Amegashie · <a href='mailto:amegashie@wustl.edu' style='color:#14b8a6; text-decoration:none;'>amegashie@wustl.edu</a>
    </div>
    <div class='disclaimer'>
        Disclaimer: CostCompass provides estimates based on market benchmarks. Actual costs may vary significantly based on lifestyle, specific neighborhood, and inflation. This tool is for planning purposes and does not constitute professional financial advice.
    </div>
</div>
""", unsafe_allow_html=True)
