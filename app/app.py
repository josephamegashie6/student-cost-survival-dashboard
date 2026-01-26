# =========================================================
# app.py  (PART 1: Calculator only, clean + stable)
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

         "scenarios": [],
        "active_scenario_id": None,

        # goal basics (we will use later in My Plan)
        "goal_amount": 1000.0,
        "goal_deadline": date.today() + timedelta(days=90),
        "current_saved": 0.0,

        # health metrics
        "health_score": 0,
        "rent_ratio": None,
        "savings_rate": None,
        "buffer_months": 0.0,

        # onboarding and flags
        "first_run": True,
        "calc_ready": False,

        # history
        "calc_history": [],

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

# rough presets (you can tune these)
CITY_EXPENSE_PRESETS = {
    "Saint Louis": {"rent": 850, "utilities": 130, "food": 350, "transport": 90, "phone_internet": 60},
    "Chicago": {"rent": 1300, "utilities": 160, "food": 420, "transport": 120, "phone_internet": 70},
    "New York City": {"rent": 1700, "utilities": 180, "food": 500, "transport": 140, "phone_internet": 80},
    "Los Angeles": {"rent": 1600, "utilities": 170, "food": 450, "transport": 130, "phone_internet": 70},
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


def pressure_flag(share: float):
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
        return pd.DataFrame(columns=["Expense", "Amount", "ShareOfIncome", "FlagLabel", "FlagCss"])

    return df.sort_values("ShareOfIncome", ascending=False, ignore_index=True)


def risk_badge_html(label: str, level: str) -> str:
    css_map = {
        "good": "pill pill-green",
        "warn": "pill pill-yellow",
        "bad": "pill pill-red",
    }
    css = css_map.get(level, "pill")
    return f"<span class='{css}'>{label}</span>"

def make_scenario_id() -> str:
    """Simple id for saved scenarios."""
    return "scn_" + datetime.now().strftime("%Y%m%d%H%M%S%f")


# =========================================================
# 6) SIDEBAR: NAV + SNAPSHOT
# =========================================================
with st.sidebar:
    st.markdown("### Student Cost Survival")
    st.write("")

    # For now only Calculator; we will add other pages later
    page = option_menu(
        menu_title=None,
        options=["Calculator"],
        icons=["calculator"],
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
    st.markdown("#### My snapshot")
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


# =========================================================
# 7) TOP TITLE
# =========================================================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.title("International Student Cost Survival Dashboard")
st.markdown(
    "<div class='small-note'>Use the calculator to understand your monthly budget and risk zones.</div>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.get("first_run", True):
    st.info("Step 1: Fill city, job and expenses. Step 2: Click Calculate to see your budget and insights.")
    st.session_state["first_run"] = False


# =========================================================
# PAGE A: CALCULATOR
# =========================================================
if page == "Calculator":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Personal calculator")
    st.markdown(
        "<div class='small-note'>Start with your study city and job hours. We use city minimum wage for estimates.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ------------- INPUT FORM -------------
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
            weeks_per_month = st.number_input(
                "Weeks per month",
                min_value=3.0,
                max_value=5.0,
                value=4.33,
                step=0.01,
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
            sunday_multiplier = st.number_input("Sunday pay multiplier", min_value=1.0, value=1.0, step=0.25)

        st.write("")
        st.markdown("### Other monthly income")
        stipend = st.number_input("Monthly stipend / support ($)", min_value=0.0, value=0.0, step=50.0)

        st.write("")
        st.markdown("### Monthly expenses")

        pcol, _ = st.columns([1.5, 1])
        with pcol:
            use_preset = st.checkbox("Use city presets for basic expenses")

        e1, e2, e3 = st.columns(3)
        with e1:
            rent_default = CITY_EXPENSE_PRESETS.get(calc_city, {}).get("rent", 850) if use_preset else 850
            utilities_default = CITY_EXPENSE_PRESETS.get(calc_city, {}).get("utilities", 120) if use_preset else 120
            rent = st.number_input("Rent ($)", min_value=0.0, value=float(rent_default), step=25.0)
            utilities = st.number_input("Utilities ($)", min_value=0.0, value=float(utilities_default), step=10.0)
        with e2:
            food_default = CITY_EXPENSE_PRESETS.get(calc_city, {}).get("food", 350) if use_preset else 350
            transport_default = CITY_EXPENSE_PRESETS.get(calc_city, {}).get("transport", 90) if use_preset else 90
            food = st.number_input("Food ($)", min_value=0.0, value=float(food_default), step=10.0)
            transport = st.number_input("Transport ($)", min_value=0.0, value=float(transport_default), step=10.0)
        with e3:
            phone_default = CITY_EXPENSE_PRESETS.get(calc_city, {}).get("phone_internet", 60) if use_preset else 60
            phone_internet = st.number_input("Phone/Internet ($)", min_value=0.0, value=float(phone_default), step=10.0)
            misc_basic = st.number_input("Misc basics ($)", min_value=0.0, value=130.0, step=10.0)

        st.write("")
        submitted = st.form_submit_button("✅ Calculate")

    # ------------- CALCULATION -------------
    if not submitted and not st.session_state.get("calc_ready", False):
        st.info("Fill the form above and click Calculate to see your budget, risk zones, charts and suggestions.")
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

        # Persist in session_state
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

        st.session_state["calc_history"].append(
            {
                "run_date": str(date.today()),
                "city": calc_city,
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "balance": float(balance),
            }
        )
        st.session_state["calc_history"] = st.session_state["calc_history"][-12:]

    # ------------- OUTPUT -------------
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

        # --- Financial health + risk zones ---
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Financial health and risk zones")
        st.write("")

        score = int(st.session_state.get("health_score", 0))
        rent_ratio = st.session_state.get("rent_ratio") or 0.0
        savings_rate = st.session_state.get("savings_rate") or 0.0
        buffer_months = float(st.session_state.get("buffer_months", 0))

        st.progress(int(clamp(score, 0, 100)))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score", f"{score}/100")
        c2.metric("Rent / income", f"{rent_ratio*100:.1f}%")
        c3.metric("Savings rate", f"{savings_rate*100:.1f}%")
        c4.metric("Buffer (months)", f"{buffer_months:.1f}")

        st.write("")
        rb1, rb2, rb3 = st.columns(3)

        if rent_ratio <= 0.30:
            rent_badge = risk_badge_html("Rent is light", "good")
        elif rent_ratio <= 0.40:
            rent_badge = risk_badge_html("Rent is heavy", "warn")
        else:
            rent_badge = risk_badge_html("Rent is very high", "bad")

        if buffer_months >= 2:
            buf_badge = risk_badge_html("Buffer is ok", "good")
        elif buffer_months >= 1:
            buf_badge = risk_badge_html("Thin buffer", "warn")
        else:
            buf_badge = risk_badge_html("No buffer", "bad")

        if savings_rate >= 0.10:
            sav_badge = risk_badge_html("Strong savings", "good")
        elif savings_rate >= 0.05:
            sav_badge = risk_badge_html("Low savings", "warn")
        else:
            sav_badge = risk_badge_html("No savings", "bad")

        with rb1:
            st.markdown(f"Rent pressure: {rent_badge}", unsafe_allow_html=True)
        with rb2:
            st.markdown(f"Emergency cushion: {buf_badge}", unsafe_allow_html=True)
        with rb3:
            st.markdown(f"Savings habit: {sav_badge}", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # --- Analytics insights ---
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Analytics insights")
        st.write("")

        expense_dict = {"Rent": rent, "Food": food, "Transport": transport}
        exp_df = build_expense_pressure_df(total_income, expense_dict)

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

        st.markdown("#### Trend insights")
        st.write("")
        hist = pd.DataFrame(st.session_state.get("calc_history", []))
        if not hist.empty:
            hist["balance"] = pd.to_numeric(hist["balance"], errors="coerce")
            last3 = hist["balance"].tail(3)
            rolling3 = float(last3.mean()) if len(last3) > 0 else float(balance)
            st.caption(f"3-run rolling average balance: {money(rolling3)}")

        projected_6m = float(balance) * 6
        st.caption(f"Simple projection: In 6 months your net change is about {money(projected_6m)}")

        st.write("")
        st.markdown("<hr class='soft'>", unsafe_allow_html=True)

        st.markdown("#### Extra risk flags")
        st.write("")
        flags = []

        if total_income > 0 and (rent / total_income) > 0.40:
            flags.append("Rent shock risk (rent is more than 40 percent of income).")
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

        # --- Charts ---
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

        # --- Scenario simulator ---
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Scenario simulator")
        st.caption("Try quick what-ifs without changing the form above.")
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

        # --- Actionable cut suggestions ---
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Actionable cut suggestions (ranked)")
        st.write("")

        exp_all = {
            "Rent": rent,
            "Utilities": utilities,
            "Food": food,
            "Transport": transport,
            "Phone/Internet": phone_internet,
            "Misc basics": misc_basic,
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
            st.markdown("<ul>", unsafe_allow_html=True)
            for _, r in exp_rank.iterrows():
                cut_amount = 0.10 * float(r["Amount"])
                new_balance = balance + cut_amount
                st.markdown(
                    f"""
                    <li>
                        Cut <strong>{money(cut_amount)}</strong> from <strong>{r['Expense']}</strong>.
                        <br>
                        <span style="opacity:0.8;">
                            This moves your monthly balance from
                            <strong>{money(balance)}</strong>
                            to
                            <strong>{money(new_balance)}</strong>.
                        </span>
                    </li>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</ul>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # --- Download CSV ---
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Download")
        st.caption("Export your current calculation as a CSV file for your own records.")
        st.write("")

        result_row = {
            "city": calc_city,
            "min_wage": wage,
            "weeks_per_month": float(st.session_state["weeks_per_month"]),
            "monthly_job_income_est": float(st.session_state["monthly_job_income"]),
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


    elif page == "Scenarios":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Scenario builder")
        st.markdown(
            "<div class='small-note'>Create full journeys like 'WashU 2025' with phases such as pre arrival, semesters, internship and grace period.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Short alias
        scenarios = st.session_state.get("scenarios", [])

    # ----------------------------------------------
    # Create or select scenario
    # ----------------------------------------------
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("#### Create or select a scenario")
        st.write("")

        left, right = st.columns(2)

    with left:
        if scenarios:
            labels = []
            label_to_id = {}
            for sc in scenarios:
                label = f"{sc['name']} | {sc['city']}"
                labels.append(label)
                label_to_id[label] = sc["id"]
            chosen_label = st.selectbox("Existing scenarios", labels)
            st.session_state["active_scenario_id"] = label_to_id[chosen_label]
        else:
            st.info("No scenarios yet. Add your first one on the right.")

    with right:
        with st.form("new_scenario"):
            name = st.text_input("Scenario name", placeholder="WashU MSBA 2025")
            city = st.text_input("City", placeholder="Saint Louis")
            visa = st.text_input("Visa type", placeholder="F1")
            start = st.date_input("Program start")
            end = st.date_input("Program end")
            add = st.form_submit_button("Add scenario")

        if add and name:
            new_sc = {
                "id": make_scenario_id(),
                "name": name,
                "city": city,
                "visa": visa,
                "program_start": str(start),
                "program_end": str(end),
                "phases": [],
            }
            st.session_state["scenarios"].append(new_sc)
            st.session_state["active_scenario_id"] = new_sc["id"]
            st.success("Scenario created.")

        st.markdown("</div>", unsafe_allow_html=True)

    # Pick active scenario object
    active = None
    for sc in st.session_state.get("scenarios", []):
        if sc["id"] == st.session_state.get("active_scenario_id"):
            active = sc
            break

    # ----------------------------------------------
    # Add timeline phase
    # ----------------------------------------------
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Add timeline phase")
    st.write("")

    if active is None:
        st.info("Select or create a scenario above, then add phases like pre arrival, semester 1, internship.")
    else:
        with st.form("add_phase"):
            pname = st.text_input("Phase name", placeholder="Pre arrival")
            months = st.number_input("Months in this phase", min_value=1, max_value=48, value=4)
            income = st.number_input("Average monthly income ($)", min_value=0.0, step=50.0)
            expenses = st.number_input("Average monthly expenses ($)", min_value=0.0, step=50.0)
            oneoff = st.number_input("One time costs in this phase ($)", min_value=0.0, step=50.0)
            addp = st.form_submit_button("Add phase")

        if addp and pname:
            active["phases"].append(
                {
                    "name": pname,
                    "months": int(months),
                    "monthly_income": float(income),
                    "monthly_expenses": float(expenses),
                    "one_time_costs": float(oneoff),
                }
            )
            st.success(f"Phase '{pname}' added.")

        if active["phases"]:
            df = pd.DataFrame(active["phases"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("No phases yet for this scenario. Add at least one to build the journey.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------
    # Balance timeline and insights
    # ----------------------------------------------
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Balance timeline and insights")
    st.write("")

    if active is None or not active.get("phases"):
        st.info("Once you add phases, we will show how your cash moves from start to graduation.")
    else:
        starting_cash = st.number_input(
            "Starting cash before first phase ($)",
            min_value=-50000.0,
            max_value=500000.0,
            value=0.0,
            step=500.0,
            help="Amount you expect to have saved before pre arrival, including family support.",
            key=f"start_cash_{active['id']}",
        )

        rows = []
        current_balance = float(starting_cash)

        for idx, ph in enumerate(active["phases"], start=1):
            months = int(ph["months"])
            mi = float(ph["monthly_income"])
            me = float(ph["monthly_expenses"])
            oneoff = float(ph["one_time_costs"])

            net_per_month = mi - me
            recurring_impact = net_per_month * months
            total_impact = recurring_impact - oneoff
            end_balance = current_balance + total_impact

            rows.append(
                {
                    "Order": idx,
                    "Phase": ph["name"],
                    "Months": months,
                    "Net per month": net_per_month,
                    "Total impact": total_impact,
                    "End balance": end_balance,
                }
            )

            current_balance = end_balance

        tl_df = pd.DataFrame(rows)

        c1, c2 = st.columns([1.3, 1.7])

        with c1:
            st.markdown("**Phase summary**")
            st.dataframe(tl_df, use_container_width=True, hide_index=True)

        with c2:
            st.markdown("**Balance over phases**")
            fig = px.line(
                tl_df,
                x="Order",
                y="End balance",
                markers=True,
                text="Phase",
                title="Projected cash balance at the end of each phase",
            )
            fig.update_traces(textposition="top center")
            fig.update_layout(
                xaxis_title="Phase (order)",
                yaxis_title="Balance (USD)",
            )
            st.plotly_chart(fig, use_container_width=True)

        min_bal = float(tl_df["End balance"].min())
        max_bal = float(tl_df["End balance"].max())
        last_bal = float(tl_df["End balance"].iloc[-1])
        worst_row = tl_df.loc[tl_df["End balance"].idxmin()]

        st.markdown("")
        st.markdown("**Quick reading of this scenario**")
        st.write(f"- Lowest balance across phases: **{money(min_bal)}** in phase **{worst_row['Phase']}**.")
        st.write(f"- Highest balance across phases: **{money(max_bal)}**.")
        st.write(f"- Balance at end of last phase: **{money(last_bal)}**.")

        if min_bal < 0:
            st.warning(
                "You drop below zero in at least one phase. You would need extra savings, backup funding or more income to avoid running out of cash."
            )
        else:
            st.success("You never go below zero in this journey. Your planned cash buffer looks feasible.")

        if last_bal < 0:
            st.info("Final balance is negative. Think about extra work, lower rent or smaller one time costs near the end.")
        elif last_bal < 1000:
            st.info("You finish the journey with a thin buffer. If possible, target at least one or two months of expenses as cash at graduation.")

        st.markdown("</div>", unsafe_allow_html=True)
