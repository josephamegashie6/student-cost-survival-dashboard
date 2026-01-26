# =========================================================
# 1) IMPORTS (make sure these are at the very top of app.py)
# =========================================================
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from datetime import date, timedelta

# =========================================================
# 2) PAGE CONFIG (must be before most Streamlit calls)
# =========================================================
st.set_page_config(
    page_title="Student Cost Survival Dashboard",
    layout="wide"
)

# ---------------------------------------
# SESSION DEFAULTS (GLOBAL SNAPSHOT)
# ---------------------------------------
if "status" not in st.session_state:
    st.session_state["status"] = "Unknown"
if "balance" not in st.session_state:
    st.session_state["balance"] = 0.0
if "context_city" not in st.session_state:
    st.session_state["context_city"] = "-"

# goal settings for "My Plan"
if "goal_amount" not in st.session_state:
    st.session_state["goal_amount"] = 1000.0
if "goal_deadline" not in st.session_state:
    st.session_state["goal_deadline"] = date.today() + timedelta(days=90)

# City Compare sidebar controls
if "compare_metric" not in st.session_state:
    st.session_state["compare_metric"] = "Balance"
if "month_preset" not in st.session_state:
    st.session_state["month_preset"] = "All data"

# financial health score
if "health_score" not in st.session_state:
    st.session_state["health_score"] = 0
if "rent_ratio" not in st.session_state:
    st.session_state["rent_ratio"] = None
if "savings_rate" not in st.session_state:
    st.session_state["savings_rate"] = None
if "buffer_months" not in st.session_state:
    st.session_state["buffer_months"] = 0.0

# guided flow + analytics history + scenarios
if "first_run" not in st.session_state:
    st.session_state["first_run"] = True
if "calc_history" not in st.session_state:
    st.session_state["calc_history"] = []
if "saved_scenarios" not in st.session_state:
    st.session_state["saved_scenarios"] = []
if "current_savings" not in st.session_state:
    st.session_state["current_savings"] = 0.0

# =========================================================
# 3) STYLING (CSS) - put before UI so it applies early
# =========================================================
st.markdown(
    """
<style>
.block-container {
    padding-top: 3.0rem;
    max-width: 1300px;
}

/* Generic card */
.card, .section-card {
    padding: 0.75rem 0.9rem;
    border-radius: 14px;
    background: #020617;
    border: 1px solid #1f2937;
    margin-bottom: 0.6rem;
}

/* Small note */
.small-note {opacity: 0.75; font-size: 0.9rem;}

/* KPI cards */
.kpi-card {
    padding: 0.65rem 0.8rem;
    border-radius: 12px;
    background: #020617;
    border: 1px solid #1f2937;
}
.kpi-label {
    font-size: 0.8rem;
    opacity: 0.8;
}
.kpi-value {
    font-size: 1.5rem;
    font-weight: 600;
    margin-top: 0.15rem;
}
.kpi-sub {
    font-size: 0.78rem;
    opacity: 0.7;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 4) CONSTANTS + HELPERS (must come BEFORE you use them)
# =========================================================

# Minimum wage defaults (update later if you want)
CITY_MIN_WAGE = {
    "Saint Louis": 12.30,
    "Chicago": 15.80,
    "New York City": 16.00,
    "Los Angeles": 16.90,
}

# Calculator dropdown list (adds fallback option)
CALCULATOR_CITIES = sorted(list(CITY_MIN_WAGE.keys()))
if "Other (Not listed)" not in CALCULATOR_CITIES:
    CALCULATOR_CITIES.append("Other (Not listed)")

DEFAULT_CITY = "Saint Louis" if "Saint Louis" in CALCULATOR_CITIES else CALCULATOR_CITIES[0]


def financial_status(balance: float) -> str:
    if balance > 0:
        return "Surplus"
    elif balance == 0:
        return "Break-even"
    return "Deficit"


def money(x: float) -> str:
    return f"${x:,.0f}"


def safe_read_csv(path: str):
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def clamp(n: float, low: float, high: float) -> float:
    return max(low, min(high, n))


def pct(x: float, base: float) -> float:
    if base <= 0:
        return 0.0
    return 100.0 * x / base


def pressure_band(ratio: float, green_max: float, yellow_max: float) -> str:
    if ratio <= green_max:
        return "Healthy"
    elif ratio <= yellow_max:
        return "Risky"
    return "Dangerous"


# -----------------------------
# Financial Health Score helpers
# -----------------------------
def financial_health_score(
    total_income: float,
    total_expenses: float,
    rent: float,
    balance: float
) -> tuple[int, dict]:

    if total_income <= 0:
        return 0, {
            "balance_points": 0,
            "rent_points": 0,
            "savings_points": 0,
            "buffer_points": 0,
            "rent_ratio": None,
            "savings_rate": None,
            "buffer_months": 0,
        }

    rent_ratio = rent / total_income
    savings_rate = balance / total_income

    # 1) Balance (0 or 40)
    balance_points = 40 if balance > 0 else 0

    # 2) Rent health (0 to 25)
    rent_points = 25 * (0.60 - rent_ratio) / (0.60 - 0.35)
    rent_points = int(round(clamp(rent_points, 0, 25)))

    # 3) Savings rate (0 to 20)
    savings_points = 20 * (savings_rate / 0.10)
    savings_points = int(round(clamp(savings_points, 0, 20)))

    # 4) Buffer (0 to 15)
    if total_expenses > 0:
        buffer_months = balance / total_expenses
    else:
        buffer_months = 0

    buffer_points = 15 * buffer_months
    buffer_points = int(round(clamp(buffer_points, 0, 15)))

    score = balance_points + rent_points + savings_points + buffer_points
    score = int(clamp(score, 0, 100))

    breakdown = {
        "balance_points": balance_points,
        "rent_points": rent_points,
        "savings_points": savings_points,
        "buffer_points": buffer_points,
        "rent_ratio": rent_ratio,
        "savings_rate": savings_rate,
        "buffer_months": buffer_months,
    }

    return score, breakdown


def score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Risky"
    return "Critical"


# =========================================================
# 5) GUIDED FIRST TIME FLOW (banner)
# =========================================================
if st.session_state.get("first_run", True):
    st.info("Step 1: Run Calculator  |  Step 2: Compare Cities  |  Step 3: Build a Plan")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        if st.button("Hide guide"):
            st.session_state["first_run"] = False

# ------------------------------
# SIDEBAR: NAV + SNAPSHOT + CONTROLS
# ------------------------------
with st.sidebar:
    st.markdown("### Student Cost Survival")

    page = option_menu(
        menu_title=None,
        options=["Calculator", "City Compare", "My Plan", "Settings"],
        icons=["calculator", "globe2", "wallet2", "gear"],
        default_index=0,
        styles={
            "container": {"padding": "0.5rem 0.3rem", "background-color": "#020617"},
            "icon": {"color": "white", "font-size": "1rem"},
            "nav-link": {
                "font-size": "0.9rem",
                "padding": "0.45rem 0.8rem",
                "border-radius": "8px",
                "color": "white",
                "margin": "0.1rem 0",
            },
            "nav-link-selected": {"background-color": "#f97316", "color": "white"},
        },
    )

    st.markdown("---")
    st.markdown("#### My Snapshot")

    st.write("Status:", st.session_state["status"])
    st.write("Balance / month:", f"${st.session_state['balance']:.0f}")
    st.caption(f"Based on last calculator run (city: {st.session_state['context_city']})")

    health_score = st.session_state.get("health_score")
    if health_score is not None:
        st.write("Health score:", health_score, f"({score_label(int(health_score))})")

    rr = st.session_state.get("rent_ratio")
    sr = st.session_state.get("savings_rate")
    if rr is not None and sr is not None:
        st.caption(f"Rent/Income: {rr*100:.1f}%  |  Savings rate: {sr*100:.1f}%")

    status = st.session_state["status"]
    if status == "Deficit":
        st.info("Tip: Check rent and misc. Even $40 cut can flip you positive.")
    elif status == "Break-even":
        st.info("Tip: Try to build at least one month of buffer savings.")
    elif status == "Surplus":
        st.info("Tip: Consider saving or investing part of your surplus.")
    else:
        st.caption("Run the calculator to see a personalized snapshot.")

    # page specific controls
    if page == "City Compare":
        st.markdown("#### Compare settings")
        st.selectbox(
            "Compare by",
            ["Balance", "Rent pressure", "Food cost", "Transport cost"],
            key="compare_metric",
        )
        st.radio(
            "Month range",
            ["All data", "Last 3 months", "Last 6 months"],
            key="month_preset",
        )

    elif page == "My Plan":
        st.markdown("#### Savings goal")
        st.number_input(
            "Goal amount ($)",
            min_value=0.0,
            step=50.0,
            key="goal_amount",
        )
        st.date_input("Goal deadline", key="goal_deadline")
        st.caption("Use the Calculator first so this plan can use your real monthly balance.")

    elif page == "Settings":
        st.markdown("#### Preferences (future)")
        st.info("Here you can later add currency options, wage presets, and theme settings.")

# =========================================================
# 6) TOP TITLE (shows on every page)
# =========================================================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.title("International Student Cost Survival Dashboard")
st.markdown(
    "<div class='small-note'>Use the Calculator for personal numbers and City Compare for CSV insights.</div>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 7) PAGE ROUTING
# =========================================================

# ---------------------------------------------------------
# PAGE A: CALCULATOR
# ---------------------------------------------------------
if page == "Calculator":

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Personal Calculator")
    st.markdown(
        "<div class='small-note'>Fill the form and click <b>Calculate</b>. "
        "We use City minimum wage to estimate job income.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("calculator_form"):

        top1, top2, top3 = st.columns([1.2, 1, 1])

        with top1:
            calc_city = st.selectbox(
                "City",
                CALCULATOR_CITIES,
                index=CALCULATOR_CITIES.index(DEFAULT_CITY) if DEFAULT_CITY in CALCULATOR_CITIES else 0,
            )

        with top2:
            is_other_city = calc_city == "Other (Not listed)"
            min_wage = 15.0 if is_other_city else CITY_MIN_WAGE.get(calc_city, 15.0)

            wage = st.number_input(
                "Minimum wage ($/hour)",
                min_value=0.0,
                value=float(min_wage),
                step=0.25,
            )

        with top3:
            weeks_per_month = st.number_input(
                "Weeks per month",
                min_value=3.0,
                max_value=5.0,
                value=4.33,
                step=0.01,
            )

        st.markdown("### Work hours (weekly)")
        h1, h2, h3, h4 = st.columns(4)
        with h1:
            hours_mon_fri = st.number_input("Hours Mon to Fri (total)", min_value=0.0, value=20.0, step=1.0)
        with h2:
            hours_sat = st.number_input("Hours Saturday", min_value=0.0, value=0.0, step=1.0)
        with h3:
            hours_sun = st.number_input("Hours Sunday", min_value=0.0, value=0.0, step=1.0)
        with h4:
            sunday_multiplier = st.number_input("Sunday pay multiplier", min_value=1.0, value=1.0, step=0.25)

        st.markdown("### Other monthly income")
        stipend = st.number_input("Monthly stipend or support ($)", min_value=0.0, value=0.0, step=50.0)

        st.markdown("### Monthly expenses")
        e1, e2, e3 = st.columns(3)
        with e1:
            rent = st.number_input("Rent ($)", min_value=0.0, value=850.0, step=25.0)
            utilities = st.number_input("Utilities ($)", min_value=0.0, value=120.0, step=10.0)
        with e2:
            food = st.number_input("Food ($)", min_value=0.0, value=350.0, step=10.0)
            transport = st.number_input("Transport ($)", min_value=0.0, value=90.0, step=10.0)
        with e3:
            phone_internet = st.number_input("Phone/Internet ($)", min_value=0.0, value=60.0, step=10.0)
            misc_basic = st.number_input("Misc basics ($)", min_value=0.0, value=130.0, step=10.0)

        submitted = st.form_submit_button("✅ Calculate")

    if not submitted:
        st.info("Fill the form above and click Calculate to see your budget, charts, and download.")
    else:
        if calc_city == "Other (Not listed)":
            st.info("City not listed. Enter your real wage and expenses for a custom estimate.")

        # Calculations
        weekly_job_income = (wage * (hours_mon_fri + hours_sat)) + (wage * hours_sun * sunday_multiplier)
        monthly_job_income = weekly_job_income * weeks_per_month

        total_income = monthly_job_income + stipend
        total_expenses = rent + utilities + food + transport + phone_internet + misc_basic
        balance = total_income - total_expenses
        status = financial_status(balance)

        health_score, score_breakdown = financial_health_score(
            total_income=total_income,
            total_expenses=total_expenses,
            rent=rent,
            balance=balance
        )

        # Save core values in session for other pages
        st.session_state["total_income"] = float(total_income)
        st.session_state["total_expenses"] = float(total_expenses)
        st.session_state["balance"] = float(balance)
        st.session_state["status"] = status
        st.session_state["context_city"] = calc_city

        st.session_state["health_score"] = int(health_score)
        st.session_state["rent_ratio"] = score_breakdown["rent_ratio"]
        st.session_state["savings_rate"] = score_breakdown["savings_rate"]
        st.session_state["buffer_months"] = float(score_breakdown.get("buffer_months", 0))

        # Store inputs needed for scenario and plan logic
        st.session_state["weekly_job_income"] = float(weekly_job_income)
        st.session_state["wage"] = float(wage)
        st.session_state["weeks_per_month"] = float(weeks_per_month)
        st.session_state["stipend"] = float(stipend)

        st.session_state["rent"] = float(rent)
        st.session_state["utilities"] = float(utilities)
        st.session_state["food"] = float(food)
        st.session_state["transport"] = float(transport)
        st.session_state["phone_internet"] = float(phone_internet)
        st.session_state["misc_basic"] = float(misc_basic)

        # Store history for trend insights
        st.session_state["calc_history"].append({
            "run_date": date.today().isoformat(),
            "city": calc_city,
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "balance": float(balance),
        })
        st.session_state["calc_history"] = st.session_state["calc_history"][-12:]

        # turn off first-run after first successful calculate
        st.session_state["first_run"] = False

        # Results cards
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Results")

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("City", calc_city)
        r2.metric("Min wage", f"${wage:.2f}/hr")
        r3.metric("Monthly job income (est.)", money(monthly_job_income))
        r4.metric("Monthly stipend", money(stipend))

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Income", money(total_income))
        k2.metric("Total Expenses", money(total_expenses))
        k3.metric("Balance", money(balance))

        if status == "Surplus":
            st.success("SURPLUS: You have buffer after essentials.")
        elif status == "Break-even":
            st.warning("BREAK-EVEN: You are surviving, but no buffer.")
        else:
            st.error("DEFICIT: You will likely need support or expense cuts.")

        st.markdown("</div>", unsafe_allow_html=True)

        # Financial Health Score
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Financial Health Score")

        score = st.session_state.get("health_score", 0)
        rent_ratio_ss = st.session_state.get("rent_ratio", 0) or 0
        savings_rate_ss = st.session_state.get("savings_rate", 0) or 0
        buffer_months_ss = st.session_state.get("buffer_months", 0) or 0

        score_int = int(round(score))
        score_int = max(0, min(score_int, 100))
        st.progress(score_int)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score", f"{int(score)}/100")
        c2.metric("Rent / Income", f"{rent_ratio_ss*100:.1f}%")
        c3.metric("Savings rate", f"{savings_rate_ss*100:.1f}%")
        c4.metric("Buffer (months)", f"{buffer_months_ss:.1f}")

        if score_int >= 75:
            st.success("Excellent financial health. You are well-positioned.")
        elif score_int >= 55:
            st.info("Moderate health. Small improvements can strengthen your buffer.")
        elif score_int >= 40:
            st.warning("Fragile finances. Focus on reducing fixed costs or boosting income.")
        else:
            st.error("High financial stress. Immediate action recommended.")

        st.markdown("</div>", unsafe_allow_html=True)

        # ========================================
        # Analytics upgrade 2.1: Expense pressure
        # ========================================
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Expense pressure indicators")

        if total_income <= 0:
            st.info("We need positive income to compute pressure ratios.")
        else:
            rent_r = rent / total_income
            food_r = food / total_income
            transport_r = transport / total_income

            rent_flag = pressure_band(rent_r, green_max=0.30, yellow_max=0.40)
            food_flag = pressure_band(food_r, green_max=0.15, yellow_max=0.25)
            transport_flag = pressure_band(transport_r, green_max=0.10, yellow_max=0.20)

            p1, p2, p3 = st.columns(3)
            with p1:
                st.metric("Rent % of income", f"{rent_r*100:.1f}%")
                if rent_flag == "Healthy":
                    st.success("Green: healthy")
                elif rent_flag == "Risky":
                    st.warning("Yellow: risky")
                else:
                    st.error("Red: dangerous")

            with p2:
                st.metric("Food % of income", f"{food_r*100:.1f}%")
                if food_flag == "Healthy":
                    st.success("Green: healthy")
                elif food_flag == "Risky":
                    st.warning("Yellow: risky")
                else:
                    st.error("Red: dangerous")

            with p3:
                st.metric("Transport % of income", f"{transport_r*100:.1f}%")
                if transport_flag == "Healthy":
                    st.success("Green: healthy")
                elif transport_flag == "Risky":
                    st.warning("Yellow: risky")
                else:
                    st.error("Red: dangerous")

            st.caption("Why it matters: this mirrors underwriting logic. Ratios show pressure better than raw amounts.")

        st.markdown("</div>", unsafe_allow_html=True)

        # ========================================
        # Analytics upgrade 2.2: Trend insights
        # ========================================
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Trend insights (light forecasting)")

        history = st.session_state.get("calc_history", [])
        hist_df = pd.DataFrame(history)

        if len(hist_df) >= 3:
            hist_df["rolling_balance_3"] = hist_df["balance"].rolling(3).mean()
            rolling_3 = float(hist_df.iloc[-1]["rolling_balance_3"])
            st.write(f"3-run rolling average balance: {money(rolling_3)}")
        else:
            st.write("3-run rolling average balance: run the calculator at least 3 times to unlock this.")

        projected_6m = balance * 6
        st.write(f"Simple projection: if you keep this monthly balance, in 6 months you could be at {money(projected_6m)}")

        st.markdown("</div>", unsafe_allow_html=True)

        # ========================================
        # Analytics upgrade 2.3: Risk flags
        # ========================================
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Risk flags")

        risk_msgs = []

        if total_income > 0 and (rent / total_income) > 0.40:
            risk_msgs.append("Rent shock risk: rent is above 40% of income.")

        if float(st.session_state.get("buffer_months", 0) or 0) < 1:
            risk_msgs.append("Zero buffer risk: less than 1 month of expenses as buffer.")

        if len(hist_df) >= 4:
            bal_std = float(hist_df["balance"].std())
            bal_mean = float(hist_df["balance"].mean())
            if abs(bal_mean) > 0 and (bal_std / max(abs(bal_mean), 1e-6)) > 0.5:
                risk_msgs.append("Income volatility: your balance swings a lot between runs.")

        if not risk_msgs:
            st.success("No major risk flags triggered based on current rules.")
        else:
            for m in risk_msgs:
                st.warning(m)

        st.markdown("</div>", unsafe_allow_html=True)

        # Charts
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Charts")

        ch1, ch2 = st.columns(2)

        with ch1:
            comparison_df = pd.DataFrame({
                "Category": ["Total Income", "Total Expenses"],
                "Amount": [total_income, total_expenses],
            })
            fig = px.bar(comparison_df, x="Category", y="Amount", text="Amount", title="Income vs Essential Expenses")
            fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_yaxes(range=[0, max(total_income, total_expenses) * 1.25])
            fig.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            exp_df = pd.DataFrame({
                "Expense": ["rent", "utilities", "food", "transport", "phone_internet", "misc_basic"],
                "Amount": [rent, utilities, food, transport, phone_internet, misc_basic],
            })
            fig2 = px.bar(exp_df, x="Expense", y="Amount", text="Amount", title="Expense Breakdown")
            fig2.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig2.update_yaxes(range=[0, max(exp_df["Amount"]) * 1.25])
            fig2.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # -----------------------------
        # Scenario Simulator + Save scenarios
        # -----------------------------
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Scenario Simulator")
    st.caption(
        "Try quick what-ifs without changing the form above "
        "(extra work hours, rent change, extra income)."
    )

    # Controls for the scenario
    s1, s2, s3 = st.columns(3)
    with s1:
        extra_hours = st.slider(
            "Extra work hours per week",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=1.0,
            help="Simulate taking a few more hours at the same wage.",
        )
    with s2:
        rent_change = st.slider(
            "Rent change ($/month)",
            min_value=-500.0,
            max_value=500.0,
            value=0.0,
            step=25.0,
            help="Negative = cheaper rent, positive = more expensive.",
        )
    with s3:
        extra_income = st.slider(
            "Extra monthly income ($)",
            min_value=0.0,
            max_value=1000.0,
            value=0.0,
            step=50.0,
            help="Any extra monthly money (research job, scholarship, etc.).",
        )

    # Need a successful calculator run first
    base_weekly_job_income = st.session_state.get("weekly_job_income")
    base_wage = st.session_state.get("wage")
    weeks_per_month = st.session_state.get("weeks_per_month")
    stipend = st.session_state.get("stipend")
    base_total_income = st.session_state.get("total_income")
    base_total_expenses = st.session_state.get("total_expenses")
    base_balance = st.session_state.get("balance")

    rent = st.session_state.get("rent")
    utilities = st.session_state.get("utilities")
    food = st.session_state.get("food")
    transport = st.session_state.get("transport")
    phone_internet = st.session_state.get("phone_internet")
    misc_basic = st.session_state.get("misc_basic")

    # Smart empty state if user has never clicked Calculate
    if (
        base_weekly_job_income is None
        or base_wage is None
        or weeks_per_month is None
        or base_total_income is None
        or base_total_expenses is None
        or base_balance is None
        or rent is None
    ):
        st.info("Run the Calculator and click Calculate once to unlock the Scenario Simulator.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Recalculate scenario based on sliders
        scenario_weekly_job_income = float(base_weekly_job_income) + (float(base_wage) * float(extra_hours))
        scenario_monthly_job_income = scenario_weekly_job_income * float(weeks_per_month)

        # Adjust rent but never below zero
        scenario_rent = max(float(rent) + float(rent_change), 0.0)

        scenario_total_expenses = (
            scenario_rent
            + float(utilities)
            + float(food)
            + float(transport)
            + float(phone_internet)
            + float(misc_basic)
        )

        scenario_total_income = float(scenario_monthly_job_income) + float(stipend) + float(extra_income)
        scenario_balance = scenario_total_income - scenario_total_expenses

        delta_balance = scenario_balance - float(base_balance)

        # Display scenario vs current
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Scenario income / month",
            money(scenario_total_income),
            delta=money(scenario_total_income - float(base_total_income)),
        )
        c2.metric(
            "Scenario expenses / month",
            money(scenario_total_expenses),
            delta=money(scenario_total_expenses - float(base_total_expenses)),
        )
        c3.metric(
            "Scenario balance / month",
            money(scenario_balance),
            delta=money(delta_balance),
        )

        if delta_balance > 0:
            st.success("This scenario improves your monthly balance.")
        elif delta_balance < 0:
            st.warning("This scenario reduces your monthly balance.")
        else:
            st.info("This scenario keeps your balance the same.")

        st.markdown("</div>", unsafe_allow_html=True)

        preset = st.selectbox("Scenario name", ["Current plan", "Optimized plan", "Worst case", "Custom"])
        custom_name = ""
        if preset == "Custom":
            custom_name = st.text_input("Custom scenario name")

        scenario_name = custom_name.strip() if preset == "Custom" else preset
        if not scenario_name:
            scenario_name = "Saved scenario"

        if st.button("Save scenario"):
            st.session_state["saved_scenarios"].append({
                "name": scenario_name,
                "city": calc_city,
                "income": float(scenario_total_income),
                "expenses": float(scenario_total_expenses),
                "balance": float(scenario_balance),
            })
            st.success("Scenario saved.")

        if st.session_state["saved_scenarios"]:
            saved_df = pd.DataFrame(st.session_state["saved_scenarios"])
            saved_df = saved_df.rename(columns={
                "name": "Scenario",
                "city": "City",
                "income": "Income",
                "expenses": "Expenses",
                "balance": "Balance",
            })
            st.dataframe(saved_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No saved scenarios yet.")

        st.markdown("</div>", unsafe_allow_html=True)

        # Download
        result_row = {
            "city": calc_city,
            "min_wage": wage,
            "weeks_per_month": weeks_per_month,
            "hours_mon_fri": hours_mon_fri,
            "hours_sat": hours_sat,
            "hours_sun": hours_sun,
            "sunday_multiplier": sunday_multiplier,
            "monthly_job_income_est": monthly_job_income_est,
            "stipend": stipend,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "status": status,
            "rent": rent,
            "utilities": utilities,
            "food": food,
            "transport": transport,
            "phone_internet": phone_internet,
            "misc_basic": misc_basic,
        }
        out_df = pd.DataFrame([result_row])
        csv_bytes = out_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download your calculation as CSV",
            data=csv_bytes,
            file_name=f"{calc_city}_calculator_result.csv",
            mime="text/csv",
            key="calc_download_csv",
        )

# ---------------------------------------------------------
# PAGE B: CITY COMPARE (reads CSV)
# ---------------------------------------------------------
elif page == "City Compare":

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("City Comparison (CSV)")
    st.markdown("<div class='small-note'>Compare cities across a selected month range.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    data = safe_read_csv("data/student_costs.csv")
    if data is None:
        st.error("Could not read data/student_costs.csv. Make sure the file exists.")
        st.stop()

    required_cols = {
        "city", "month", "campus_job_income", "stipend_income",
        "rent", "utilities", "food", "transport",
        "phone_internet", "misc_basic"
    }
    missing = required_cols - set(data.columns)
    if missing:
        st.error(f"Your CSV is missing these columns: {sorted(list(missing))}")
        st.stop()

    expense_columns = ["rent", "utilities", "food", "transport", "phone_internet", "misc_basic"]

    # Prep
    data["month_dt"] = pd.to_datetime(data["month"], format="%Y-%m", errors="coerce")
    if data["month_dt"].isna().all():
        st.error("Month parsing failed. Ensure month column is YYYY-MM (example: 2026-01).")
        st.stop()

    data["total_income"] = data["campus_job_income"] + data["stipend_income"]
    data["total_expenses"] = data[expense_columns].sum(axis=1)
    data["balance"] = data["total_income"] - data["total_expenses"]
    data["status"] = data["balance"].apply(financial_status)

    cities = sorted(data["city"].dropna().unique().tolist())
    months_sorted = sorted(data["month"].dropna().unique().tolist())

    if len(cities) < 2:
        st.info("City Compare needs at least 2 cities in your CSV. Add another city row to compare.")
        st.stop()

    f1, f2, f3 = st.columns([1.4, 1.3, 1.3])
    with f1:
        compare_cities = st.multiselect("Cities to compare", cities, default=cities[:2])
    with f2:
        start_month = st.selectbox("Start month", months_sorted, index=0)
    with f3:
        end_month = st.selectbox("End month", months_sorted, index=len(months_sorted) - 1)

    # Smart empty state
    if len(compare_cities) < 2:
        st.info("Select at least 2 cities to unlock comparison insights.")
        st.stop()

    start_dt = pd.to_datetime(start_month, format="%Y-%m", errors="coerce")
    end_dt = pd.to_datetime(end_month, format="%Y-%m", errors="coerce")
    if pd.isna(start_dt) or pd.isna(end_dt) or start_dt > end_dt:
        st.error("Invalid month range. Check Start and End month.")
        st.stop()

    filt = data[(data["city"].isin(compare_cities)) & (data["month_dt"] >= start_dt) & (data["month_dt"] <= end_dt)].copy()
    if filt.empty:
        st.warning("No rows found for the selected cities and month range.")
        st.stop()

    summary = (
        filt.groupby("city", as_index=False)
            .agg(
                avg_income=("total_income", "mean"),
                avg_expenses=("total_expenses", "mean"),
                avg_balance=("balance", "mean"),
                months=("month", "nunique"),
            )
    )
    summary["savings_rate"] = summary.apply(
        lambda r: (r["avg_balance"] / r["avg_income"]) if r["avg_income"] else 0.0, axis=1
    )

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### KPI Tiles (Average per month)")
    cols = st.columns(min(4, len(summary)))
    for i, row in summary.iterrows():
        col = cols[i % len(cols)]
        with col:
            st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-label'>{row['city']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-value'>{money(row['avg_balance'])}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-sub'>Avg income {money(row['avg_income'])}  |  Avg expenses {money(row['avg_expenses'])}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-sub'>Months: {int(row['months'])}  |  Savings rate: {row['savings_rate']*100:.1f}%</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.6, 1.0])

    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Balance Trend (by city)")
        trend = (
            filt.groupby(["month_dt", "city"], as_index=False)
                .agg(balance=("balance", "mean"))
                .sort_values(["month_dt", "city"])
        )
        fig = px.line(trend, x="month_dt", y="balance", color="city", markers=True)
        fig.update_layout(xaxis_title="Month", yaxis_title="Balance (USD)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Expense Mix (selected range)")

        exp_mix = filt.groupby("city", as_index=False)[expense_columns].sum()
        donut_city = st.selectbox("Donut city", compare_cities, index=0)
        row = exp_mix[exp_mix["city"] == donut_city]

        if not row.empty:
            donut_df = pd.DataFrame({
                "Expense": expense_columns,
                "Amount": [float(row[col].iloc[0]) for col in expense_columns]
            })
            fig2 = px.pie(donut_df, names="Expense", values="Amount", hole=0.55)
            fig2.update_layout(title=f"{donut_city}: Total expenses by category")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No expense data for donut.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Compare Table")
    show = summary.sort_values("avg_balance", ascending=False).copy()
    show["avg_income"] = show["avg_income"].round(0)
    show["avg_expenses"] = show["avg_expenses"].round(0)
    show["avg_balance"] = show["avg_balance"].round(0)
    show["savings_rate"] = (show["savings_rate"] * 100).round(1)
    show = show.rename(columns={
        "avg_income": "Avg Income",
        "avg_expenses": "Avg Expenses",
        "avg_balance": "Avg Balance",
        "months": "Months",
        "savings_rate": "Savings Rate (%)",
    })
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE C: MY PLAN (upgraded)
# ---------------------------------------------------------
elif page == "My Plan":
    st.subheader("My Plan")

    # Smart empty state
    if st.session_state.get("total_income") is None:
        st.info("Run Calculator to activate planning. Once you run it, this page will use your real monthly balance.")
        st.stop()

    goal_amount = float(st.session_state["goal_amount"])
    deadline = st.session_state["goal_deadline"]
    monthly_balance = float(st.session_state.get("balance", 0.0))
    today = date.today()

    current_savings = st.number_input(
        "Current savings toward this goal ($)",
        min_value=0.0,
        step=50.0,
        value=float(st.session_state.get("current_savings", 0.0)),
        key="current_savings",
    )

    days_left = max((deadline - today).days, 1)
    weeks_left = days_left / 7.0
    weekly_target = goal_amount / weeks_left if weeks_left > 0 else 0.0

    st.markdown("#### Weekly savings target")
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.metric("Goal amount", f"${goal_amount:,.0f}")
    with g2:
        st.metric("Current savings", f"${current_savings:,.0f}")
    with g3:
        st.metric("Weeks left", f"{weeks_left:,.1f}")
    with g4:
        st.metric("Weekly target", f"${weekly_target:,.0f}")

    st.markdown("---")
    st.markdown("#### Progress tracking")

    remaining = max(goal_amount - current_savings, 0.0)
    progress_pct = pct(current_savings, goal_amount) if goal_amount > 0 else 0.0
    st.progress(min(progress_pct / 100.0, 1.0))

    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("Progress", f"{progress_pct:.1f}%")
    with p2:
        st.metric("Remaining", f"${remaining:,.0f}")
    with p3:
        st.metric("Time left (days)", f"{days_left}")

    st.markdown("---")
    st.markdown("#### Am I on track?")

    weekly_from_balance = monthly_balance / 4.33 if monthly_balance else 0.0
    delta_weekly = weekly_from_balance - weekly_target

    if monthly_balance <= 0:
        st.error("Your current budget is not saving anything. Fix the Calculator first, then come back here.")
    elif delta_weekly >= 0:
        st.success(
            f"On track. Estimated weekly saving from your budget is ${weekly_from_balance:,.0f}, "
            f"target is ${weekly_target:,.0f}."
        )
    else:
        st.warning(
            f"Short by about ${abs(delta_weekly):,.0f} per week. Small cuts or extra hours can close this."
        )

    st.markdown("---")
    st.markdown("#### Actionable cut suggestions (ranked)")

    total_income = float(st.session_state.get("total_income", 0.0))
    expenses = {
        "Rent": st.session_state.get("rent"),
        "Utilities": st.session_state.get("utilities"),
        "Food": st.session_state.get("food"),
        "Transport": st.session_state.get("transport"),
        "Phone/Internet": st.session_state.get("phone_internet"),
        "Misc basics": st.session_state.get("misc_basic"),
    }

    if total_income <= 0 or any(v is None for v in expenses.values()):
        st.info("Run Calculator first so we can rank your expenses and suggest cuts.")
    else:
        rows = []
        for name, val in expenses.items():
            val_f = float(val)
            share = pct(val_f, total_income)
            rows.append({"Expense": name, "Amount": val_f, "Share Of Income": share})

        exp_df = pd.DataFrame(rows).sort_values("ShareOfIncome", ascending=False)

        show_df = exp_df.copy()
        show_df["Amount"] = show_df["Amount"].round(0)
        show_df["ShareOfIncome"] = show_df["ShareOfIncome"].round(1)
        st.dataframe(show_df, use_container_width=True, hide_index=True)

        top2 = exp_df.head(2)
        st.markdown("**Top 2 cut ideas (example: 10% cut each)**")
        for _, r in top2.iterrows():
            cut_amount = 0.10 * float(r["Amount"])
            new_balance = monthly_balance + cut_amount
            st.markdown(
                f"- Cut **${cut_amount:,.0f}** from **{r['Expense']} (about 10%)** "
                f"and your monthly balance could move from **{money(monthly_balance)}** to **{money(new_balance)}**)."
            )

    st.markdown("---")
    st.markdown("#### Next actions")
    st.write("- Re-run Calculator if your hours or rent change.")
    st.write("- Use City Compare to test which city gives a better long-run balance.")
    st.write("- Adjust your goal or deadline if the weekly target is unrealistic.")

# ---------------------------------------------------------
# PAGE D: SETTINGS
# ---------------------------------------------------------
elif page == "Settings":
    st.subheader("Settings")
    st.info("Preferences and configuration coming soon.")
