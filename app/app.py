# =========================================================
# 1) IMPORTS 
# =========================================================
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from datetime import date, timedelta


# =========================================================
# 2) SESSION DEFAULTS (GLOBAL SNAPSHOT)
# =========================================================
if "status" not in st.session_state:
    st.session_state["status"] = "Unknown"
if "balance" not in st.session_state:
    st.session_state["balance"] = 0.0
if "context_city" not in st.session_state:
    st.session_state["context_city"] = "-"

# Calculator snapshot values
if "total_income" not in st.session_state:
    st.session_state["total_income"] = None
if "total_expenses" not in st.session_state:
    st.session_state["total_expenses"] = None
if "weekly_job_income" not in st.session_state:
    st.session_state["weekly_job_income"] = None

# Goal settings for "My Plan"
if "goal_amount" not in st.session_state:
    st.session_state["goal_amount"] = 1000.0
if "goal_deadline" not in st.session_state:
    st.session_state["goal_deadline"] = date.today() + timedelta(days=90)

# City Compare sidebar controls
if "compare_metric" not in st.session_state:
    st.session_state["compare_metric"] = "Balance"
if "month_preset" not in st.session_state:
    st.session_state["month_preset"] = "All data"

# Financial health score
if "health_score" not in st.session_state:
    st.session_state["health_score"] = 0
if "rent_ratio" not in st.session_state:
    st.session_state["rent_ratio"] = None
if "savings_rate" not in st.session_state:
    st.session_state["savings_rate"] = None
if "buffer_months" not in st.session_state:
    st.session_state["buffer_months"] = 0.0

# Saved scenarios
if "saved_scenarios" not in st.session_state:
    st.session_state["saved_scenarios"] = []

# Scenario picker on My Plan
if "plan_scenario_choice" not in st.session_state:
    st.session_state["plan_scenario_choice"] = "Latest calculator run"

# Optional: first run banner
if "first_run" not in st.session_state:
    st.session_state["first_run"] = True


# =========================================================
# 3) PAGE CONFIG (must be before most Streamlit calls)
# =========================================================
st.set_page_config(
    page_title="Student Cost Survival Dashboard",
    layout="wide",
)


# =========================================================
# 4) STYLING (CSS) - applies early
# =========================================================
st.markdown(
    """
<style>
.block-container {
    padding-top: 2.2rem;
    max-width: 1300px;
}

/* Generic card */
.card {
    padding: 0.9rem 1.0rem;
    border-radius: 14px;
    background: #020617;
    border: 1px solid #1f2937;
    margin-bottom: 1.0rem;
}

/* Extra section card (same style, different class name) */
.section-card {
    padding: 0.9rem 1.0rem;
    border-radius: 14px;
    background: #020617;
    border: 1px solid #1f2937;
    margin-bottom: 1.0rem;
}

/* Small note */
.small-note {opacity: 0.78; font-size: 0.92rem; margin-top: 0.15rem;}

/* KPI cards */
.kpi-card {
    padding: 0.8rem 0.9rem;
    border-radius: 12px;
    background: #020617;
    border: 1px solid #1f2937;
    margin-bottom: 0.7rem;
}
.kpi-label { font-size: 0.82rem; opacity: 0.85; }
.kpi-value { font-size: 1.55rem; font-weight: 650; margin-top: 0.2rem; }
.kpi-sub   { font-size: 0.8rem; opacity: 0.75; margin-top: 0.2rem; }

/* Add a bit of vertical spacing for widgets */
div[data-testid="stVerticalBlock"] > div { margin-bottom: 0.35rem; }
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# 5) CONSTANTS + HELPERS
# =========================================================

CITY_MIN_WAGE = {
    "Saint Louis": 12.30,
    "Chicago": 15.80,
    "New York City": 16.00,
    "Los Angeles": 16.90,
}

DEFAULT_CITY = "Saint Louis" if "Saint Louis" in CITY_MIN_WAGE else list(CITY_MIN_WAGE.keys())[0]


def financial_status(balance: float) -> str:
    if balance > 0:
        return "Surplus"
    if balance == 0:
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


def financial_health_score(total_income: float, total_expenses: float, rent: float, balance: float):
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

    # 2) Rent health (0–25): best around <=35%, fades to 0 at 60%+
    rent_points = 25 * (0.60 - rent_ratio) / (0.60 - 0.35)
    rent_points = int(round(clamp(rent_points, 0, 25)))

    # 3) Savings rate (0–20): full points at 10%+ savings
    savings_points = 20 * (savings_rate / 0.10)
    savings_points = int(round(clamp(savings_points, 0, 20)))

    # 4) Buffer (0–15): scale by months of buffer (balance / expenses)
    buffer_months = (balance / total_expenses) if total_expenses > 0 else 0.0
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
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Risky"
    return "Critical"


# =========================================================
# 6) SIDEBAR: NAV + SNAPSHOT + CONTROLS
# =========================================================
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
                "padding": "0.48rem 0.85rem",
                "border-radius": "8px",
                "color": "white",
                "margin": "0.12rem 0",
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
        st.caption(f"Rent/Income: {rr*100:.1f}%  •  Savings rate: {sr*100:.1f}%")

    status = st.session_state["status"]
    if status == "Deficit":
        st.info("Tip: Check rent and misc basics. A small cut can flip you positive.")
    elif status == "Break-even":
        st.info("Tip: Try to build at least one month of buffer savings.")
    elif status == "Surplus":
        st.info("Tip: Consider saving or investing part of your surplus.")
    else:
        st.caption("Run the calculator to see a personalized snapshot.")

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

        st.date_input(
            "Goal deadline",
            key="goal_deadline",
        )

        st.caption("Run the Calculator first so this plan uses your real monthly balance.")

    elif page == "Settings":
        st.markdown("#### Preferences (future)")
        st.info("Later you can add currency options, wage presets, and theme settings.")


# =========================================================
# 7) TOP TITLE (all pages)
# =========================================================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.title("International Student Cost Survival Dashboard")
st.markdown(
    "<div class='small-note'>Use the Calculator for personal numbers and City Compare for CSV insights.</div>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# First-time guide banner (optional)
if st.session_state.get("first_run", False):
    st.info("First time here? Step 1: Run Calculator  →  Step 2: Compare Cities  →  Step 3: Build a Plan")
    st.session_state["first_run"] = False


# =========================================================
# 8) PAGE A: CALCULATOR
# =========================================================
if page == "Calculator":

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Personal Calculator")
    st.markdown(
        "<div class='small-note'>Fill the form and click Calculate. We use the city minimum wage to estimate job income.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("calculator_form"):

        top1, top2, top3 = st.columns([1.2, 1, 1])

        with top1:
            calc_city = st.selectbox(
                "City",
                list(CITY_MIN_WAGE.keys()),
                index=list(CITY_MIN_WAGE.keys()).index(DEFAULT_CITY),
            )

        with top2:
            min_wage = CITY_MIN_WAGE.get(calc_city, 15.0)
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
                help="4.33 is the average weeks per month (52 weeks / 12 months).",
            )

        st.write("")
        st.markdown("### Work hours (weekly)")

        h1, h2, h3, h4 = st.columns(4)
        with h1:
            hours_mon_fri = st.number_input("Hours Mon–Fri (total)", min_value=0.0, value=20.0, step=1.0)
        with h2:
            hours_sat = st.number_input("Hours Saturday", min_value=0.0, value=0.0, step=1.0)
        with h3:
            hours_sun = st.number_input("Hours Sunday", min_value=0.0, value=0.0, step=1.0)
        with h4:
            sunday_multiplier = st.number_input(
                "Sunday pay multiplier",
                min_value=1.0,
                value=1.0,
                step=0.25,
                help="If Sunday is paid higher (e.g., 1.5x or 2x), set it here.",
            )

        st.write("")
        st.markdown("### Other monthly income")
        stipend = st.number_input("Monthly stipend / support ($)", min_value=0.0, value=0.0, step=50.0)

        st.write("")
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

        st.write("")
        submitted = st.form_submit_button("✅ Calculate")

    if not submitted:
        st.info("Fill the form above and click Calculate to see your budget, charts, and downloads.")
    else:
        # --- Calculations ---
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
            balance=balance,
        )

        # Save snapshot in session
        st.session_state["weekly_job_income"] = float(weekly_job_income)
        st.session_state["total_income"] = float(total_income)
        st.session_state["total_expenses"] = float(total_expenses)
        st.session_state["balance"] = float(balance)
        st.session_state["status"] = status
        st.session_state["context_city"] = calc_city

        st.session_state["health_score"] = int(health_score)
        st.session_state["rent_ratio"] = score_breakdown["rent_ratio"]
        st.session_state["savings_rate"] = score_breakdown["savings_rate"]
        st.session_state["buffer_months"] = float(score_breakdown.get("buffer_months", 0.0))

        # --- Results card ---
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Results")
        st.write("")

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("City", calc_city)
        r2.metric("Min wage", f"${wage:.2f}/hr")
        r3.metric("Monthly job income (est.)", money(monthly_job_income))
        r4.metric("Monthly stipend", money(stipend))

        st.write("")
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Income", money(total_income))
        k2.metric("Total Expenses", money(total_expenses))
        k3.metric("Balance", money(balance))

        st.write("")
        if status == "Surplus":
            st.success("Surplus: you have buffer after essentials.")
        elif status == "Break-even":
            st.warning("Break-even: you are surviving, but no buffer.")
        else:
            st.error("Deficit: you will likely need support or expense cuts.")

        st.markdown("</div>", unsafe_allow_html=True)

        # --- Financial Health Score ---
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Financial Health Score")
        st.write("")

        score = int(st.session_state.get("health_score", 0))
        rent_ratio = st.session_state.get("rent_ratio", 0) or 0
        savings_rate = st.session_state.get("savings_rate", 0) or 0
        buffer_months = st.session_state.get("buffer_months", 0) or 0

        st.progress(max(0, min(score, 100)))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score", f"{score}/100")
        c2.metric("Rent / Income", f"{rent_ratio*100:.1f}%")
        c3.metric("Savings rate", f"{savings_rate*100:.1f}%")
        c4.metric("Buffer (months)", f"{buffer_months:.1f}")

        st.write("")
        if score >= 75:
            st.success("Excellent financial health. You are well-positioned.")
        elif score >= 55:
            st.info("Moderate health. Small improvements can strengthen your buffer.")
        elif score >= 40:
            st.warning("Fragile finances. Focus on reducing fixed costs or boosting income.")
        else:
            st.error("High financial stress. Immediate action recommended.")

        st.markdown("</div>", unsafe_allow_html=True)

        # --- Charts ---
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Charts")
        st.write("")

        ch1, ch2 = st.columns(2)

        with ch1:
            comparison_df = pd.DataFrame(
                {"Category": ["Total Income", "Total Expenses"], "Amount": [total_income, total_expenses]}
            )
            fig = px.bar(comparison_df, x="Category", y="Amount", text="Amount", title="Income vs Essential Expenses")
            fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_yaxes(range=[0, max(total_income, total_expenses) * 1.25])
            fig.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            exp_df = pd.DataFrame(
                {
                    "Expense": ["rent", "utilities", "food", "transport", "phone_internet", "misc_basic"],
                    "Amount": [rent, utilities, food, transport, phone_internet, misc_basic],
                }
            )
            fig2 = px.bar(exp_df, x="Expense", y="Amount", text="Amount", title="Expense Breakdown")
            fig2.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig2.update_yaxes(range=[0, max(exp_df["Amount"]) * 1.25])
            fig2.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # --- Scenario Simulator (quick what-ifs) ---
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Scenario Simulator")
        st.caption("Try quick what-ifs without changing the form above (extra hours, rent change, extra income).")
        st.write("")

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
                help="Negative means cheaper rent. Positive means more expensive.",
            )
        with s3:
            extra_income = st.slider(
                "Extra monthly income ($)",
                min_value=0.0,
                max_value=1000.0,
                value=0.0,
                step=50.0,
                help="Extra monthly money (research job, scholarship, etc.).",
            )

        scenario_weekly_job_income = weekly_job_income + (wage * extra_hours)
        scenario_monthly_job_income = scenario_weekly_job_income * weeks_per_month

        scenario_rent = max(rent + rent_change, 0)

        scenario_total_expenses = (
            scenario_rent + utilities + food + transport + phone_internet + misc_basic
        )
        scenario_total_income = scenario_monthly_job_income + stipend + extra_income
        scenario_balance = scenario_total_income - scenario_total_expenses

        delta_balance = scenario_balance - balance

        st.write("")
        m1, m2, m3 = st.columns(3)
        m1.metric("Scenario income / month", money(scenario_total_income), delta=money(scenario_total_income - total_income))
        m2.metric(
            "Scenario expenses / month",
            money(scenario_total_expenses),
            delta=money(scenario_total_expenses - total_expenses),
        )
        m3.metric("Scenario balance / month", money(scenario_balance), delta=money(delta_balance))

        st.write("")
        if delta_balance > 0:
            st.success("This scenario improves your monthly balance.")
        elif delta_balance < 0:
            st.warning("This scenario reduces your monthly balance.")
        else:
            st.info("This scenario keeps your balance the same.")

        st.markdown("</div>", unsafe_allow_html=True)

        # --- Save scenario (for My Plan) ---
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Save this calculation")
        st.caption("Save this result so you can use it later in My Plan.")
        st.write("")

        default_name = f"{calc_city} ({status})"
        scenario_name = st.text_input("Scenario name", value=default_name, key="scenario_name_input")

        st.write("")
        left, right = st.columns([1, 2])
        with left:
            if st.button("💾 Save scenario", key="save_scenario_button"):
                name_clean = scenario_name.strip()
                if not name_clean:
                    st.warning("Please enter a scenario name before saving.")
                else:
                    st.session_state["saved_scenarios"].append(
                        {
                            "name": name_clean,
                            "city": calc_city,
                            "status": status,
                            "total_income": float(total_income),
                            "total_expenses": float(total_expenses),
                            "balance": float(balance),
                            "health_score": int(health_score),
                        }
                    )
                    st.success(f"Saved: {name_clean}")

        with right:
            count_saved = len(st.session_state.get("saved_scenarios", []))
            st.caption(f"Saved scenarios: {count_saved}")

        st.markdown("</div>", unsafe_allow_html=True)

        # --- Download CSV (current run only) ---
        result_row = {
            "city": calc_city,
            "min_wage": wage,
            "weeks_per_month": weeks_per_month,
            "hours_mon_fri": hours_mon_fri,
            "hours_sat": hours_sat,
            "hours_sun": hours_sun,
            "sunday_multiplier": sunday_multiplier,
            "weekly_job_income_est": weekly_job_income,
            "monthly_job_income_est": monthly_job_income,
            "stipend": stipend,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "status": status,
            "health_score": health_score,
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


# =========================================================
# 9) PAGE B: CITY COMPARE (reads CSV)
# =========================================================
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

    f1, f2, f3 = st.columns([1.4, 1.3, 1.3])
    with f1:
        compare_cities = st.multiselect(
            "Cities to compare",
            cities,
            default=cities[:2] if len(cities) >= 2 else cities,
        )
    with f2:
        start_month = st.selectbox("Start month", months_sorted, index=0)
    with f3:
        end_month = st.selectbox("End month", months_sorted, index=len(months_sorted) - 1)

    if len(compare_cities) < 2:
        st.info("Select at least 2 cities to compare.")
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
        lambda r: (r["avg_balance"] / r["avg_income"]) if r["avg_income"] else 0.0,
        axis=1,
    )

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### KPI Tiles (Average per month)")
    st.write("")

    cols = st.columns(min(4, len(summary)))
    for i, row in summary.iterrows():
        col = cols[i % len(cols)]
        with col:
            st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-label'>{row['city']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-value'>{money(row['avg_balance'])}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='kpi-sub'>Avg income {money(row['avg_income'])}  •  Avg expenses {money(row['avg_expenses'])}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='kpi-sub'>Months: {int(row['months'])}  •  Savings rate: {row['savings_rate']*100:.1f}%</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.6, 1.0])

    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Balance Trend (by city)")
        st.write("")

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
        st.write("")

        exp_mix = filt.groupby("city", as_index=False)[expense_columns].sum()
        donut_city = st.selectbox("Donut city", compare_cities, index=0)
        row = exp_mix[exp_mix["city"] == donut_city]

        if not row.empty:
            donut_df = pd.DataFrame(
                {"Expense": expense_columns, "Amount": [float(row[col].iloc[0]) for col in expense_columns]}
            )
            fig2 = px.pie(donut_df, names="Expense", values="Amount", hole=0.55)
            fig2.update_layout(title=f"{donut_city}: Total expenses by category")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No expense data for donut.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Compare Table")
    st.write("")

    show = summary.sort_values("avg_balance", ascending=False).copy()
    show["avg_income"] = show["avg_income"].round(0)
    show["avg_expenses"] = show["avg_expenses"].round(0)
    show["avg_balance"] = show["avg_balance"].round(0)
    show["savings_rate"] = (show["savings_rate"] * 100).round(1)

    show = show.rename(
        columns={
            "avg_income": "Avg Income",
            "avg_expenses": "Avg Expenses",
            "avg_balance": "Avg Balance",
            "months": "Months",
            "savings_rate": "Savings Rate (%)",
        }
    )
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 10) PAGE C: MY PLAN (uses selected scenario balance)
# =========================================================
elif page == "My Plan":

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("My Plan")
    st.caption("Pick a scenario and let the plan use its monthly balance for your goal.")
    st.markdown("</div>", unsafe_allow_html=True)

    saved = st.session_state.get("saved_scenarios", [])

    latest_balance = float(st.session_state.get("balance", 0.0))
    latest_status = st.session_state.get("status", "Unknown")
    has_latest = (latest_status != "Unknown") or (latest_balance != 0)

    options = []
    if has_latest:
        options.append("Latest calculator run")
    for s in saved:
        options.append(f"{s['name']} ({s['city']}, {s['status']})")

    if not options:
        st.info("Run the Calculator first. Then you can save scenarios and plan here.")
        st.stop()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Choose a scenario")
    st.write("")

    selected_label = st.selectbox(
        "Use this scenario for planning",
        options,
        key="plan_scenario_choice",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if selected_label == "Latest calculator run":
        active_balance = latest_balance
        active_name = "Latest calculator run"
        active_status = latest_status
    else:
        offset = 1 if has_latest else 0
        idx = options.index(selected_label) - offset
        chosen = saved[idx]
        active_balance = float(chosen["balance"])
        active_name = chosen["name"]
        active_status = chosen["status"]

    goal_amount = float(st.session_state["goal_amount"])
    deadline = st.session_state["goal_deadline"]
    today = date.today()

    days_left = max((deadline - today).days, 1)
    weeks_left = days_left / 7.0
    weekly_target = goal_amount / weeks_left if weeks_left > 0 else 0.0

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Goal summary")
    st.write("")

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Goal", f"${goal_amount:,.0f}")
    g2.metric("Weeks left", f"{weeks_left:.1f}")
    g3.metric("Target per week", f"${weekly_target:,.0f}")
    g4.metric("Using scenario", active_name)

    st.caption(f"Scenario status: {active_status}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Am I on track?")
    st.write("")

    monthly_balance = active_balance
    weekly_from_balance = monthly_balance / 4.33 if monthly_balance else 0.0
    gap = weekly_from_balance - weekly_target

    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly balance used", f"${monthly_balance:,.0f}")
    c2.metric("Estimated saving per week", f"${weekly_from_balance:,.0f}")
    c3.metric("Gap vs target (per week)", f"${gap:,.0f}")

    st.write("")
    if monthly_balance <= 0:
        st.error("This scenario is not saving money. Improve the Calculator numbers or pick a surplus scenario.")
    elif gap >= 0:
        st.success("You are on track with this scenario.")
    else:
        st.warning("You are short with this scenario. Consider small cuts or adding work hours.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Next actions")
    st.write("")
    st.write("• Re-run Calculator if rent, hours, or stipend changes.")
    st.write("• Save multiple scenarios: Current plan, Optimized plan, Worst case.")
    st.write("• Use City Compare to test where balance is stronger.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Saved scenarios")
    st.write("")

    if not saved:
        st.info("No saved scenarios yet. Go to Calculator and click Save scenario after Calculate.")
    else:
        df = pd.DataFrame(saved).copy()
        df["total_income"] = df["total_income"].round(0)
        df["total_expenses"] = df["total_expenses"].round(0)
        df["balance"] = df["balance"].round(0)

        df = df.rename(
            columns={
                "name": "Scenario",
                "city": "City",
                "status": "Status",
                "total_income": "Total income",
                "total_expenses": "Total expenses",
                "balance": "Balance",
                "health_score": "Health score",
            }
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 11) PAGE D: SETTINGS
# =========================================================
elif page == "Settings":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Settings")
    st.caption("Preferences and configuration coming soon.")
    st.markdown("</div>", unsafe_allow_html=True)
