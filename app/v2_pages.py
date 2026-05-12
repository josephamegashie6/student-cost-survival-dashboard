"""
v2_pages.py — V2/V3 Decision Tool Pages  (Pass 2)
CostCompass — Plan. Manage. Thrive.

Pages:
  - Decision Planner      (+ FX risk toggle)
  - Admit Comparison      (+ PDF export)
  - Stress Test
  - Move-In Shock Calculator

Pass 2 additions:
  - Entry-screen decision flow (4-path landing on Overview)
  - FX depreciation risk toggle in Decision Planner
  - Admit Comparison PDF memo export
  - Session-persistent saved plans (survives page navigation)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data_model import (
    PlanningScenario, FundingInputs, LivingCosts, MoveInCosts
)
from decision_engine import evaluate_scenario
from providers import (
    metro_names, university_names, get_metro, get_university,
    metro_names_by_country, university_names_by_country, metro_countries, university_countries
)

# ─── shared style helpers
TEAL   = "#14b8a6"
GOLD   = "#f59e0b"
GREEN  = "#10b981"
RED    = "#ef4444"
NAVY   = "#050a14"
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(5,10,20,0.6)",
    font=dict(color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(gridcolor="rgba(30,40,64,0.5)", showgrid=True),
    yaxis=dict(gridcolor="rgba(30,40,64,0.5)", showgrid=True),
)

def usd(x):
    if x is None: return "—"
    return f"${x:,.0f}" if x >= 0 else f"-${abs(x):,.0f}"

def score_color(s):
    if s >= 75: return GREEN
    if s >= 55: return GOLD
    if s >= 35: return "#f97316"
    return RED

def score_label(s):
    if s >= 75: return "Strong"
    if s >= 55: return "Viable"
    if s >= 35: return "Fragile"
    return "Critical"

def flag_icon(severity):
    return {"danger": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")

def flag_bg(severity):
    return {
        "danger":  "rgba(239,68,68,0.08)",
        "warning": "rgba(245,158,11,0.08)",
        "info":    "rgba(20,184,166,0.08)",
    }.get(severity, "rgba(255,255,255,0.04)")

def flag_border(severity):
    return {
        "danger":  "rgba(239,68,68,0.35)",
        "warning": "rgba(245,158,11,0.35)",
        "info":    "rgba(20,184,166,0.35)",
    }.get(severity, "rgba(255,255,255,0.1)")

def flag_text(severity):
    return {"danger": "#f87171", "warning": "#fbbf24", "info": "#2dd4bf"}.get(severity, "#94a3b8")

def render_flag(flag):
    st.markdown(f"""
    <div style='background:{flag_bg(flag.severity)};border:1px solid {flag_border(flag.severity)};
    border-radius:8px;padding:0.6rem 1rem;margin:0.35rem 0;
    color:{flag_text(flag.severity)};font-size:0.88rem;line-height:1.5;'>
        {flag_icon(flag.severity)} {flag.message}
    </div>""", unsafe_allow_html=True)

def kpi(label, value, sub=None, color=TEAL):
    sub_html = f"<div style='font-size:0.78rem;color:#64748b;margin-top:0.15rem;'>{sub}</div>" if sub else ""
    return f"""
    <div style='background:rgba(10,20,40,0.9);border:1px solid rgba(20,184,166,0.2);
    border-radius:12px;padding:1rem 1.2rem;margin-bottom:0.8rem;'>
        <div style='font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;'>{label}</div>
        <div style='font-size:1.55rem;font-weight:700;color:{color};margin:0.2rem 0;'>{value}</div>
        {sub_html}
    </div>"""

def section(title):
    st.markdown(f"""
    <div style='background:linear-gradient(90deg,rgba(20,184,166,0.12) 0%,rgba(5,10,20,0) 100%);
    border-left:3px solid #14b8a6;padding:0.5rem 1rem;border-radius:0 8px 8px 0;
    margin-bottom:1rem;font-size:1.05rem;font-weight:600;letter-spacing:0.04em;color:#e2e8f0;'>
        {title}
    </div>""", unsafe_allow_html=True)

def advisor_box(text):
    st.markdown(f"""
    <div style='background:rgba(20,184,166,0.06);border:1px solid rgba(20,184,166,0.25);
    border-radius:10px;padding:1.1rem 1.4rem;margin:0.8rem 0;
    font-size:0.92rem;color:#cbd5e1;line-height:1.7;font-style:italic;'>
        💬 {text}
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
def init_v2_state():
    if "v2_saved_scenarios" not in st.session_state:
        st.session_state["v2_saved_scenarios"] = []   # list of (PlanningScenario, DecisionResult)
    if "v2_current_result" not in st.session_state:
        st.session_state["v2_current_result"] = None
    if "v2_current_scenario" not in st.session_state:
        st.session_state["v2_current_scenario"] = None
    # Entry screen: which path was chosen
    if "v2_entry_path" not in st.session_state:
        st.session_state["v2_entry_path"] = None

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY SCREEN — 4-path decision flow (called from Overview page)
# ─────────────────────────────────────────────────────────────────────────────
def render_entry_screen():
    """
    Renders the 4-path decision entry screen at the bottom of the Overview page.
    Each path pre-routes the user to the right tool with context.
    """
    init_v2_state()
    st.markdown("""
    <div style='margin-top:2rem;margin-bottom:0.5rem;'>
        <div style='font-size:1.3rem;font-weight:700;color:#f8fafc;letter-spacing:0.03em;'>
            What do you need to figure out?
        </div>
        <div style='font-size:0.88rem;color:#64748b;margin-top:0.3rem;'>
            Choose your question — we'll take you to the right tool.
        </div>
    </div>""", unsafe_allow_html=True)

    paths = [
        {
            "icon": "🏙️",
            "title": "Can I afford this city?",
            "desc": "Check if your funding covers living costs in a specific metro area.",
            "route": "Decision Planner",
            "key": "entry_city",
            "color": TEAL,
        },
        {
            "icon": "🏠",
            "title": "How much rent can I safely pay?",
            "desc": "Find your safe rent ceiling based on your income and expenses.",
            "route": "Decision Planner",
            "key": "entry_rent",
            "color": GREEN,
        },
        {
            "icon": "🎓",
            "title": "Which school is financially better?",
            "desc": "Compare two or more admit offers side by side with stress testing.",
            "route": "Compare Offers",
            "key": "entry_compare",
            "color": GOLD,
        },
        {
            "icon": "⚡",
            "title": "What if my funding changes?",
            "desc": "Run a stress test to see how rent increases or income cuts affect your plan.",
            "route": "Stress Test",
            "key": "entry_stress",
            "color": "#f97316",
        },
    ]

    cols = st.columns(4, gap="small")
    for i, (col, path) in enumerate(zip(cols, paths)):
        with col:
            st.markdown(f"""
            <div style='background:rgba(10,20,40,0.9);border:1px solid rgba(20,184,166,0.15);
            border-radius:14px;padding:1.2rem 1rem;text-align:center;min-height:160px;
            transition:border-color 0.2s;'>
                <div style='font-size:2rem;margin-bottom:0.5rem;'>{path["icon"]}</div>
                <div style='font-size:0.9rem;font-weight:700;color:#e2e8f0;margin-bottom:0.4rem;
                line-height:1.3;'>{path["title"]}</div>
                <div style='font-size:0.78rem;color:#64748b;line-height:1.45;'>{path["desc"]}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Go →", key=path["key"], use_container_width=True):
                st.session_state["v2_entry_path"] = path["route"]
                st.session_state["_nav_target"] = path["route"]
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# FX RISK ANALYSIS helper
# ─────────────────────────────────────────────────────────────────────────────
def render_fx_risk_section(home_currency_monthly: float, fx_rate: float, monthly_income: float, monthly_surplus: float):
    """
    Shows how FX depreciation affects the plan when the user has home currency funding.
    """
    if home_currency_monthly <= 0 or fx_rate <= 0:
        return

    section("FX Depreciation Risk")
    st.markdown("""
    <div style='font-size:0.85rem;color:#64748b;margin-bottom:1rem;'>
    Your plan includes home currency funding. This section shows how currency depreciation
    affects your monthly income and surplus.
    </div>""", unsafe_allow_html=True)

    usd_from_home = home_currency_monthly * fx_rate
    depreciation_levels = [0, 5, 10, 15, 20, 30, 40]
    rows = []
    for pct in depreciation_levels:
        new_rate = fx_rate * (1 - pct / 100)
        new_usd = home_currency_monthly * new_rate
        income_change = new_usd - usd_from_home
        new_income = monthly_income + income_change
        new_surplus = monthly_surplus + income_change
        rows.append({
            "Depreciation": f"{pct}%",
            "New Rate": f"{new_rate:.4f}",
            "USD from Home": usd(new_usd),
            "Monthly Income": usd(new_income),
            "Monthly Surplus": usd(new_surplus),
            "Status": "✅ Viable" if new_surplus >= 0 else "❌ Deficit",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Chart
    surpluses = []
    for pct in depreciation_levels:
        new_rate = fx_rate * (1 - pct / 100)
        new_usd = home_currency_monthly * new_rate
        income_change = new_usd - usd_from_home
        surpluses.append(monthly_surplus + income_change)

    colors_list = [GREEN if s >= 0 else RED for s in surpluses]
    fig = go.Figure(go.Bar(
        x=[f"{p}%" for p in depreciation_levels],
        y=surpluses,
        marker_color=colors_list,
        text=[usd(s) for s in surpluses],
        textposition="outside",
    ))
    fig.add_hline(y=0, line_color=RED, line_dash="dash", line_width=1.5)
    fig.update_layout(
        title="Monthly Surplus Under FX Depreciation Scenarios",
        xaxis_title="Home Currency Depreciation",
        yaxis_title="Monthly Surplus (USD)",
        **PLOT_LAYOUT
    )
    st.plotly_chart(fig, use_container_width=True)

    # Advisor note
    breakeven_pct = None
    for pct in depreciation_levels:
        new_rate = fx_rate * (1 - pct / 100)
        new_usd = home_currency_monthly * new_rate
        income_change = new_usd - usd_from_home
        if monthly_surplus + income_change < 0:
            breakeven_pct = pct
            break

    if breakeven_pct:
        advisor_box(
            f"Your plan breaks under a {breakeven_pct}% depreciation of your home currency. "
            f"If you are funded from {['GHS', 'NGN', 'KES', 'GHC', 'home currency'][0]}, "
            f"monitor exchange rate movements closely. A {breakeven_pct}% move is not unusual over a 12-month period. "
            f"Consider converting a portion of your savings to USD before arrival to reduce this exposure."
        )
    else:
        advisor_box(
            f"Your plan remains viable even under a 40% depreciation of your home currency. "
            f"Your USD income sources provide sufficient buffer against FX risk."
        )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DECISION PLANNER
# ─────────────────────────────────────────────────────────────────────────────
def page_decision_planner():
    init_v2_state()
    st.markdown("<div style='font-size:1.55rem;font-weight:700;color:#f8fafc;letter-spacing:0.03em;margin-bottom:0.25rem;'>Decision Planner</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.88rem;color:#94a3b8;margin-bottom:1.2rem;'>Build a financial plan for one school or city. Get a bottom-line recommendation, safe rent ceiling, and risk assessment.</div>", unsafe_allow_html=True)

    all_countries = metro_countries()
    all_uni_countries = university_countries()

    # ── Planning mode
    mode = st.radio("Planning mode", ["By University", "By City / Metro"], horizontal=True)
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        section("Location & School")
        label = st.text_input("Plan label (e.g. WashU Option A)", value="My Plan")
        if mode == "By University":
            uni_country = st.selectbox("Country", all_uni_countries, key="dp_uni_country")
            unis = university_names_by_country(uni_country)
            uni_name = st.selectbox("University", unis, key="dp_uni_name")
            uni = get_university(uni_name)
            if uni:
                metro_default = uni.metro
                st.markdown(f"<div style='font-size:0.8rem;color:#64748b;margin-top:-0.5rem;margin-bottom:0.8rem;'>📍 {uni.metro}, {uni.state} · {uni.program_type} · I-20 estimate: {usd(uni.i20_cost_estimate)}</div>", unsafe_allow_html=True)
                if uni.notes:
                    st.markdown(f"<div style='font-size:0.78rem;color:#475569;margin-bottom:0.8rem;font-style:italic;'>{uni.notes}</div>", unsafe_allow_html=True)
            else:
                metros = metro_names()
                metro_default = metros[0]
            metro_name = metro_default
        else:
            uni = None
            metro_country = st.selectbox("Country", all_countries, key="dp_metro_country")
            metros = metro_names_by_country(metro_country)
            metro_name = st.selectbox("Metro / City", metros, key="dp_metro_name")

        metro = get_metro(metro_name)

        section("Funding")
        has_assistantship = st.checkbox("I have (or expect) an assistantship / TA / RA", value=False)
        tuition_covered = False
        if has_assistantship and uni:
            default_stipend = round(uni.assistantship_stipend_annual / 12, 0)
            tuition_covered = st.checkbox("Assistantship covers tuition", value=uni.assistantship_covers_tuition)
        elif has_assistantship:
            default_stipend = 1800.0
        else:
            default_stipend = 0.0

        stipend = st.number_input("Monthly stipend / assistantship ($)", min_value=0.0, value=float(default_stipend), step=100.0)
        wage = st.number_input("Hourly wage from on-campus job ($)", min_value=0.0, value=12.50, step=0.50)
        hours = st.number_input("Weekly work hours (F-1 max: 20 during semester)", min_value=0.0, max_value=40.0, value=15.0, step=1.0)
        family = st.number_input("Monthly family support ($)", min_value=0.0, value=0.0, step=50.0)

        st.markdown("**Foreign currency funding (optional)**")
        fx_col1, fx_col2 = st.columns(2)
        with fx_col1:
            home_currency = st.number_input("Amount in home currency (monthly)", min_value=0.0, value=0.0, step=100.0)
        with fx_col2:
            fx_rate = st.number_input("Exchange rate (1 home unit = ? USD)", min_value=0.01, value=1.0, step=0.01)

        # FX risk toggle
        show_fx_risk = False
        if home_currency > 0:
            show_fx_risk = st.checkbox("Show FX depreciation risk analysis", value=True,
                                        help="See how your plan changes if your home currency loses value against USD")

        starting_cash = st.number_input("Cash available before arrival ($)", min_value=0.0, value=5000.0, step=500.0)

    with col_right:
        section("Living Costs")
        if metro:
            st.markdown(f"<div style='font-size:0.8rem;color:#64748b;margin-bottom:0.6rem;'>Defaults loaded from {metro.metro} benchmark (Cost tier: {metro.cost_tier})</div>", unsafe_allow_html=True)

        housing_type = st.radio("Housing type", ["Shared / Roommate", "Studio", "1-Bedroom"], horizontal=True)
        if metro:
            rent_default = {"Shared / Roommate": metro.rent_shared, "Studio": metro.rent_studio, "1-Bedroom": metro.rent_1br}[housing_type]
        else:
            rent_default = 900.0
        has_roommate = housing_type == "Shared / Roommate"

        rent = st.number_input("Monthly rent ($)", min_value=0.0, value=float(rent_default), step=50.0)
        groceries = st.number_input("Groceries ($)", min_value=0.0, value=float(metro.groceries if metro else 320.0), step=10.0)
        utilities = st.number_input("Utilities ($)", min_value=0.0, value=float(metro.utilities if metro else 120.0), step=10.0)
        transport = st.number_input("Transport / transit ($)", min_value=0.0, value=float(metro.transport_monthly if metro else 65.0), step=10.0)
        internet = st.number_input("Internet / phone ($)", min_value=0.0, value=float(metro.internet if metro else 65.0), step=5.0)
        misc = st.number_input("Misc / personal care ($)", min_value=0.0, value=float(metro.misc_basic if metro else 120.0), step=10.0)
        discretionary = st.number_input("Discretionary / social ($)", min_value=0.0, value=float(metro.discretionary if metro else 180.0), step=10.0)
        has_car = st.checkbox("I will have a car (adds ~$350-500/mo in insurance, gas, parking)")

        section("Academic Costs")
        if uni and not tuition_covered:
            tuition_annual_default = uni.tuition_annual + uni.fees_annual
            health_default = round(uni.health_insurance_annual / 12, 0)
        elif uni and tuition_covered:
            tuition_annual_default = 0.0
            health_default = round(uni.health_insurance_annual / 12, 0)
            st.markdown("<div style='font-size:0.8rem;color:#10b981;margin-bottom:0.5rem;'>✓ Assistantship covers tuition — set to $0</div>", unsafe_allow_html=True)
        else:
            tuition_annual_default = 0.0
            health_default = 250.0

        tuition_monthly = st.number_input("Monthly tuition allocation ($)", min_value=0.0, value=float(round(tuition_annual_default / 12, 0)), step=50.0)
        health_monthly = st.number_input("Health insurance (monthly)", min_value=0.0, value=float(health_default), step=10.0)

    # ── Run engine
    st.markdown("---")
    run_col, save_col = st.columns([1, 1])
    with run_col:
        run = st.button("▶  Run Decision Analysis", type="primary", use_container_width=True)
    with save_col:
        save = st.button("＋  Save to Comparison", use_container_width=True)

    if run or save:
        funding = FundingInputs(
            monthly_stipend=stipend,
            hourly_wage=wage,
            weekly_work_hours=hours,
            family_support_monthly=family,
            home_currency_monthly=home_currency,
            fx_rate=fx_rate,
            has_assistantship=has_assistantship,
            tuition_covered_by_aid=tuition_covered,
        )
        living = LivingCosts(
            rent=rent,
            groceries=groceries,
            utilities=utilities,
            transport=transport,
            internet=internet,
            misc_basic=misc,
            discretionary=discretionary,
            health_insurance_monthly=health_monthly,
            tuition_monthly=tuition_monthly,
        )
        move_in = MoveInCosts(
            housing_deposit=rent,
            first_last_rent=rent * 2,
        )
        scenario = PlanningScenario(
            label=label,
            university=uni.university if uni else None,
            metro=metro_name,
            state=metro.state if metro else "",
            funding=funding,
            living=living,
            move_in=move_in,
            starting_cash=starting_cash,
            has_roommate=has_roommate,
            has_car=has_car,
        )
        result = evaluate_scenario(scenario)
        st.session_state["v2_current_result"] = result
        st.session_state["v2_current_scenario"] = scenario

        if save:
            existing_labels = [r.scenario_label for _, r in st.session_state["v2_saved_scenarios"]]
            if result.scenario_label not in existing_labels:
                st.session_state["v2_saved_scenarios"].append((scenario, result))
                st.success(f"'{label}' saved to Admit Comparison.")
            else:
                st.warning(f"A scenario named '{label}' is already saved. Rename it to save a new version.")

    result = st.session_state.get("v2_current_result")
    scenario_obj = st.session_state.get("v2_current_scenario")
    if not result:
        return

    st.markdown("---")
    section("Decision Output")

    # KPI row 1
    k1, k2, k3, k4 = st.columns(4)
    aff_color = score_color(result.affordability_score)
    with k1:
        st.markdown(kpi("Affordability Score", f"{result.affordability_score}/100", score_label(result.affordability_score), aff_color), unsafe_allow_html=True)
    with k2:
        surplus_color = GREEN if result.monthly_surplus >= 150 else (GOLD if result.monthly_surplus >= 0 else RED)
        st.markdown(kpi("Monthly Surplus", usd(result.monthly_surplus), "After all expenses", surplus_color), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi("Safe Rent Ceiling", usd(result.safe_rent_ceiling), "30% of income rule", TEAL), unsafe_allow_html=True)
    with k4:
        runway_color = GREEN if result.emergency_runway_months >= 3 else (GOLD if result.emergency_runway_months >= 2 else RED)
        st.markdown(kpi("Cash Runway", f"{result.emergency_runway_months:.1f} mo", "After move-in", runway_color), unsafe_allow_html=True)

    # KPI row 2
    k5, k6, k7, k8 = st.columns(4)
    with k5:
        st.markdown(kpi("Monthly Income", usd(result.monthly_income), "All sources", TEAL), unsafe_allow_html=True)
    with k6:
        st.markdown(kpi("Monthly Expenses", usd(result.monthly_expenses), "All categories", GOLD), unsafe_allow_html=True)
    with k7:
        st.markdown(kpi("Move-In Cash Needed", usd(result.move_in_cash_required), "Before arrival", GOLD), unsafe_allow_html=True)
    with k8:
        cash_color = GREEN if result.starting_cash_after_movein >= 0 else RED
        st.markdown(kpi("Cash After Move-In", usd(result.starting_cash_after_movein), "Starting balance", cash_color), unsafe_allow_html=True)

    # Advisor recommendation
    section("Advisor Recommendation")
    advisor_box(result.recommendation)

    # Stress test summary
    section("Stress Scenarios")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(kpi("Baseline Surplus", usd(result.monthly_surplus), "Current assumptions", GREEN if result.monthly_surplus >= 0 else RED), unsafe_allow_html=True)
    with sc2:
        mod_color = GREEN if result.stress_moderate >= 0 else RED
        st.markdown(kpi("Moderate Stress", usd(result.stress_moderate), "Rent +8%, income -10%", mod_color), unsafe_allow_html=True)
    with sc3:
        sev_color = GREEN if result.stress_severe >= 0 else RED
        st.markdown(kpi("Severe Stress", usd(result.stress_severe), "Rent +15%, income -25%", sev_color), unsafe_allow_html=True)

    # Cash runway chart
    section("12-Month Cash Projection")
    months = list(range(0, 13))
    cash_vals = [max(0, result.starting_cash_after_movein + result.monthly_surplus * m) for m in months]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=cash_vals,
        mode="lines+markers",
        name="Cash Balance",
        line=dict(color=TEAL, width=2.5),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(20,184,166,0.08)",
    ))
    fig.add_hline(y=0, line_color=RED, line_dash="dash", line_width=1.5, annotation_text="Zero", annotation_position="bottom right")
    fig.update_layout(title="Projected Cash Balance (12 months)", xaxis_title="Month", yaxis_title="USD", **PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # FX risk section (only shown when user has home currency funding and toggle is on)
    if show_fx_risk and scenario_obj:
        render_fx_risk_section(
            home_currency_monthly=scenario_obj.funding.home_currency_monthly,
            fx_rate=scenario_obj.funding.fx_rate,
            monthly_income=result.monthly_income,
            monthly_surplus=result.monthly_surplus,
        )

    # Risk flags
    if result.risk_flags:
        section("Risk Flags")
        for flag in result.risk_flags:
            render_flag(flag)

    # Cash negative warning
    if result.cash_negative_month:
        st.markdown(f"""
        <div style='background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.4);
        border-radius:8px;padding:0.8rem 1.2rem;margin:0.5rem 0;color:#f87171;font-size:0.9rem;'>
            ⚠️ At current burn rate, your cash balance goes negative around <strong>month {result.cash_negative_month}</strong>.
            Additional funding, reduced spending, or a higher-stipend option is required.
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: ADMIT COMPARISON
# ─────────────────────────────────────────────────────────────────────────────
def page_admit_comparison():
    init_v2_state()
    st.markdown("<div style='font-size:1.55rem;font-weight:700;color:#f8fafc;letter-spacing:0.03em;margin-bottom:0.25rem;'>Admit Comparison</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.88rem;color:#94a3b8;margin-bottom:1.2rem;'>Compare saved financial plans side by side. Save plans from the Decision Planner first.</div>", unsafe_allow_html=True)

    saved = st.session_state.get("v2_saved_scenarios", [])

    # Session persistence info
    n_saved = len(saved)
    if n_saved > 0:
        st.markdown(f"""
        <div style='background:rgba(20,184,166,0.06);border:1px solid rgba(20,184,166,0.2);
        border-radius:8px;padding:0.6rem 1rem;margin-bottom:1rem;font-size:0.85rem;color:#94a3b8;'>
            📋 {n_saved} plan{"s" if n_saved != 1 else ""} saved this session:
            {" · ".join(f"<strong style='color:#14b8a6;'>{r.scenario_label}</strong>" for _, r in saved)}
        </div>""", unsafe_allow_html=True)

    if not saved:
        st.markdown("""
        <div style='background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.2);
        border-radius:10px;padding:1.5rem;text-align:center;color:#94a3b8;'>
            <div style='font-size:1.5rem;margin-bottom:0.5rem;'>📊</div>
            <div style='font-size:0.95rem;'>No plans saved yet.</div>
            <div style='font-size:0.85rem;margin-top:0.3rem;'>
                Go to <strong>Decision Planner</strong>, build a scenario, and click
                <strong>＋ Save to Comparison</strong>.
        </div>""", unsafe_allow_html=True)
        return

    results = [r for _, r in saved]
    labels = [r.scenario_label for r in results]

    # Action buttons row
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
    with btn_col1:
        if st.button("🗑  Clear all saved scenarios"):
            st.session_state["v2_saved_scenarios"] = []
            st.rerun()
    with btn_col2:
        # PDF export
        try:
            from pdf_export import generate_admit_comparison_pdf
            pdf_bytes = generate_admit_comparison_pdf(saved)
            st.download_button(
                label="📄  Export PDF Memo",
                data=pdf_bytes,
                file_name="admit_comparison_memo.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.caption(f"PDF export unavailable: {e}")

    section("Side-by-Side Comparison")
    rows = {
        "Monthly Income":       [usd(r.monthly_income) for r in results],
        "Monthly Expenses":     [usd(r.monthly_expenses) for r in results],
        "Monthly Surplus":      [usd(r.monthly_surplus) for r in results],
        "Affordability Score":  [f"{r.affordability_score}/100 ({score_label(r.affordability_score)})" for r in results],
        "Safe Rent Ceiling":    [usd(r.safe_rent_ceiling) for r in results],
        "Move-In Cash Needed":  [usd(r.move_in_cash_required) for r in results],
        "Cash After Move-In":   [usd(r.starting_cash_after_movein) for r in results],
        "Emergency Runway":     [f"{r.emergency_runway_months:.1f} months" for r in results],
        "Moderate Stress":      [usd(r.stress_moderate) for r in results],
        "Severe Stress":        [usd(r.stress_severe) for r in results],
        "Plan Viable":          ["✅ Yes" if r.plan_viable else "❌ No" for r in results],
    }
    df = pd.DataFrame(rows, index=labels).T
    df.index.name = "Metric"
    st.dataframe(df, use_container_width=True)

    # Ranking
    section("Ranking by Affordability Score")
    ranked = sorted(results, key=lambda r: r.affordability_score, reverse=True)
    for i, r in enumerate(ranked):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
        color = score_color(r.affordability_score)
        st.markdown(f"""
        <div style='background:rgba(10,20,40,0.9);border:1px solid rgba(20,184,166,0.15);
        border-radius:10px;padding:0.9rem 1.2rem;margin-bottom:0.6rem;
        display:flex;justify-content:space-between;align-items:center;'>
            <div>
                <span style='font-size:1.1rem;'>{medal}</span>
                <span style='font-size:1rem;font-weight:600;color:#e2e8f0;margin-left:0.6rem;'>{r.scenario_label}</span>
            </div>
            <div>
                <span style='font-size:1.2rem;font-weight:700;color:{color};'>{r.affordability_score}/100</span>
                <span style='font-size:0.8rem;color:#64748b;margin-left:0.5rem;'>{score_label(r.affordability_score)}</span>
            </div>
        </div>""", unsafe_allow_html=True)

    # Surplus comparison chart
    section("Monthly Surplus Comparison")
    surplus_vals = [r.monthly_surplus for r in results]
    colors_list = [GREEN if v >= 0 else RED for v in surplus_vals]
    fig = go.Figure(go.Bar(
        x=labels,
        y=surplus_vals,
        marker_color=colors_list,
        text=[usd(v) for v in surplus_vals],
        textposition="outside",
    ))
    fig.add_hline(y=0, line_color=RED, line_dash="dash", line_width=1)
    fig.update_layout(title="Monthly Surplus by Option", yaxis_title="USD", **PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # Stress comparison chart
    section("Stress Test Comparison")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Baseline", x=labels, y=[r.monthly_surplus for r in results], marker_color=TEAL))
    fig2.add_trace(go.Bar(name="Moderate Stress", x=labels, y=[r.stress_moderate for r in results], marker_color=GOLD))
    fig2.add_trace(go.Bar(name="Severe Stress", x=labels, y=[r.stress_severe for r in results], marker_color=RED))
    fig2.add_hline(y=0, line_color="#475569", line_dash="dash", line_width=1)
    fig2.update_layout(barmode="group", title="Surplus Under Stress Scenarios", yaxis_title="USD", **PLOT_LAYOUT)
    st.plotly_chart(fig2, use_container_width=True)

    # Advisor summary
    section("Advisor Summary")
    best = ranked[0]
    worst = ranked[-1]
    if len(ranked) > 1:
        gap = best.monthly_surplus - worst.monthly_surplus
        advisor_box(
            f"Based on your saved options, **{best.scenario_label}** is the strongest financial choice "
            f"with an affordability score of {best.affordability_score}/100 and a monthly surplus of {usd(best.monthly_surplus)}. "
            f"It outperforms **{worst.scenario_label}** by {usd(gap)} per month in baseline surplus. "
            f"{'All options hold under moderate stress.' if all(r.stress_moderate >= 0 for r in results) else 'Some options break under moderate stress — review carefully before committing.'}"
        )
    else:
        advisor_box(best.recommendation)

    # Individual recommendations
    section("Individual Recommendations")
    for scenario, result in saved:
        with st.expander(f"{result.scenario_label} — {result.affordability_score}/100"):
            advisor_box(result.recommendation)
            for flag in result.risk_flags:
                render_flag(flag)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: STRESS TEST
# ─────────────────────────────────────────────────────────────────────────────
def page_stress_test():
    init_v2_state()
    st.markdown("<div style='font-size:1.55rem;font-weight:700;color:#f8fafc;letter-spacing:0.03em;margin-bottom:0.25rem;'>Stress Test</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.88rem;color:#94a3b8;margin-bottom:1.2rem;'>Apply custom shocks to your financial plan and see how your surplus and cash position change.</div>", unsafe_allow_html=True)

    saved = st.session_state.get("v2_saved_scenarios", [])
    current_result = st.session_state.get("v2_current_result")
    current_scenario = st.session_state.get("v2_current_scenario")

    if not current_result and not saved:
        st.markdown("""
        <div style='background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.2);
        border-radius:10px;padding:1.5rem;text-align:center;color:#94a3b8;'>
            <div style='font-size:1.5rem;margin-bottom:0.5rem;'>⚡</div>
            <div style='font-size:0.95rem;'>No plan loaded yet.</div>
            <div style='font-size:0.85rem;margin-top:0.3rem;'>
                Run an analysis in <strong>Decision Planner</strong> first, then return here.
            </div>
        </div>""", unsafe_allow_html=True)
        return

    # Select which plan to stress test
    options = []
    if current_result:
        options.append(f"Current: {current_result.scenario_label}")
    for _, r in saved:
        if not current_result or r.scenario_label != current_result.scenario_label:
            options.append(r.scenario_label)

    selected_label = st.selectbox("Select plan to stress test", options)
    if selected_label.startswith("Current: "):
        base_result = current_result
        base_scenario = current_scenario
    else:
        matches = [(s, r) for s, r in saved if r.scenario_label == selected_label]
        if matches:
            base_scenario, base_result = matches[0]
        else:
            base_result = current_result
            base_scenario = current_scenario

    if not base_result:
        return

    st.markdown(f"""
    <div style='background:rgba(10,20,40,0.9);border:1px solid rgba(20,184,166,0.15);
    border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:1rem;'>
        <span style='color:#64748b;font-size:0.82rem;'>Baseline · </span>
        <span style='color:#e2e8f0;font-weight:600;'>{base_result.scenario_label}</span>
        <span style='color:#64748b;font-size:0.82rem;'> · Income: {usd(base_result.monthly_income)} · Expenses: {usd(base_result.monthly_expenses)} · Surplus: {usd(base_result.monthly_surplus)}</span>
    </div>""", unsafe_allow_html=True)

    section("Custom Stress Parameters")
    col1, col2 = st.columns(2)
    with col1:
        rent_shock = st.slider("Rent increase (%)", min_value=0, max_value=50, value=10, step=1)
        income_shock = st.slider("Income reduction (%)", min_value=0, max_value=50, value=10, step=1)
    with col2:
        grocery_shock = st.slider("Grocery/food cost increase (%)", min_value=0, max_value=50, value=5, step=1)
        utility_shock = st.slider("Utilities increase (%)", min_value=0, max_value=50, value=5, step=1)

    # Calculate stressed values
    base_income = base_result.monthly_income
    base_expenses = base_result.monthly_expenses
    base_surplus = base_result.monthly_surplus

    # Estimate component breakdown from scenario if available
    if base_scenario:
        rent_component = base_scenario.living.rent
        grocery_component = base_scenario.living.groceries
        utility_component = base_scenario.living.utilities
        other_expenses = base_expenses - rent_component - grocery_component - utility_component
    else:
        rent_component = base_expenses * 0.35
        grocery_component = base_expenses * 0.15
        utility_component = base_expenses * 0.08
        other_expenses = base_expenses - rent_component - grocery_component - utility_component

    stressed_rent = rent_component * (1 + rent_shock / 100)
    stressed_groceries = grocery_component * (1 + grocery_shock / 100)
    stressed_utilities = utility_component * (1 + utility_shock / 100)
    stressed_income = base_income * (1 - income_shock / 100)
    stressed_expenses = stressed_rent + stressed_groceries + stressed_utilities + other_expenses
    stressed_surplus = stressed_income - stressed_expenses

    expense_delta = stressed_expenses - base_expenses
    income_delta = stressed_income - base_income
    surplus_delta = stressed_surplus - base_surplus

    section("Stress Impact")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi("Stressed Income", usd(stressed_income), f"Change: {usd(income_delta)}", TEAL if income_delta >= 0 else RED), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi("Stressed Expenses", usd(stressed_expenses), f"Change: +{usd(expense_delta)}", RED if expense_delta > 0 else GREEN), unsafe_allow_html=True)
    with k3:
        surplus_color = GREEN if stressed_surplus >= 150 else (GOLD if stressed_surplus >= 0 else RED)
        st.markdown(kpi("Stressed Surplus", usd(stressed_surplus), f"Change: {usd(surplus_delta)}", surplus_color), unsafe_allow_html=True)
    with k4:
        viability = "✅ Viable" if stressed_surplus >= 0 else "❌ Deficit"
        v_color = GREEN if stressed_surplus >= 0 else RED
        st.markdown(kpi("Plan Status", viability, "Under stress", v_color), unsafe_allow_html=True)

    # Waterfall chart
    section("Waterfall: Baseline → Stressed")
    waterfall_labels = ["Baseline Surplus", f"Rent +{rent_shock}%", f"Groceries +{grocery_shock}%", f"Utilities +{utility_shock}%", f"Income -{income_shock}%", "Stressed Surplus"]
    rent_impact = -(stressed_rent - rent_component)
    grocery_impact = -(stressed_groceries - grocery_component)
    utility_impact = -(stressed_utilities - utility_component)
    income_impact = income_delta

    waterfall_values = [base_surplus, rent_impact, grocery_impact, utility_impact, income_impact, stressed_surplus]
    waterfall_measures = ["absolute", "relative", "relative", "relative", "relative", "total"]
    waterfall_colors = [TEAL, RED, RED, RED, RED if income_impact < 0 else GREEN, GREEN if stressed_surplus >= 0 else RED]

    fig = go.Figure(go.Waterfall(
        name="Stress Impact",
        orientation="v",
        measure=waterfall_measures,
        x=waterfall_labels,
        y=waterfall_values,
        connector=dict(line=dict(color="rgba(148,163,184,0.3)", width=1, dash="dot")),
        decreasing=dict(marker_color=RED),
        increasing=dict(marker_color=GREEN),
        totals=dict(marker_color=TEAL),
        text=[usd(v) for v in waterfall_values],
        textposition="outside",
    ))
    fig.add_hline(y=0, line_color=RED, line_dash="dash", line_width=1.5)
    fig.update_layout(title="Surplus Waterfall Under Custom Stress", yaxis_title="USD", **PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # Multi-scenario stress comparison
    if len(saved) > 1:
        section("Compare All Saved Plans Under Same Stress")
        all_labels = [r.scenario_label for _, r in saved]
        all_stressed = []
        for s, r in saved:
            if s:
                rc = s.living.rent
                gc = s.living.groceries
                uc = s.living.utilities
                oe = r.monthly_expenses - rc - gc - uc
            else:
                rc = r.monthly_expenses * 0.35
                gc = r.monthly_expenses * 0.15
                uc = r.monthly_expenses * 0.08
                oe = r.monthly_expenses * 0.42
            sr = rc * (1 + rent_shock / 100)
            sg = gc * (1 + grocery_shock / 100)
            su = uc * (1 + utility_shock / 100)
            si = r.monthly_income * (1 - income_shock / 100)
            se = sr + sg + su + oe
            all_stressed.append(si - se)

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name="Baseline",
            x=all_labels,
            y=[r.monthly_surplus for _, r in saved],
            marker_color=TEAL,
        ))
        fig3.add_trace(go.Bar(
            name=f"Stressed (rent+{rent_shock}%, income-{income_shock}%)",
            x=all_labels,
            y=all_stressed,
            marker_color=[GREEN if v >= 0 else RED for v in all_stressed],
        ))
        fig3.add_hline(y=0, line_color="#475569", line_dash="dash", line_width=1)
        fig3.update_layout(barmode="group", title="All Plans: Baseline vs Stressed Surplus", yaxis_title="USD", **PLOT_LAYOUT)
        st.plotly_chart(fig3, use_container_width=True)

    # Advisor note
    section("Stress Analysis Summary")
    if stressed_surplus >= 0:
        advisor_box(
            f"Under your custom stress scenario (rent +{rent_shock}%, income -{income_shock}%, food +{grocery_shock}%, utilities +{utility_shock}%), "
            f"the plan remains viable with a surplus of {usd(stressed_surplus)}. "
            f"The total expense increase is {usd(expense_delta)} and income reduction is {usd(abs(income_delta))}. "
            f"The plan has adequate resilience to these shocks."
        )
    else:
        advisor_box(
            f"Under your custom stress scenario, the plan goes into deficit at {usd(stressed_surplus)} per month. "
            f"The combined impact of rent +{rent_shock}%, income -{income_shock}%, food +{grocery_shock}%, and utilities +{utility_shock}% "
            f"creates a {usd(abs(surplus_delta))} swing from baseline. "
            f"To restore viability, you would need to either increase income by {usd(abs(stressed_surplus))} or cut expenses by the same amount."
        )

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: MOVE-IN SHOCK CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────
def page_movein_shock():
    init_v2_state()
    st.markdown("<div style='font-size:1.55rem;font-weight:700;color:#f8fafc;letter-spacing:0.03em;margin-bottom:0.25rem;'>Move-In Shock Calculator</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.88rem;color:#94a3b8;margin-bottom:1.2rem;'>Calculate your total arrival cost, cash runway, and 6-month projection after move-in.</div>", unsafe_allow_html=True)

    all_countries = metro_countries()
    all_uni_countries = university_countries()

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        section("Location")
        mi_country = st.selectbox("Country", all_countries, key="movein_country")
        metros = metro_names_by_country(mi_country)
        metro_name = st.selectbox("Metro / City", metros, key="movein_metro")
        metro = get_metro(metro_name)
        mi_uni_country = st.selectbox("University Country", all_uni_countries, key="movein_uni_country")
        unis = university_names_by_country(mi_uni_country)
        uni_name = st.selectbox("University (optional)", ["— None —"] + unis, key="movein_uni")
        uni = get_university(uni_name) if uni_name != "— None —" else None

        section("Your Savings")
        starting_cash = st.number_input("Total cash available before arrival ($)", min_value=0.0, value=8000.0, step=500.0, key="movein_cash")

        section("Monthly Income & Expenses (for runway calc)")
        monthly_income_est = st.number_input("Expected monthly income ($)", min_value=0.0, value=1800.0, step=100.0, key="movein_income")
        monthly_expenses_est = st.number_input("Expected monthly expenses ($)", min_value=0.0,
                                                value=float(metro.rent_shared + metro.groceries + metro.utilities + metro.transport_monthly + metro.internet + metro.misc_basic + metro.discretionary if metro else 1400.0),
                                                step=50.0, key="movein_expenses")
        monthly_surplus = monthly_income_est - monthly_expenses_est

    with col_right:
        section("Move-In Cost Items")
        visa_fee = st.number_input("Visa application fee ($)", min_value=0.0, value=185.0, step=5.0)
        sevis_fee = st.number_input("SEVIS fee ($)", min_value=0.0, value=350.0, step=5.0)
        flight = st.number_input("International flight ($)", min_value=0.0, value=900.0, step=50.0)

        rent_default = float(metro.rent_shared) if metro else 800.0
        housing_deposit = st.number_input("Housing deposit ($)", min_value=0.0, value=rent_default, step=50.0)

        first_last_months = st.radio("First/last month rent required?", ["First month only", "First + Last month"], horizontal=True)
        first_last_amount = rent_default if first_last_months == "First month only" else rent_default * 2

        furniture = st.number_input("Furniture & household setup ($)", min_value=0.0, value=800.0, step=50.0)
        winter_clothing = st.number_input("Winter clothing ($)", min_value=0.0, value=300.0, step=25.0)
        phone = st.number_input("Phone setup / SIM ($)", min_value=0.0, value=150.0, step=10.0)
        transport_setup = st.number_input("Local transport setup ($)", min_value=0.0, value=100.0, step=10.0)
        laptop = st.number_input("Laptop / academic supplies ($)", min_value=0.0, value=0.0, step=50.0)
        misc_arrival = st.number_input("Miscellaneous arrival costs ($)", min_value=0.0, value=200.0, step=25.0)

    # Totals
    total_movein = (visa_fee + sevis_fee + flight + housing_deposit +
                    first_last_amount + furniture + winter_clothing +
                    phone + transport_setup + laptop + misc_arrival)
    cash_after = starting_cash - total_movein
    runway = cash_after / monthly_expenses_est if monthly_expenses_est > 0 else 0

    st.markdown("---")
    section("Arrival Summary")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi("Total Move-In Cost", usd(total_movein), "All pre-arrival items", GOLD), unsafe_allow_html=True)
    with k2:
        cash_color = GREEN if cash_after >= 0 else RED
        st.markdown(kpi("Cash After Move-In", usd(cash_after), "Starting balance", cash_color), unsafe_allow_html=True)
    with k3:
        runway_color = GREEN if runway >= 3 else (GOLD if runway >= 2 else RED)
        st.markdown(kpi("Emergency Runway", f"{max(0, runway):.1f} months", "Cash ÷ monthly expenses", runway_color), unsafe_allow_html=True)
    with k4:
        surplus_color = GREEN if monthly_surplus >= 0 else RED
        st.markdown(kpi("Monthly Surplus", usd(monthly_surplus), "Income minus expenses", surplus_color), unsafe_allow_html=True)

    if cash_after < 0:
        st.markdown(f"""
        <div style='background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.4);
        border-radius:8px;padding:0.8rem 1.2rem;margin:0.5rem 0;color:#f87171;font-size:0.9rem;'>
            ⚠️ You need <strong>{usd(abs(cash_after))}</strong> more before arriving.
            Your current savings do not cover move-in costs.
        </div>""", unsafe_allow_html=True)
    elif runway < 2:
        st.markdown(f"""
        <div style='background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);
        border-radius:8px;padding:0.8rem 1.2rem;margin:0.5rem 0;color:#fbbf24;font-size:0.9rem;'>
            ⚠️ Cash runway after move-in is only {runway:.1f} months. Aim for at least 3 months buffer.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);
        border-radius:8px;padding:0.8rem 1.2rem;margin:0.5rem 0;color:#34d399;font-size:0.9rem;'>
            ✓ You have sufficient funds for move-in with {runway:.1f} months of runway remaining.
        </div>""", unsafe_allow_html=True)

    # Breakdown chart
    st.markdown("---")
    section("Move-In Cost Breakdown")
    breakdown_items = [
        ("Visa & SEVIS", visa_fee + sevis_fee),
        ("Flight", flight),
        ("Housing Deposit", housing_deposit),
        ("First/Last Rent", first_last_amount),
        ("Furniture", furniture),
        ("Clothing", winter_clothing),
        ("Phone", phone),
        ("Transport Setup", transport_setup),
        ("Laptop/Supplies", laptop),
        ("Misc", misc_arrival),
    ]
    breakdown_labels = [l for l, v in breakdown_items if v > 0]
    breakdown_values = [v for l, v in breakdown_items if v > 0]

    fig = go.Figure(go.Pie(
        labels=breakdown_labels,
        values=breakdown_values,
        hole=0.45,
        marker=dict(colors=[TEAL, GOLD, GREEN, "#8b5cf6", "#f97316", "#06b6d4", "#ec4899", "#84cc16", "#a78bfa", "#fb923c"]),
        textinfo="label+percent",
        textfont=dict(size=11, color="#e2e8f0"),
    ))
    fig.update_layout(
        title=f"Total Move-In: {usd(total_movein)}",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(font=dict(color="#94a3b8", size=10)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # 6-month cash projection
    section("6-Month Cash Projection After Arrival")
    months = list(range(0, 7))
    cash_proj = [max(0, cash_after + monthly_surplus * m) for m in months]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=months, y=cash_proj,
        mode="lines+markers",
        name="Cash Balance",
        line=dict(color=TEAL, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(20,184,166,0.08)",
    ))
    fig2.add_hline(y=0, line_color=RED, line_dash="dash", line_width=1.5)
    fig2.update_layout(title="Cash Balance: Months 0–6 After Arrival", xaxis_title="Month", yaxis_title="USD", **PLOT_LAYOUT)
    st.plotly_chart(fig2, use_container_width=True)

    # Advisor note
    section("Advisor Note")
    if cash_after < 0:
        advisor_box(
            f"Your current savings of {usd(starting_cash)} are insufficient for move-in costs of {usd(total_movein)}. "
            f"You need at least {usd(total_movein + monthly_expenses_est * 2)} before arriving — covering move-in plus two months of living expenses. "
            f"The most flexible areas to reduce are furniture (buy second-hand), flight (book early), and first/last rent (negotiate with landlord)."
        )
    elif runway < 3:
        advisor_box(
            f"You can cover move-in, but your {runway:.1f}-month runway is thin. "
            f"International students frequently face delayed stipend payments in the first month. "
            f"Aim to arrive with at least {usd(monthly_expenses_est * 3 + total_movein)} total — enough for move-in plus 3 months of living costs."
        )
    else:
        advisor_box(
            f"You are financially prepared for arrival. Move-in costs of {usd(total_movein)} leave you with {usd(cash_after)} "
            f"and a {runway:.1f}-month runway. "
            f"{'Your monthly surplus of ' + usd(monthly_surplus) + ' will build your balance over time.' if monthly_surplus > 0 else 'However, your monthly expenses exceed income — address this before arrival.'}"
        )
