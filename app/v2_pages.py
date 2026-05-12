"""
v2_pages.py — V2 Decision Tool Pages
Student Financial Intelligence Dashboard

Pages:
  - Decision Planner
  - Admit Comparison
  - Stress Test
  - Move-In Shock Calculator
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_model import (
    PlanningScenario, FundingInputs, LivingCosts, MoveInCosts
)
from decision_engine import evaluate_scenario
from providers import (
    load_metro_benchmarks, load_university_profiles,
    metro_names, university_names, get_metro, get_university
)

# ─── shared style helpers (duplicated from app.py to keep module self-contained)
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


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DECISION PLANNER
# ─────────────────────────────────────────────────────────────────────────────

def page_decision_planner():
    init_v2_state()
    st.markdown("<div style='font-size:1.55rem;font-weight:700;color:#f8fafc;letter-spacing:0.03em;margin-bottom:0.25rem;'>Decision Planner</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.88rem;color:#94a3b8;margin-bottom:1.2rem;'>Build a financial plan for one school or city. Get a bottom-line recommendation, safe rent ceiling, and risk assessment.</div>", unsafe_allow_html=True)

    metros = metro_names()
    unis = university_names()

    # ── Planning mode
    mode = st.radio("Planning mode", ["By University", "By City / Metro"], horizontal=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        section("Location & School")
        label = st.text_input("Plan label (e.g. WashU Option A)", value="My Plan")

        if mode == "By University":
            uni_name = st.selectbox("University", unis)
            uni = get_university(uni_name)
            if uni:
                metro_default = uni.metro
                st.markdown(f"<div style='font-size:0.8rem;color:#64748b;margin-top:-0.5rem;margin-bottom:0.8rem;'>📍 {uni.metro}, {uni.state} · {uni.program_type} · I-20 estimate: {usd(uni.i20_cost_estimate)}</div>", unsafe_allow_html=True)
                if uni.notes:
                    st.markdown(f"<div style='font-size:0.78rem;color:#475569;margin-bottom:0.8rem;font-style:italic;'>{uni.notes}</div>", unsafe_allow_html=True)
            else:
                metro_default = metros[0]
            metro_name = metro_default
        else:
            uni = None
            metro_name = st.selectbox("Metro / City", metros)

        metro = get_metro(metro_name)

        section("Funding")
        has_assistantship = st.checkbox("I have (or expect) an assistantship / TA / RA", value=False)

        if has_assistantship and uni:
            default_stipend = round(uni.assistantship_stipend_annual / 12, 0)
            tuition_covered = uni.assistantship_covers_tuition
        else:
            default_stipend = 0.0
            tuition_covered = False

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
    if not result:
        return

    st.markdown("---")
    section("Decision Output")

    # KPI row
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
    st.markdown("<div style='font-size:0.88rem;color:#94a3b8;margin-bottom:1.2rem;'>Rank your saved options side by side. See which school or city is financially safer over 12 months.</div>", unsafe_allow_html=True)

    saved = st.session_state.get("v2_saved_scenarios", [])

    if not saved:
        st.markdown("""
        <div style='background:rgba(20,184,166,0.06);border:1px solid rgba(20,184,166,0.2);
        border-radius:10px;padding:1.5rem 2rem;text-align:center;color:#64748b;'>
            No scenarios saved yet. Go to <strong style='color:#14b8a6;'>Decision Planner</strong>,
            build a plan, and click <strong style='color:#14b8a6;'>Save to Comparison</strong>.
        </div>""", unsafe_allow_html=True)
        return

    results = [r for _, r in saved]
    labels = [r.scenario_label for r in results]

    # Clear button
    if st.button("🗑  Clear all saved scenarios"):
        st.session_state["v2_saved_scenarios"] = []
        st.rerun()

    section("Side-by-Side Comparison")

    # Build comparison table
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
    colors = [GREEN if v >= 0 else RED for v in surplus_vals]
    fig = go.Figure(go.Bar(
        x=labels,
        y=surplus_vals,
        marker_color=colors,
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
    st.markdown("<div style='font-size:0.88rem;color:#94a3b8;margin-bottom:1.2rem;'>Apply realistic downside pressure to any saved plan. See exactly when and how your finances break.</div>", unsafe_allow_html=True)

    saved = st.session_state.get("v2_saved_scenarios", [])

    if not saved:
        st.markdown("""
        <div style='background:rgba(20,184,166,0.06);border:1px solid rgba(20,184,166,0.2);
        border-radius:10px;padding:1.5rem 2rem;text-align:center;color:#64748b;'>
            No scenarios saved yet. Build and save a plan in <strong style='color:#14b8a6;'>Decision Planner</strong> first.
        </div>""", unsafe_allow_html=True)
        return

    labels = [r.scenario_label for _, r in saved]
    selected_label = st.selectbox("Select a plan to stress test", labels)
    selected_pair = next((pair for pair in saved if pair[1].scenario_label == selected_label), None)
    if not selected_pair:
        return

    scenario, base_result = selected_pair

    section("Baseline Position")
    b1, b2, b3 = st.columns(3)
    with b1: st.markdown(kpi("Baseline Surplus", usd(base_result.monthly_surplus), "No stress applied", GREEN if base_result.monthly_surplus >= 0 else RED), unsafe_allow_html=True)
    with b2: st.markdown(kpi("Affordability Score", f"{base_result.affordability_score}/100", score_label(base_result.affordability_score), score_color(base_result.affordability_score)), unsafe_allow_html=True)
    with b3: st.markdown(kpi("Cash Runway", f"{base_result.emergency_runway_months:.1f} mo", "After move-in", TEAL), unsafe_allow_html=True)

    section("Custom Stress Parameters")
    st.markdown("<div style='font-size:0.82rem;color:#64748b;margin-bottom:0.8rem;'>Adjust sliders to simulate specific downside scenarios.</div>", unsafe_allow_html=True)

    sc1, sc2 = st.columns(2)
    with sc1:
        rent_increase = st.slider("Rent increase (%)", 0, 30, 8)
        income_reduction = st.slider("Income reduction (%)", 0, 50, 10)
        fx_depreciation = st.slider("FX depreciation (%)", 0, 40, 0)
    with sc2:
        emergency_expense = st.slider("One-time emergency expense ($)", 0, 5000, 0, step=100)
        grocery_inflation = st.slider("Grocery/utilities inflation (%)", 0, 20, 5)
        work_hours_cut = st.slider("Work hours reduction (hrs/week)", 0, 20, 0)

    # Apply custom stress
    base_income = base_result.monthly_income
    base_expenses = base_result.monthly_expenses
    base_rent = scenario.living.rent

    # Adjust income
    wage_income = scenario.funding.hourly_wage * max(0, scenario.funding.weekly_work_hours - work_hours_cut) * 4.33
    fx_income = (scenario.funding.home_currency_monthly / scenario.funding.fx_rate) * (1 - fx_depreciation / 100) if scenario.funding.fx_rate > 0 else 0
    stressed_income = (scenario.funding.monthly_stipend + wage_income + scenario.funding.family_support_monthly + fx_income) * (1 - income_reduction / 100)

    # Adjust expenses
    rent_stressed = base_rent * (1 + rent_increase / 100)
    food_stressed = (scenario.living.groceries + scenario.living.utilities) * (1 + grocery_inflation / 100)
    other_expenses = base_expenses - base_rent - scenario.living.groceries - scenario.living.utilities
    stressed_expenses = rent_stressed + food_stressed + other_expenses + (emergency_expense / 12)

    stressed_surplus = round(stressed_income - stressed_expenses, 2)
    surplus_delta = stressed_surplus - base_result.monthly_surplus

    section("Stress Test Results")
    r1, r2, r3, r4 = st.columns(4)
    with r1: st.markdown(kpi("Stressed Income", usd(stressed_income), f"-{income_reduction}% reduction", GOLD), unsafe_allow_html=True)
    with r2: st.markdown(kpi("Stressed Expenses", usd(stressed_expenses), f"Rent +{rent_increase}%, food +{grocery_inflation}%", GOLD), unsafe_allow_html=True)
    with r3:
        s_color = GREEN if stressed_surplus >= 0 else RED
        st.markdown(kpi("Stressed Surplus", usd(stressed_surplus), "After all adjustments", s_color), unsafe_allow_html=True)
    with r4:
        d_color = GREEN if surplus_delta >= 0 else RED
        st.markdown(kpi("Impact vs Baseline", usd(surplus_delta), "Change from baseline", d_color), unsafe_allow_html=True)

    # Waterfall chart
    section("Stress Impact Waterfall")
    rent_impact = -(rent_stressed - base_rent)
    food_impact = -(food_stressed - (scenario.living.groceries + scenario.living.utilities))
    income_impact = stressed_income - base_income
    emergency_impact = -(emergency_expense / 12)

    waterfall_labels = ["Baseline Surplus", "Rent Increase", "Food/Utilities", "Income Reduction", "Emergency", "Stressed Surplus"]
    waterfall_values = [base_result.monthly_surplus, rent_impact, food_impact, income_impact, emergency_impact, stressed_surplus]
    waterfall_measures = ["absolute", "relative", "relative", "relative", "relative", "total"]
    waterfall_colors = [TEAL, RED, RED, RED, RED, GREEN if stressed_surplus >= 0 else RED]

    fig = go.Figure(go.Waterfall(
        name="Stress Impact",
        orientation="v",
        measure=waterfall_measures,
        x=waterfall_labels,
        y=waterfall_values,
        connector={"line": {"color": "rgba(94,114,148,0.3)"}},
        decreasing={"marker": {"color": RED}},
        increasing={"marker": {"color": GREEN}},
        totals={"marker": {"color": TEAL}},
        text=[usd(v) for v in waterfall_values],
        textposition="outside",
    ))
    fig.update_layout(title="Surplus Waterfall Under Stress", yaxis_title="USD", **PLOT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # Scenario presets
    section("Preset Stress Scenarios")
    preset_col1, preset_col2, preset_col3 = st.columns(3)

    scenarios_preset = [
        ("Stipend Delayed 1 Month", base_result.monthly_surplus - base_income, "Income drops to zero for one month"),
        ("Rent +15%, Income -10%", base_result.monthly_surplus - (base_rent * 0.15) - (base_income * 0.10), "Moderate housing + income shock"),
        ("Assistantship Lost", base_result.monthly_surplus - scenario.funding.monthly_stipend, "Stipend removed entirely"),
    ]
    for col, (label, val, desc) in zip([preset_col1, preset_col2, preset_col3], scenarios_preset):
        with col:
            v_color = GREEN if val >= 0 else RED
            st.markdown(f"""
            <div style='background:rgba(10,20,40,0.9);border:1px solid rgba(20,184,166,0.15);
            border-radius:10px;padding:0.9rem 1.1rem;margin-bottom:0.6rem;'>
                <div style='font-size:0.78rem;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.3rem;'>{label}</div>
                <div style='font-size:1.3rem;font-weight:700;color:{v_color};'>{usd(val)}</div>
                <div style='font-size:0.75rem;color:#475569;margin-top:0.2rem;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

    # Advisor note
    if stressed_surplus < 0:
        advisor_box(
            f"Under your custom stress scenario, the plan becomes cash-negative with a surplus of {usd(stressed_surplus)}. "
            f"The largest single driver is {'rent pressure' if rent_impact < income_impact else 'income reduction'}. "
            f"To restore viability, consider reducing rent by at least {usd(abs(stressed_surplus) + 100)} or securing an additional income source."
        )
    else:
        advisor_box(
            f"Under your custom stress scenario, the plan remains viable with a surplus of {usd(stressed_surplus)}. "
            f"This represents a {abs(surplus_delta / base_result.monthly_surplus * 100):.0f}% reduction from baseline. "
            f"The plan has adequate resilience to moderate downside pressure."
        )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: MOVE-IN SHOCK CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────

def page_movein_shock():
    init_v2_state()
    st.markdown("<div style='font-size:1.55rem;font-weight:700;color:#f8fafc;letter-spacing:0.03em;margin-bottom:0.25rem;'>Move-In Shock Calculator</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.88rem;color:#94a3b8;margin-bottom:1.2rem;'>Calculate the total cash you need before arriving. Most students underestimate this by $2,000–$4,000.</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        section("Government & Travel Costs")
        visa_fee = st.number_input("F-1 Visa application fee ($)", value=185.0, step=10.0)
        sevis_fee = st.number_input("SEVIS I-901 fee ($)", value=350.0, step=10.0)
        flight = st.number_input("International flight ($)", value=800.0, step=50.0)

        section("Housing Setup")
        monthly_rent = st.number_input("Monthly rent ($)", value=900.0, step=50.0)
        deposit_months = st.selectbox("Security deposit (months of rent)", [1, 2], index=0)
        first_last = st.checkbox("First + last month rent required upfront", value=True)
        housing_deposit = monthly_rent * deposit_months
        first_last_amount = monthly_rent * 2 if first_last else monthly_rent

        section("Setup & Supplies")
        furniture = st.number_input("Furniture & bedding setup ($)", value=800.0, step=50.0)
        winter_clothing = st.number_input("Winter clothing ($)", value=300.0, step=25.0)
        phone = st.number_input("Phone setup / SIM ($)", value=150.0, step=10.0)
        transport_setup = st.number_input("Transport setup (transit card, etc.) ($)", value=100.0, step=10.0)
        laptop = st.number_input("Laptop / study supplies ($)", value=0.0, step=50.0)
        misc_arrival = st.number_input("Miscellaneous arrival costs ($)", value=200.0, step=25.0)

    with col2:
        section("Financial Context")
        starting_cash = st.number_input("Total cash available before arrival ($)", value=8000.0, step=500.0)
        monthly_income = st.number_input("Expected monthly income after arrival ($)", value=1500.0, step=100.0)
        monthly_expenses_est = st.number_input("Expected monthly expenses ($)", value=1800.0, step=100.0)

        # Calculate totals
        total_movein = (visa_fee + sevis_fee + flight + housing_deposit +
                        first_last_amount + furniture + winter_clothing +
                        phone + transport_setup + laptop + misc_arrival)
        cash_after = starting_cash - total_movein
        monthly_surplus = monthly_income - monthly_expenses_est
        runway = cash_after / monthly_expenses_est if monthly_expenses_est > 0 else 0
        months_to_stabilize = abs(cash_after / monthly_surplus) if monthly_surplus < 0 and monthly_surplus != 0 else 0

        section("Results")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(kpi("Total Move-In Cost", usd(total_movein), "All pre-arrival expenses", GOLD), unsafe_allow_html=True)
            st.markdown(kpi("Cash After Move-In", usd(cash_after), "Starting balance on arrival", GREEN if cash_after >= 0 else RED), unsafe_allow_html=True)
        with r2:
            st.markdown(kpi("Emergency Runway", f"{max(0, runway):.1f} months", "Cash ÷ monthly expenses", GREEN if runway >= 3 else (GOLD if runway >= 2 else RED)), unsafe_allow_html=True)
            st.markdown(kpi("Monthly Surplus", usd(monthly_surplus), "Income minus expenses", GREEN if monthly_surplus >= 0 else RED), unsafe_allow_html=True)

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
    breakdown_labels = ["Visa & SEVIS", "Flight", "Housing Deposit", "First/Last Rent", "Furniture", "Clothing", "Phone", "Transport", "Laptop/Supplies", "Misc"]
    breakdown_values = [visa_fee + sevis_fee, flight, housing_deposit, first_last_amount, furniture, winter_clothing, phone, transport_setup, laptop, misc_arrival]
    breakdown_values = [v for v in breakdown_values if v > 0]
    breakdown_labels = [l for l, v in zip(breakdown_labels, [visa_fee + sevis_fee, flight, housing_deposit, first_last_amount, furniture, winter_clothing, phone, transport_setup, laptop, misc_arrival]) if v > 0]

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
