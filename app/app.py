# =========================================================
# app.py  (rewritten with saved calculations + My Plan link)
# =========================================================

# 1) IMPORTS
# =========================================================
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from datetime import date, timedelta, datetime


# =========================================================
# 2) SESSION DEFAULTS
# =========================================================
def init_defaults():
    defaults = {
        "status": "Unknown",
        "balance": 0.0,
        "context_city": "-",
        "goal_amount": 1000.0,
        "goal_deadline": date.today() + timedelta(days=90),
        "compare_metric": "Balance",
        "month_preset": "All data",
        "health_score": 0,
        "rent_ratio": None,
        "savings_rate": None,
        "buffer_months": 0.0,
        "first_run": True,
        "calc_ready": False,

        # history (for trends) and saved named calculations (for My Plan)
        "calc_history": [],
        "saved_calcs": [],
        "active_saved_calc_id": None,

        # values needed for scenario simulator + download
        "weekly_job_income": None,
        "monthly_job_income": None,
        "wage": None,
        "weeks_per_month": None,
        "stipend": None,
        "total_income": None,
        "total_expenses": None,

        "rent": None,
        "utilities": None,
        "food": None,
        "transport": None,
        "phone_internet": None,
        "misc_basic": None,

        # My Plan extra
        "current_saved": 0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_defaults()


# =========================================================
# 3) PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Student Cost Survival Dashboard", layout="wide")


# =========================================================
# 4) STYLING (CSS)
# =========================================================
st.markdown(
    """
<style>
.block-container {
    padding-top: 3.5rem;
    max-width: 1300px;
}
.card {
    padding: 1.0rem 1.1rem;
    border-radius: 14px;
    background: #020617;
    border: 1px solid #1f2937;
    margin-bottom: 0.8rem;
}
.section-card {
    padding: 1.0rem 1.1rem;
    border-radius: 14px;
    background: #020617;
    border: 1px solid #1f2937;
    margin-bottom: 1.0rem;
}
.small-note {
    opacity: 0.78;
    font-size: 0.9rem;
    margin-top: 0.25rem;
}
.kpi-card {
    padding: 0.8rem 0.9rem;
    border-radius: 12px;
    background: #020617;
    border: 1px solid #1f2937;
    margin-bottom: 0.8rem;
}
.kpi-label {
    font-size: 0.85rem;
    opacity: 0.8;
}
.kpi-value {
    font-size: 1.6rem;
    font-weight: 600;
    margin-top: 0.2rem;
}
.kpi-sub {
    font-size: 0.8rem;
    opacity: 0.7;
    margin-top: 0.1rem;
}
.pill {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    border: 1px solid #334155;
    font-size: 0.78rem;
    opacity: 0.95;
    margin-left: 0.4rem;
}
.pill-green {background: rgba(34,197,94,0.12); border-color: rgba(34,197,94,0.35);}
.pill-yellow {background: rgba(234,179,8,0.12); border-color: rgba(234,179,8,0.35);}
.pill-red {background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.35);}
hr.soft {
    border: none;
    border-top: 1px solid #1f2937;
    margin: 0.75rem 0;
}
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
    try:
        return f"${float(x):,.0f}"
    except Exception:
        return "$0"


def safe_read_csv(path: str):
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def clamp(n: float, low: float, high: float) -> float:
    return max(low, min(high, n))


def financial_health_score(total_income: float, total_expenses: float, rent: float, balance: float) -> tuple[int, dict]:
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

    balance_points = 40 if balance > 0 else 0

    rent_points = 25 * (0.60 - rent_ratio) / (0.60 - 0.35)
    rent_points = int(round(clamp(rent_points, 0, 25)))

    savings_points = 20 * (savings_rate / 0.10)
    savings_points = int(round(clamp(savings_points, 0, 20)))

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
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Risky"
    return "Critical"


def pressure_flag(share: float) -> tuple[str, str]:
    """
    Returns (label, css_class)
    Thresholds are simple underwriting-style rules of thumb.
    """
    if share <= 0.25:
        return "Healthy", "pill-green"
    if share <= 0.35:
        return "Risky", "pill-yellow"
    return "Danger", "pill-red"


def build_expense_pressure_df(total_income: float, expense_dict: dict) -> pd.DataFrame:
    rows = []
    income = float(total_income) if total_income else 0.0

    for name, amt in expense_dict.items():
        amt_f = float(amt)
        share = (amt_f / income) if income > 0 else 0.0
        label, css = pressure_flag(share)
        rows.append(
            {
                "Expense": name,
                "Amount": amt_f,
                "ShareOfIncome": share,
                "FlagLabel": label,
                "FlagCss": css,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        # Always return with required columns to avoid KeyError later
        return pd.DataFrame(columns=["Expense", "Amount", "ShareOfIncome", "FlagLabel", "FlagCss"])

    return df.sort_values("ShareOfIncome", ascending=False, ignore_index=True)


def make_saved_calc_id() -> str:
    """Simple id for saved calculations."""
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


# =========================================================
# 6) SIDEBAR: NAV + SNAPSHOT + CONTROLS
# =========================================================
with st.sidebar:
    st.markdown("### Student Cost Survival")
    st.write("")

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
    st.write("")

    st.write("Status:", st.session_state["status"])
    st.write("Balance / month:", f"${st.session_state['balance']:.0f}")
    st.caption(f"Based on last calculator run (city: {st.session_state['context_city']})")

    health_score = st.session_state.get("health_score")
    if health_score is not None:
        st.write("Health score:", health_score, f"({score_label(int(health_score))})")

    rr = st.session_state.get("rent_ratio")
    sr = st.session_state.get("savings_rate")
    if rr is not None and sr is not None:
        st.caption(f"Rent/Income: {rr*100:.1f}% • Savings rate: {sr*100:.1f}%")

    status_now = st.session_state["status"]
    st.write("")
    if status_now == "Deficit":
        st.info("Tip: Check rent and misc. Even a small cut can flip you positive.")
    elif status_now == "Break-even":
        st.info("Tip: Try to build at least one month of buffer savings.")
    elif status_now == "Surplus":
        st.info("Good spot. Save or invest part of your surplus.")
    else:
        st.caption("Run the calculator to see a personalized snapshot.")

    if page == "City Compare":
        st.markdown("---")
        st.markdown("#### Compare settings")
        st.write("")
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
        st.markdown("---")
        st.markdown("#### Savings goal")
        st.write("")
        st.number_input("Goal amount ($)", min_value=0.0, step=50.0, key="goal_amount")
        st.date_input("Goal deadline", key="goal_deadline")
        st.number_input("Already saved toward goal ($)", min_value=0.0, step=50.0, key="current_saved")
        st.caption("Use the Calculator first and save a calculation to power your plan.")


# =========================================================
# 7) TOP TITLE
# =========================================================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.title("International Student Cost Survival Dashboard")
st.markdown(
    "<div class='small-note'>Use the Calculator for personal numbers, City Compare for CSV insights, "
    "and My Plan to turn one of your saved calculations into a goal plan.</div>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# Guided first-time banner
if st.session_state.get("first_run", True):
    st.info("Step 1: Run Calculator. Step 2: Save a calculation. Step 3: Build a plan in My Plan.")
    st.session_state["first_run"] = False


# =========================================================
# PAGE A: CALCULATOR
# =========================================================
if page == "Calculator":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Personal Calculator")
    st.markdown(
        "<div class='small-note'>Fill the form and click Calculate. "
        "We use city minimum wage to estimate job income.</div>",
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
            wage = st.number_input("Minimum wage ($/hour)", min_value=0.0, value=float(min_wage), step=0.25)

        with top3:
            weeks_per_month = st.number_input("Weeks per month", min_value=3.0, max_value=5.0, value=4.33, step=0.01)

        st.write("")
        st.markdown("### Work hours (weekly)")
        h1, h2, h3, h4 = st.columns(4)
        with h1:
            # Using "-" instead of long dash here
            hours_mon_fri = st.number_input("Hours Mon-Fri (total)", min_value=0.0, value=20.0, step=1.0)
        with h2:
            hours_sat = st.number_input("Hours Saturday", min_value=0.0, value=0.0, step=1.0)
        with h3:
            hours_sun = st.number_input("Hours Sunday", min_value=0.0, value=0.0, step=1.0)
        with h4:
            sunday_multiplier = st.number_input("Sunday pay multiplier", min_value=1.0, value=1.0, step=0.25)

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

    # Smart empty state
    if not submitted and not st.session_state.get("calc_ready", False):
        st.info(
            "Fill the form above and click Calculate to see your budget, charts, scenario simulator, "
            "and the save option for My Plan."
        )
    elif submitted:
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

        # Persist for scenario + download + My Plan (fixes NameError issues)
        st.session_state["weekly_job_income"] = float(weekly_job_income)
        st.session_state["monthly_job_income"] = float(monthly_job_income)
        st.session_state["wage"] = float(wage)
        st.session_state["weeks_per_month"] = float(weeks_per_month)
        st.session_state["stipend"] = float(stipend)

        st.session_state["total_income"] = float(total_income)
        st.session_state["total_expenses"] = float(total_expenses)
        st.session_state["balance"] = float(balance)
        st.session_state["status"] = status
        st.session_state["context_city"] = calc_city

        st.session_state["health_score"] = int(health_score)
        st.session_state["rent_ratio"] = score_breakdown["rent_ratio"]
        st.session_state["savings_rate"] = score_breakdown["savings_rate"]
        st.session_state["buffer_months"] = float(score_breakdown.get("buffer_months", 0))

        st.session_state["rent"] = float(rent)
        st.session_state["utilities"] = float(utilities)
        st.session_state["food"] = float(food)
        st.session_state["transport"] = float(transport)
        st.session_state["phone_internet"] = float(phone_internet)
        st.session_state["misc_basic"] = float(misc_basic)

        st.session_state["calc_ready"] = True

        # History for light trend insights
        st.session_state["calc_history"].append(
            {
                "run_date": str(date.today()),
                "city": calc_city,
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "balance": float(balance),
            }
        )
        st.session_state["calc_history"] = st.session_state["calc_history"][-12:]  # keep last 12 runs

    # Show results if ready (current or previous run)
    if st.session_state.get("calc_ready", False):
        total_income = float(st.session_state["total_income"])
        total_expenses = float(st.session_state["total_expenses"])
        balance = float(st.session_state["balance"])
        status = st.session_state["status"]
        calc_city = st.session_state["context_city"]

        wage = float(st.session_state["wage"])
        monthly_job_income = float(st.session_state["monthly_job_income"])
        stipend = float(st.session_state["stipend"])

        rent = float(st.session_state["rent"])
        utilities = float(st.session_state["utilities"])
        food = float(st.session_state["food"])
        transport = float(st.session_state["transport"])
        phone_internet = float(st.session_state["phone_internet"])
        misc_basic = float(st.session_state["misc_basic"])

        # Results
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
        k1.metric("Total income", money(total_income))
        k2.metric("Total expenses", money(total_expenses))
        k3.metric("Balance", money(balance))

        st.write("")
        if status == "Surplus":
            st.success("SURPLUS. You have buffer after essentials.")
        elif status == "Break-even":
            st.warning("BREAK-EVEN. You are surviving, but there is no buffer.")
        else:
            st.error("DEFICIT. You will likely need support or expense cuts.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Financial Health Score
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Financial Health Score")
        st.write("")

        score = int(st.session_state.get("health_score", 0))
        rent_ratio = st.session_state.get("rent_ratio") or 0.0
        savings_rate = st.session_state.get("savings_rate") or 0.0
        buffer_months = float(st.session_state.get("buffer_months", 0))

        score_int = int(clamp(score, 0, 100))
        st.progress(score_int)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score", f"{score}/100")
        c2.metric("Rent / income", f"{rent_ratio*100:.1f}%")
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

        # Analytics: Expense pressure + trend + risk flags
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Analytics insights")
        st.write("")

        # 2.1 Expense pressure indicators (ratios)
        expense_dict = {
            "Rent": rent,
            "Food": food,
            "Transport": transport,
        }
        exp_df = build_expense_pressure_df(total_income, expense_dict)  # fixes KeyError ShareOfIncome

        st.markdown("#### Expense pressure indicators")
        st.write("")
        for _, row in exp_df.iterrows():
            share_pct = float(row["ShareOfIncome"]) * 100
            st.markdown(
                f"- **{row['Expense']}**: {money(row['Amount'])} "
                f"({share_pct:.1f}% of income) "
                f"<span class='pill {row['FlagCss']}'>{row['FlagLabel']}</span>",
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown("<hr class='soft'>", unsafe_allow_html=True)

        # 2.2 Trend insights
        st.markdown("#### Trend insights")
        st.write("")
        hist = pd.DataFrame(st.session_state.get("calc_history", []))
        if not hist.empty:
            hist["balance"] = pd.to_numeric(hist["balance"], errors="coerce")
            last3 = hist["balance"].tail(3)
            rolling3 = float(last3.mean()) if len(last3) > 0 else float(balance)
            st.caption(f"3-run rolling average balance: {money(rolling3)}")

        projected_6m = float(balance) * 6
        st.caption(f"Simple projection: At this rate, in 6 months your net change is about {money(projected_6m)}")

        st.write("")
        st.markdown("<hr class='soft'>", unsafe_allow_html=True)

        # 2.3 Risk flags
        st.markdown("#### Risk flags")
        st.write("")
        flags = []

        if total_income > 0 and (rent / total_income) > 0.40:
            flags.append("Rent shock risk (rent is more than 40% of income).")
        if buffer_months <= 0:
            flags.append("Zero buffer risk (no savings cushion).")
        if balance < 0:
            flags.append("Cashflow deficit risk (spending more than you make).")

        if hist.shape[0] >= 4:
            vol = float(hist["balance"].tail(6).std() or 0.0)
            if vol > 200:
                flags.append("Income or expense volatility across recent runs.")

        if flags:
            for f in flags:
                st.warning(f)
        else:
            st.success("No major risk flags triggered from current inputs.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Charts
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Charts")
        st.write("")

        ch1, ch2 = st.columns(2)
        with ch1:
            comparison_df = pd.DataFrame(
                {"Category": ["Total income", "Total expenses"], "Amount": [total_income, total_expenses]}
            )
            fig = px.bar(comparison_df, x="Category", y="Amount", text="Amount", title="Income vs essential expenses")
            fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_yaxes(range=[0, max(total_income, total_expenses) * 1.25])
            fig.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            exp_all_df = pd.DataFrame(
                {
                    "Expense": ["Rent", "Utilities", "Food", "Transport", "Phone/Internet", "Misc basics"],
                    "Amount": [rent, utilities, food, transport, phone_internet, misc_basic],
                }
            )
            fig2 = px.bar(exp_all_df, x="Expense", y="Amount", text="Amount", title="Expense breakdown")
            fig2.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig2.update_yaxes(range=[0, max(exp_all_df["Amount"]) * 1.25])
            fig2.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Scenario Simulator
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Scenario simulator")
        st.caption("Try quick what-ifs without changing the form above (extra work hours, rent change, extra income).")
        st.write("")

        s1, s2, s3 = st.columns(3)
        with s1:
            extra_hours = st.slider("Extra work hours per week", 0.0, 10.0, 0.0, 1.0)
        with s2:
            rent_change = st.slider("Rent change ($/month)", -500.0, 500.0, 0.0, 25.0)
        with s3:
            extra_income = st.slider("Extra monthly income ($)", 0.0, 1000.0, 0.0, 50.0)

        base_weekly_job_income = float(st.session_state["weekly_job_income"])
        base_wage = float(st.session_state["wage"])
        base_weeks_per_month = float(st.session_state["weeks_per_month"])
        base_stipend = float(st.session_state["stipend"])

        scenario_weekly_job_income = base_weekly_job_income + (base_wage * extra_hours)
        scenario_monthly_job_income = scenario_weekly_job_income * base_weeks_per_month

        scenario_rent = max(rent + rent_change, 0.0)
        scenario_total_expenses = scenario_rent + utilities + food + transport + phone_internet + misc_basic
        scenario_total_income = scenario_monthly_job_income + base_stipend + extra_income
        scenario_balance = scenario_total_income - scenario_total_expenses
        delta_balance = scenario_balance - balance

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Scenario income / month",
            money(scenario_total_income),
            delta=money(scenario_total_income - total_income),
        )
        c2.metric(
            "Scenario expenses / month",
            money(scenario_total_expenses),
            delta=money(scenario_total_expenses - total_expenses),
        )
        c3.metric("Scenario balance / month", money(scenario_balance), delta=money(delta_balance))

        st.write("")
        if delta_balance > 0:
            st.success("This scenario improves your monthly balance.")
        elif delta_balance < 0:
            st.warning("This scenario reduces your monthly balance.")
        else:
            st.info("This scenario keeps your balance the same.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Save calculation for My Plan
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Save this calculation for My Plan")
        st.caption("Give this calculation a name and save it so you can use it later in the My Plan tab.")
        st.write("")

        default_label = f"{calc_city} • {money(balance)}/month"
        label = st.text_input("Name for this calculation", value=default_label, key="save_calc_label")
        save_clicked = st.button("💾 Save calculation")

        if save_clicked:
            calc_id = make_saved_calc_id()
            saved_entry = {
                "id": calc_id,
                "label": label,
                "city": calc_city,
                "run_date": str(date.today()),
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "balance": float(balance),
                "monthly_job_income": float(monthly_job_income),
                "stipend": float(stipend),
                "rent": float(rent),
                "utilities": float(utilities),
                "food": float(food),
                "transport": float(transport),
                "phone_internet": float(phone_internet),
                "misc_basic": float(misc_basic),
            }
            st.session_state["saved_calcs"].append(saved_entry)
            st.session_state["active_saved_calc_id"] = calc_id
            st.success("Calculation saved. You can use it in My Plan.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Download (safe, uses session_state values)
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Download")
        st.caption("Export your current calculation as a CSV file for your own records.")
        st.write("")

        result_row = {
            "city": calc_city,
            "min_wage": wage,
            "weeks_per_month": float(st.session_state["weeks_per_month"]),
            "monthly_job_income_est": float(st.session_state["monthly_job_income"]),  # NameError fix
            "stipend": float(st.session_state["stipend"]),
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
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# PAGE B: CITY COMPARE
# =========================================================
elif page == "City Compare":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("City comparison (CSV)")
    st.markdown(
        "<div class='small-note'>Compare cities based on a CSV file with monthly costs and incomes.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    data = safe_read_csv("data/student_costs.csv")
    if data is None:
        st.error("Could not read data/student_costs.csv. Make sure the file exists.")
        st.stop()

    required_cols = {
        "city",
        "month",
        "campus_job_income",
        "stipend_income",
        "rent",
        "utilities",
        "food",
        "transport",
        "phone_internet",
        "misc_basic",
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

    st.write("")
    # Smart empty state
    if len(compare_cities) < 2:
        st.info("Select at least two cities to compare trends and expense mix.")
        st.stop()

    start_dt = pd.to_datetime(start_month, format="%Y-%m", errors="coerce")
    end_dt = pd.to_datetime(end_month, format="%Y-%m", errors="coerce")
    if pd.isna(start_dt) or pd.isna(end_dt) or start_dt > end_dt:
        st.error("Invalid month range. Check Start and End month.")
        st.stop()

    filt = data[
        (data["city"].isin(compare_cities))
        & (data["month_dt"] >= start_dt)
        & (data["month_dt"] <= end_dt)
    ].copy()
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
    st.markdown("#### KPI tiles (average per month)")
    st.write("")
    cols = st.columns(min(4, len(summary)))
    for i, row in summary.iterrows():
        col = cols[i % len(cols)]
        with col:
            st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-label'>{row['city']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-value'>{money(row['avg_balance'])}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='kpi-sub'>Avg income {money(row['avg_income'])} • "
                f"Avg expenses {money(row['avg_expenses'])}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='kpi-sub'>Months: {int(row['months'])} • "
                f"Savings rate: {row['savings_rate']*100:.1f}%</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.6, 1.0])
    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Balance trend (by city)")
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
        st.markdown("#### Expense mix (selected range)")
        st.write("")
        exp_mix = filt.groupby("city", as_index=False)[expense_columns].sum()
        donut_city = st.selectbox("Donut city", compare_cities, index=0)
        row = exp_mix[exp_mix["city"] == donut_city]

        if not row.empty:
            donut_df = pd.DataFrame(
                {"Expense": expense_columns, "Amount": [float(row[col].iloc[0]) for col in expense_columns]}
            )
            fig2 = px.pie(donut_df, names="Expense", values="Amount", hole=0.55)
            fig2.update_layout(title=f"{donut_city}: total expenses by category")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No expense data for donut chart.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Compare table")
    st.write("")
    show = summary.sort_values("avg_balance", ascending=False).copy()
    show["Avg income"] = show["avg_income"].round(0)
    show["Avg expenses"] = show["avg_expenses"].round(0)
    show["Avg balance"] = show["avg_balance"].round(0)
    show["Savings rate (%)"] = (show["savings_rate"] * 100).round(1)
    show = show[
        ["city", "Avg income", "Avg expenses", "Avg balance", "months", "Savings rate (%)"]
    ].rename(columns={"city": "City", "months": "Months"})
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# PAGE C: MY PLAN
# =========================================================
elif page == "My Plan":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("My plan")
    st.markdown(
        "<div class='small-note'>Pick one of your saved calculations and turn it into a savings plan.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    saved = st.session_state.get("saved_calcs", [])

    if not saved:
        if not st.session_state.get("calc_ready", False):
            st.info("Run the Calculator and save at least one calculation to unlock My Plan.")
            st.stop()
        else:
            st.info("You have not saved any calculations yet. Go back to Calculator and click Save.")
            st.stop()

    # Build options for selectbox
    options = []
    id_to_entry = {}
    for entry in saved:
        label = entry.get("label", "Unnamed")
        city = entry.get("city", "-")
        bal = entry.get("balance", 0.0)
        run_date = entry.get("run_date", "")
        display = f"{label}  |  {city} • {money(bal)}/month • {run_date}"
        options.append(display)
        id_to_entry[display] = entry

    # Determine default selection
    default_index = 0
    active_id = st.session_state.get("active_saved_calc_id")
    if active_id is not None:
        for i, entry in enumerate(saved):
            if entry.get("id") == active_id:
                default_index = i
                break

    selection = st.selectbox("Saved calculation", options, index=default_index)
    chosen = id_to_entry[selection]
    st.session_state["active_saved_calc_id"] = chosen["id"]

    # Pull numbers from chosen saved calc
    monthly_balance = float(chosen["balance"])
    total_income = float(chosen["total_income"])
    goal_amount = float(st.session_state["goal_amount"])
    deadline = st.session_state["goal_deadline"]
    current_saved = float(st.session_state.get("current_saved", 0.0))
    today = date.today()

    # Goal summary
    days_left = max((deadline - today).days, 1)
    weeks_left = days_left / 7.0
    weekly_target = (goal_amount - current_saved) / weeks_left if weeks_left > 0 else goal_amount

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Goal summary")
    st.write("")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Goal", money(goal_amount))
    g2.metric("Saved so far", money(current_saved))
    g3.metric("Weeks left", f"{weeks_left:.1f}")
    g4.metric("Target per week", money(weekly_target))
    st.markdown("</div>", unsafe_allow_html=True)

    # Progress tracking
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Progress tracking")
    st.write("")
    remaining = max(goal_amount - current_saved, 0.0)
    pct = 0.0 if goal_amount <= 0 else clamp(current_saved / goal_amount, 0, 1)
    st.progress(int(pct * 100))
    p1, p2, p3 = st.columns(3)
    p1.metric("Progress", f"{pct*100:.1f}%")
    p2.metric("Remaining", money(remaining))
    p3.metric("Time left (days)", f"{days_left}")
    st.markdown("</div>", unsafe_allow_html=True)

    # On-track check
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Am I on track?")
    st.write("")
    weekly_from_balance = monthly_balance / 4.33 if monthly_balance else 0.0
    delta = weekly_from_balance - weekly_target

    if monthly_balance <= 0:
        st.error("Your chosen calculation is not saving anything. Improve your Calculator result first.")
    elif delta >= 0:
        st.success(
            f"On track. Estimated weekly saving is {money(weekly_from_balance)} and your target is {money(weekly_target)}."
        )
    else:
        st.warning(
            f"Short by about {money(abs(delta))} per week. Try cutting expenses or adding a few work hours."
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Actionable cut suggestions (based on chosen calc)
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Actionable cut suggestions (ranked)")
    st.write("")

    exp_all = {
        "Rent": float(chosen.get("rent", 0.0)),
        "Utilities": float(chosen.get("utilities", 0.0)),
        "Food": float(chosen.get("food", 0.0)),
        "Transport": float(chosen.get("transport", 0.0)),
        "Phone/Internet": float(chosen.get("phone_internet", 0.0)),
        "Misc basics": float(chosen.get("misc_basic", 0.0)),
    }

    rows = []
    for k, v in exp_all.items():
        share = (float(v) / total_income) if total_income > 0 else 0.0
        rows.append({"Expense": k, "Amount": float(v), "ShareOfIncome": share})
    exp_rank = (
        pd.DataFrame(rows)
        .sort_values("ShareOfIncome", ascending=False, ignore_index=True)
        .head(2)
    )

    if exp_rank.empty:
        st.info("No expenses found to rank.")
    else:
        for _, r in exp_rank.iterrows():
            cut_amount = 0.10 * float(r["Amount"])
            new_balance = monthly_balance + cut_amount
            st.markdown(
                f"- Cut **{money(cut_amount)}** from **{r['Expense']}**. "
                f"This moves balance from **{money(monthly_balance)}** to **{money(new_balance)}**."
            )
        st.write("")
    st.markdown("</div>", unsafe_allow_html=True)

    # Small table of all saved calcs for quick view
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### All saved calculations")
    st.write("")
    saved_df = pd.DataFrame(saved)
    if not saved_df.empty:
        show_cols = ["label", "city", "run_date", "total_income", "total_expenses", "balance"]
        for c in show_cols:
            if c not in saved_df.columns:
                saved_df[c] = None
        saved_df = saved_df[show_cols]
        saved_df.rename(
            columns={
                "label": "Label",
                "city": "City",
                "run_date": "Run date",
                "total_income": "Total income",
                "total_expenses": "Total expenses",
                "balance": "Balance",
            },
            inplace=True,
        )
        st.dataframe(saved_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No saved calculations to display.")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# PAGE D: SETTINGS
# =========================================================
elif page == "Settings":
    st.subheader("Settings")
    st.write("")
    st.info("Preferences and configuration coming soon.")
