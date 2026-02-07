import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from datetime import date, timedelta, datetime
import math



#2) SESSION DEFAULTS
def init_defaults():
    defaults = {
        # snapshot
        "status": "Unknown",
        "balance": 0.0,
        "context_city": "-",

        # nav settings
        "compare_metric": "Balance",
        "month_preset": "All data",

        # onboarding
        "first_run": True,
        "calc_ready": False,

        # calculator history
        "calc_history": [],

        # saved calculations (for My Plan)
        "saved_calcs": [],
        "active_saved_calc_id": None,

        # scenario model (timeline)
        "scenarios": [],
        "active_scenario_id": None,

        # calculator persisted values
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

        # My Plan goal
        "goal_amount": 1000.0,
        "goal_deadline": date.today() + timedelta(days=90),
        "current_saved": 0.0,

        # program details stored from Calculator (for saving calc)
        "program_name": "",
        "program_type": "Current offer",
        "program_start": date.today(),
        "program_end": date.today() + timedelta(days=365),
        "program_tuition_total": 0.0,
        "program_loan_amount": 0.0,

        # health metrics stored from Calculator
        "health_score": 0,
        "rent_ratio": None,
        "savings_rate": None,
        "buffer_months": 0.0,

        # debt planner inputs 
        "debt_tuition_total": 0.0,
        "debt_living_total": 0.0,
        "debt_scholarships_total": 0.0,
        "debt_loan_principal": 0.0,
        "debt_loan_interest_rate": 6.0,         
        "debt_expected_start_salary": 60000.0, 
        "debt_salary_to_debt_rate_1": 0.05,
        "debt_salary_to_debt_rate_2": 0.10,
        "debt_salary_to_debt_rate_3": 0.20,

         # onboarding
        "onboarding_step": 1,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_defaults()

#3) PAGE CONFIG
st.set_page_config(page_title="Student Cost Survival Dashboard", layout="wide")

#4) STYLING (CSS)
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
    margin-bottom: 0.9rem;
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
    font-size: 0.92rem;
    margin-top: 0.35rem;
    line-height: 1.55;
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
    font-size: 0.82rem;
    opacity: 0.7;
    margin-top: 0.25rem;
    line-height: 1.35;
}
.pill {
    display: inline-block;
    padding: 0.18rem 0.60rem;
    border-radius: 999px;
    border: 1px solid #334155;
    font-size: 0.80rem;
    opacity: 0.95;
    margin-left: 0.40rem;
}
.pill-green {background: rgba(34,197,94,0.12); border-color: rgba(34,197,94,0.35);}
.pill-yellow {background: rgba(234,179,8,0.12); border-color: rgba(234,179,8,0.35);}
.pill-red {background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.35);}

hr.soft {
    border: none;
    border-top: 1px solid #1f2937;
    margin: 0.90rem 0;
}

ul { margin-top: 0.25rem; margin-bottom: 0.45rem; }
li { margin-bottom: 0.45rem; line-height: 1.45; }

/* Mobile-first tweaks */
@media (max-width: 768px) {
    .block-container {
        padding-top: 1.5rem;
        padding-left: 0.7rem;
        padding-right: 0.7rem;
    }
    .card, .section-card {
        padding: 0.9rem 0.9rem;
        margin-bottom: 0.8rem;
    }
    .kpi-value {
        font-size: 1.3rem;
    }
    .kpi-sub, .small-note {
        font-size: 0.85rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


#5) CONSTANTS + HELPERS
CITY_MIN_WAGE = {
    "Saint Louis": 12.30,
    "Chicago": 15.80,
    "New York City": 16.00,
    "Los Angeles": 16.90,
}

CITY_EXPENSE_PRESETS = {
    "Saint Louis": {"rent": 850, "utilities": 130, "food": 350, "transport": 90, "phone_internet": 60, "misc_basic": 130},
    "Chicago": {"rent": 1300, "utilities": 160, "food": 420, "transport": 120, "phone_internet": 70, "misc_basic": 150},
    "New York City": {"rent": 1700, "utilities": 180, "food": 500, "transport": 140, "phone_internet": 80, "misc_basic": 170},
    "Los Angeles": {"rent": 1600, "utilities": 170, "food": 450, "transport": 130, "phone_internet": 70, "misc_basic": 160},
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

def score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Risky"
    return "Critical"

def financial_health_score(total_income: float, total_expenses: float, rent: float, balance: float) -> tuple[int, dict]:
    if total_income <= 0:
        return 0, {
            "balance_points": 0,
            "rent_points": 0,
            "savings_points": 0,
            "buffer_points": 0,
            "rent_ratio": None,
            "savings_rate": None,
            "buffer_months": 0.0,
        }

    rent_ratio = rent / total_income
    savings_rate = balance / total_income
    
    balance_points = 40 if balance > 0 else 0

    rent_points = 25 * (0.60 - rent_ratio) / (0.60 - 0.35)
    rent_points = int(round(clamp(rent_points, 0, 25)))

    savings_points = 20 * (savings_rate / 0.10)
    savings_points = int(round(clamp(savings_points, 0, 20)))

    buffer_months = (balance / total_expenses) if total_expenses > 0 else 0.0
    buffer_points = 15 * buffer_months
    buffer_points = int(round(clamp(buffer_points, 0, 15)))

    score = int(clamp(balance_points + rent_points + savings_points + buffer_points, 0, 100))

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
    
def pressure_flag(share: float) -> tuple[str, str]:
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
            {"Expense": name, "Amount": amt_f, "ShareOfIncome": share, "FlagLabel": label, "FlagCss": css}
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["Expense", "Amount", "ShareOfIncome", "FlagLabel", "FlagCss"])
    return df.sort_values("ShareOfIncome", ascending=False, ignore_index=True)

def make_saved_calc_id() -> str:
    return "calc_" + datetime.now().strftime("%Y%m%d%H%M%S%f")

def make_scenario_id() -> str:
    return "scn_" + datetime.now().strftime("%Y%m%d%H%M%S%f")

def risk_badge_html(label: str, level: str) -> str:
    css_map = {"good": "pill pill-green", "warn": "pill pill-yellow", "bad": "pill pill-red"}
    css = css_map.get(level, "pill")
    return f"<span class='{css}'>{label}</span>"

def get_active_scenario_index():
    active_id = st.session_state.get("active_scenario_id")
    scenarios = st.session_state.get("scenarios", [])
    for i, sc in enumerate(scenarios):
        if sc.get("id") == active_id:
            return i
    return None

def monthly_payment(principal: float, rate_monthly: float, years: float) -> float:
    n = int(years * 12)
    if principal <= 0 or n <= 0:
        return 0.0
    if rate_monthly <= 0:
        return principal / n
    return principal * rate_monthly / (1 - (1 + rate_monthly) ** (-n))

def years_to_pay(principal: float, rate_monthly: float, monthly_contrib: float) -> float:
    if principal <= 0 or monthly_contrib <= 0:
        return 0.0
    if rate_monthly <= 0:
        return principal / (monthly_contrib * 12.0)
    if monthly_contrib <= principal * rate_monthly:
        return float("inf")
    n_months = -math.log(1 - principal * rate_monthly / monthly_contrib) / math.log(1 + rate_monthly)
    return n_months / 12.0


#6) SIDEBAR: NAV + SNAPSHOT + CONTROLS
with st.sidebar:
    st.markdown("### Student Cost Survival")
    st.write("")

    page = option_menu(
        menu_title=None,
        options=["Onboarding", "Calculator", "Scenarios", "City Compare", "My Plan", "Settings"],
        icons=["play-circle", "calculator", "calendar3", "globe2", "wallet2", "gear"],
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

    hs = st.session_state.get("health_score")
    if hs is not None:
        st.write("Health score:", int(hs), f"({score_label(int(hs))})")

    rr = st.session_state.get("rent_ratio")
    sr = st.session_state.get("savings_rate")
    if rr is not None and sr is not None:
        st.caption(f"Rent/Income: {rr*100:.1f}%  •  Savings rate: {sr*100:.1f}%")

    st.write("")
    status_now = st.session_state["status"]
    if status_now == "Deficit":
        st.info("Tip: rent and misc are the fastest levers to adjust.")
    elif status_now == "Break-even":
        st.info("Tip: aim for a small buffer, even one month helps.")
    elif status_now == "Surplus":
        st.info("Good spot. protect your buffer and grow savings.")
    else:
        st.caption("Run Calculator to see a personalized snapshot.")

    if page == "City Compare":
        st.markdown("---")
        st.markdown("#### Compare settings")
        st.write("")
        st.selectbox("Compare by", ["Balance", "Rent pressure", "Food cost", "Transport cost"], key="compare_metric")
        st.radio("Month range", ["All data", "Last 3 months", "Last 6 months"], key="month_preset")

    if page == "My Plan":
        st.markdown("---")
        st.markdown("#### Savings goal")
        st.write("")
        st.number_input("Goal amount ($)", min_value=0.0, step=50.0, key="goal_amount")
        st.date_input("Goal deadline", key="goal_deadline")
        st.number_input("Already saved toward goal ($)", min_value=0.0, step=50.0, key="current_saved")
        st.caption("Use Calculator and Save at least one calculation.")

# 7) TOP TITLE
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.title("International Student Cost Survival Dashboard")
st.markdown(
    "<div class='small-note'>Calculator for personal numbers. Scenarios for your timeline. City Compare for CSV insights. My Plan uses a saved calculation.</div>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.get("first_run", True):
    st.info("Step 1: Run Calculator. Step 2: Save a calculation. Step 3: Use My Plan. Step 4: Use Scenarios to model phases.")
    st.session_state["first_run"] = False


# PAGE 0: ONBOARDING WIZARD
if page == "Onboarding":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Quick onboarding")
    st.markdown(
        "<div class='small-note'>Four short steps: school and timing, income, housing and bills, then a simple result + risks. You can always fine-tune later in Calculator.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    step = st.session_state.get("onboarding_step", 1)
    step = int(step)

    # progress / step header
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown(f"**Step {step} of 4**")
    st.write("")

    # STEP 1
    if step == 1:
        st.markdown("### Step 1: Where will you study and when do you arrive?")
        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            city = st.selectbox(
                "Study city",
                list(CITY_MIN_WAGE.keys()),
                index=list(CITY_MIN_WAGE.keys()).index(DEFAULT_CITY),
                key="ob_city",
            )
        with col2:
            arrival = st.date_input("Approx arrival date", key="ob_arrival_date")

        st.caption("This helps set your city presets and gives you a rough timeline.")

    # STEP 2
    if step == 2:
        st.markdown("### Step 2: Income sources")
        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            wage = st.number_input(
                "Campus / hourly wage ($/hour)",
                min_value=0.0,
                value=st.session_state.get("wage", CITY_MIN_WAGE.get(st.session_state.get('ob_city', DEFAULT_CITY), 15.0)),
                step=0.25,
                key="ob_wage",
            )
            weekly_hours = st.number_input(
                "Total weekly work hours",
                min_value=0.0,
                value=20.0,
                step=1.0,
                key="ob_weekly_hours",
            )
        with c2:
            weeks_per_month = st.number_input(
                "Weeks per month",
                min_value=3.0,
                max_value=5.0,
                value=4.33,
                step=0.01,
                key="ob_weeks_per_month",
            )
            stipend = st.number_input(
                "Monthly stipend / family support ($)",
                min_value=0.0,
                value=0.0,
                step=50.0,
                key="ob_stipend",
            )

        st.caption("This will estimate your monthly income automatically in the background.")

    # STEP 3
    if step == 3:
        st.markdown("### Step 3: Housing and bills")
        st.write("")

        city_for_preset = st.session_state.get("ob_city", DEFAULT_CITY)
        preset = CITY_EXPENSE_PRESETS.get(city_for_preset, CITY_EXPENSE_PRESETS.get(DEFAULT_CITY, {}))

        use_preset = st.checkbox(
            f"Use typical {city_for_preset} presets as a starting point",
            key="ob_use_preset",
        )

        def preset_or(name, fallback):
            if use_preset:
                return float(preset.get(name, fallback))
            return float(fallback)

        e1, e2, e3 = st.columns(3)
        with e1:
            st.number_input(
                "Rent ($)",
                min_value=0.0,
                value=preset_or("rent", 900.0),
                step=25.0,
                key="ob_rent",
            )
            st.number_input(
                "Utilities ($)",
                min_value=0.0,
                value=preset_or("utilities", 130.0),
                step=10.0,
                key="ob_utilities",
            )
        with e2:
            st.number_input(
                "Food ($)",
                min_value=0.0,
                value=preset_or("food", 350.0),
                step=10.0,
                key="ob_food",
            )
            st.number_input(
                "Transport ($)",
                min_value=0.0,
                value=preset_or("transport", 90.0),
                step=10.0,
                key="ob_transport",
            )
        with e3:
            st.number_input(
                "Phone/Internet ($)",
                min_value=0.0,
                value=preset_or("phone_internet", 60.0),
                step=10.0,
                key="ob_phone_internet",
            )
            st.number_input(
                "Misc basics ($)",
                min_value=0.0,
                value=preset_or("misc_basic", 130.0),
                step=10.0,
                key="ob_misc_basic",
            )

        st.caption("These are benchmarks for an off-campus student. Change them to match your actual numbers.")

    # STEP 4
    if step == 4:
        st.markdown("### Step 4: Result + risks")
        st.write("")

        # pull onboarding values
        city = st.session_state.get("ob_city", DEFAULT_CITY)
        wage = float(st.session_state.get("ob_wage", CITY_MIN_WAGE.get(city, 15.0)))
        weekly_hours = float(st.session_state.get("ob_weekly_hours", 20.0))
        weeks_per_month = float(st.session_state.get("ob_weeks_per_month", 4.33))
        stipend = float(st.session_state.get("ob_stipend", 0.0))

        rent = float(st.session_state.get("ob_rent", 900.0))
        utilities = float(st.session_state.get("ob_utilities", 130.0))
        food = float(st.session_state.get("ob_food", 350.0))
        transport = float(st.session_state.get("ob_transport", 90.0))
        phone_internet = float(st.session_state.get("ob_phone_internet", 60.0))
        misc_basic = float(st.session_state.get("ob_misc_basic", 130.0))

        monthly_job_income = wage * weekly_hours * weeks_per_month
        total_income = monthly_job_income + stipend
        total_expenses = rent + utilities + food + transport + phone_internet + misc_basic
        balance = total_income - total_expenses
        status = financial_status(balance)

        score, breakdown = financial_health_score(
            total_income=total_income,
            total_expenses=total_expenses,
            rent=rent,
            balance=balance,
        )

        rent_ratio = breakdown["rent_ratio"] or 0.0
        savings_rate = breakdown["savings_rate"] or 0.0
        buffer_months = float(breakdown.get("buffer_months", 0.0))

        # quick summary
        r1, r2, r3 = st.columns(3)
        r1.metric("Income / month", money(total_income))
        r2.metric("Expenses / month", money(total_expenses))
        r3.metric("Balance / month", money(balance))

        st.write("")
        if status == "Surplus":
            st.success("You are in surplus. You have some buffer after essentials.")
        elif status == "Break-even":
            st.warning("You are at break-even. You survive, but you have no buffer.")
        else:
            st.error("You are in deficit. You will need support, higher income, or lower expenses.")

        st.write("")
        st.markdown("##### Quick risk zones")

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Rent / income",
            f"{rent_ratio*100:.1f}%",
            help="How much of your income goes to rent. Above 40% is usually a red zone."
        )
        c2.metric(
            "Savings rate",
            f"{savings_rate*100:.1f}%",
            help="What's left after core expenses. Below ~5% is fragile."
        )
        c3.metric(
            "Buffer months",
            f"{buffer_months:.1f}",
            help="How long you can keep going if your income stops and you keep spending the same."
        )

        st.write("")
        flags = []
        if total_income > 0 and rent_ratio > 0.40:
            flags.append("Rent is above 40 percent of income (red zone).")
        if buffer_months <= 0:
            flags.append("Zero buffer (you have no savings cushion).")
        if savings_rate < 0.05:
            flags.append("Savings rate is under 5 percent (yellow zone).")

        if flags:
            for f in flags:
                st.warning(f)
        else:
            st.success("No major risk flags based on these numbers.")

        st.write("")
        st.caption("You can now open the Calculator page to fine-tune details and save this setup as a scenario.")

    # navigation buttons
    st.markdown("</div>", unsafe_allow_html=True)

    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 2])
    with nav_col1:
        if step > 1 and st.button("⬅️ Back"):
            st.session_state["onboarding_step"] = max(1, step - 1)
    with nav_col2:
        if step < 4 and st.button("Next ➡️"):
            st.session_state["onboarding_step"] = min(4, step + 1)
    with nav_col3:
        if step == 4 and st.button("Send to Calculator"):
            # push onboarding values into main calculator defaults
            st.session_state["context_city"] = st.session_state.get("ob_city", DEFAULT_CITY)
            st.session_state["wage"] = float(st.session_state.get("ob_wage", CITY_MIN_WAGE.get(st.session_state["context_city"], 15.0)))
            st.session_state["weeks_per_month"] = float(st.session_state.get("ob_weeks_per_month", 4.33))
            st.session_state["stipend"] = float(st.session_state.get("ob_stipend", 0.0))

            st.session_state["rent"] = float(st.session_state.get("ob_rent", 900.0))
            st.session_state["utilities"] = float(st.session_state.get("ob_utilities", 130.0))
            st.session_state["food"] = float(st.session_state.get("ob_food", 350.0))
            st.session_state["transport"] = float(st.session_state.get("ob_transport", 90.0))
            st.session_state["phone_internet"] = float(st.session_state.get("ob_phone_internet", 60.0))
            st.session_state["misc_basic"] = float(st.session_state.get("ob_misc_basic", 130.0))

            st.session_state["onboarding_step"] = 1
            st.success("Values sent. Open the Calculator page to see and refine them.")

#PAGE A: CALCULATOR
if page == "Calculator":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Personal Calculator")
    st.markdown(
        "<div class='small-note'>Fill the form and click Calculate. You can also save the result for My Plan.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("calculator_form"):
        top1, top2, top3 = st.columns([1.2, 1, 1])

        with top1:
            calc_city = st.selectbox("City", list(CITY_MIN_WAGE.keys()), index=list(CITY_MIN_WAGE.keys()).index(DEFAULT_CITY))

        with top2:
            min_wage = CITY_MIN_WAGE.get(calc_city, 15.0)
            wage = st.number_input("Minimum wage ($/hour)", min_value=0.0, value=float(min_wage), step=0.25)

        with top3:
            weeks_per_month = st.number_input("Weeks per month", min_value=3.0, max_value=5.0, value=4.33, step=0.01)

        st.write("")
        st.markdown("### Work hours (weekly)")
        h1, h2, h3, h4 = st.columns(4)
        with h1:
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

        pcol, _ = st.columns([1.5, 1])
        with pcol:
            use_preset = st.checkbox("Use city presets for basic expenses", value=False)

        preset = CITY_EXPENSE_PRESETS.get(calc_city, CITY_EXPENSE_PRESETS.get(DEFAULT_CITY, {}))

        e1, e2, e3 = st.columns(3)
        with e1:
            rent = st.number_input(
                "Rent ($)",
                min_value=0.0,
                value=float(preset.get("rent", 850)) if use_preset else 850.0,
                step=25.0,
            )
            utilities = st.number_input(
                "Utilities ($)",
                min_value=0.0,
                value=float(preset.get("utilities", 120)) if use_preset else 120.0,
                step=10.0,
            )
        with e2:
            food = st.number_input(
                "Food ($)",
                min_value=0.0,
                value=float(preset.get("food", 350)) if use_preset else 350.0,
                step=10.0,
            )
            transport = st.number_input(
                "Transport ($)",
                min_value=0.0,
                value=float(preset.get("transport", 90)) if use_preset else 90.0,
                step=10.0,
            )
        with e3:
            phone_internet = st.number_input(
                "Phone/Internet ($)",
                min_value=0.0,
                value=float(preset.get("phone_internet", 60)) if use_preset else 60.0,
                step=10.0,
            )
            misc_basic = st.number_input(
                "Misc basics ($)",
                min_value=0.0,
                value=float(preset.get("misc_basic", 130)) if use_preset else 130.0,
                step=10.0,
            )

        st.write("")
        st.markdown("### Program details (optional, helps naming and saving)")
        d1, d2 = st.columns(2)
        with d1:
            program_name = st.text_input("Program name", value=st.session_state.get("program_name", ""))
            program_type = st.selectbox(
                "Scenario type",
                ["Current offer", "Backup offer", "Dream option", "Current school"],
                index=["Current offer", "Backup offer", "Dream option", "Current school"].index(st.session_state.get("program_type", "Current offer")),
            )
            program_start = st.date_input("Program start date", value=st.session_state.get("program_start", date.today()))
        with d2:
            program_end = st.date_input("Expected graduation date", value=st.session_state.get("program_end", date.today() + timedelta(days=365)))
            program_tuition_total = st.number_input(
                "Total tuition and fees for full program ($)",
                min_value=0.0,
                value=float(st.session_state.get("program_tuition_total", 0.0)),
                step=1000.0,
            )
            program_loan_amount = st.number_input(
                "Planned total loan amount ($)",
                min_value=0.0,
                value=float(st.session_state.get("program_loan_amount", 0.0)),
                step=1000.0,
            )

        st.write("")
        submitted = st.form_submit_button("✅ Calculate")

    if not submitted and not st.session_state.get("calc_ready", False):
        st.info("Fill the form and click Calculate. Your results stay available across pages after the first run.")
    elif submitted:
        weekly_job_income = (wage * (hours_mon_fri + hours_sat)) + (wage * hours_sun * sunday_multiplier)
        monthly_job_income = weekly_job_income * weeks_per_month

        total_income = monthly_job_income + stipend
        total_expenses = rent + utilities + food + transport + phone_internet + misc_basic
        balance = total_income - total_expenses
        status = financial_status(balance)

        health_score, score_breakdown = financial_health_score(total_income=total_income, total_expenses=total_expenses, rent=rent, balance=balance)

        # persist core
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
        st.session_state["rent_ratio"] = float(score_breakdown["rent_ratio"]) if score_breakdown["rent_ratio"] is not None else None
        st.session_state["savings_rate"] = float(score_breakdown["savings_rate"]) if score_breakdown["savings_rate"] is not None else None
        st.session_state["buffer_months"] = float(score_breakdown.get("buffer_months", 0.0))

        st.session_state["rent"] = float(rent)
        st.session_state["utilities"] = float(utilities)
        st.session_state["food"] = float(food)
        st.session_state["transport"] = float(transport)
        st.session_state["phone_internet"] = float(phone_internet)
        st.session_state["misc_basic"] = float(misc_basic)

        # program details 
        st.session_state["program_name"] = program_name
        st.session_state["program_type"] = program_type
        st.session_state["program_start"] = program_start
        st.session_state["program_end"] = program_end
        st.session_state["program_tuition_total"] = float(program_tuition_total)
        st.session_state["program_loan_amount"] = float(program_loan_amount)

        st.session_state["calc_ready"] = True

        # history
        st.session_state["calc_history"].append(
            {"run_date": str(date.today()), "city": calc_city, "total_income": float(total_income), "total_expenses": float(total_expenses), "balance": float(balance)}
        )
        st.session_state["calc_history"] = st.session_state["calc_history"][-12:]

    # show results if ready
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

        program_name = st.session_state.get("program_name", "")
        program_type = st.session_state.get("program_type", "Current offer")
        program_start = st.session_state.get("program_start", date.today())
        program_end = st.session_state.get("program_end", date.today() + timedelta(days=365))
        program_tuition_total = float(st.session_state.get("program_tuition_total", 0.0))
        program_loan_amount = float(st.session_state.get("program_loan_amount", 0.0))

        # Results card
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

        # Financial health and risk zones
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Financial Health and risk zones")
        st.write("")

        score = int(st.session_state.get("health_score", 0))
        rent_ratio = float(st.session_state.get("rent_ratio") or 0.0)
        savings_rate = float(st.session_state.get("savings_rate") or 0.0)
        buffer_months = float(st.session_state.get("buffer_months", 0.0))

        st.progress(int(clamp(score, 0, 100)))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Score",
            f"{score}/100",
            help="Quick 0–100 view of how your month looks (income, expenses, savings, buffer)."
        )
        c2.metric(
            "Rent / income",
            f"{rent_ratio*100:.1f}%",
            help="How much of your monthly income goes to rent."
        )
        c3.metric(
            "Savings rate",
            f"{savings_rate*100:.1f}%",
            help="Part of your income left after core expenses. Think of it as your savings muscle."
        )
        c4.metric(
            "Buffer (months)",
            f"{buffer_months:.1f}",
            help="Buffer months is how long you can survive if income stops and you keep spending the same."
        )
        st.write("")
        rb1, rb2, rb3 = st.columns(3)

        # rent badge
        if rent_ratio <= 0.30:
            rent_badge = risk_badge_html("Rent is light", "good")
        elif rent_ratio <= 0.40:
            rent_badge = risk_badge_html("Rent is heavy", "warn")
        else:
            rent_badge = risk_badge_html("Rent is very high", "bad")

        # buffer badge
        if buffer_months >= 2:
            buf_badge = risk_badge_html("Buffer is ok", "good")
        elif buffer_months >= 1:
            buf_badge = risk_badge_html("Thin buffer", "warn")
        else:
            buf_badge = risk_badge_html("No buffer", "bad")

        # savings badge
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

        # Analytics insights
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
        st.caption(f"Simple projection: at this rate, in 6 months your net change is about {money(projected_6m)}")

        st.write("")
        st.markdown("<hr class='soft'>", unsafe_allow_html=True)

        st.markdown("#### Extra risk flags")
        st.write("")
        flags = []
        if total_income > 0 and (rent / total_income) > 0.40:
            flags.append("Rent shock risk (rent is above 40 percent of income).")
        if buffer_months <= 0:
            flags.append("Zero buffer risk (no savings cushion).")
        if balance < 0:
            flags.append("Cashflow deficit risk (spending more than income).")

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
            comparison_df = pd.DataFrame({"Category": ["Total income", "Total expenses"], "Amount": [total_income, total_expenses]})
            fig = px.bar(comparison_df, x="Category", y="Amount", text="Amount", title="Income vs essential expenses")
            fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_yaxes(range=[0, max(total_income, total_expenses) * 1.25])
            fig.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            exp_all_df = pd.DataFrame(
                {"Expense": ["Rent", "Utilities", "Food", "Transport", "Phone/Internet", "Misc basics"],
                 "Amount": [rent, utilities, food, transport, phone_internet, misc_basic]}
            )
            fig2 = px.bar(exp_all_df, x="Expense", y="Amount", text="Amount", title="Expense breakdown")
            fig2.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig2.update_yaxes(range=[0, max(exp_all_df["Amount"]) * 1.25])
            fig2.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Scenario simulator (quick what-ifs)
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
        c1.metric("Scenario income / month", money(scenario_total_income), delta=money(scenario_total_income - total_income))
        c2.metric("Scenario expenses / month", money(scenario_total_expenses), delta=money(scenario_total_expenses - total_expenses))
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
        st.caption("Save multiple options like WashU 2025, UT Dallas backup, etc.")
        st.write("")

        default_label = f"{program_name or calc_city}  •  {money(balance)}/month"
        label = st.text_input("Name for this saved calculation", value=default_label, key="save_calc_label")

        col_save, col_clear = st.columns([1, 1.2])
        with col_save:
            save_clicked = st.button("💾 Save calculation")
        with col_clear:
            st.caption("Tip: after saving, go to My Plan to compare, plan, and run debt payback.")

        if save_clicked:
            calc_id = make_saved_calc_id()
            saved_entry = {
                "id": calc_id,
                "label": label,
                "run_date": str(date.today()),
                "city": calc_city,

                "program_name": program_name,
                "program_type": program_type,
                "program_start": str(program_start),
                "program_end": str(program_end),
                "program_tuition_total": float(program_tuition_total),
                "program_loan_amount": float(program_loan_amount),

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

                "health_score": int(score),
                "rent_ratio": float(rent_ratio),
                "savings_rate": float(savings_rate),
                "buffer_months": float(buffer_months),
            }
            st.session_state["saved_calcs"].append(saved_entry)
            st.session_state["active_saved_calc_id"] = calc_id
            st.success("Saved. Open My Plan to use this calculation.")

        st.markdown("</div>", unsafe_allow_html=True)

        # Download current calc
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Download")
        st.caption("Export your current calculation as CSV.")
        st.write("")

        result_row = {
            "city": calc_city,
            "program_name": program_name,
            "program_type": program_type,
            "program_start": str(program_start),
            "program_end": str(program_end),
            "program_tuition_total": program_tuition_total,
            "program_loan_amount": program_loan_amount,
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


#PAGE B: SCENARIOS
elif page == "Scenarios":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Scenario builder")
    st.markdown(
        "<div class='small-note'>Store scenarios per user: User → Scenarios → Phases. Build a timeline for pre-arrival, semesters, internships, and grace period.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Create or select scenario
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Create or select a scenario")
    st.write("")

    scenarios = st.session_state.get("scenarios", [])
    left, right = st.columns(2)

    with left:
        if scenarios:
            labels = []
            label_to_id = {}
            for sc in scenarios:
                label = f"{sc.get('name','Unnamed')}  |  {sc.get('city','-')}  |  {sc.get('visa','-')}"
                labels.append(label)
                label_to_id[label] = sc["id"]
            chosen_label = st.selectbox("Existing scenarios", labels)
            st.session_state["active_scenario_id"] = label_to_id[chosen_label]
        else:
            st.info("No scenarios yet. Add your first one on the right.")

    with right:
        with st.form("new_scenario_form"):
            name = st.text_input("Scenario name", placeholder="WashU 2025")
            city = st.text_input("City", placeholder="Saint Louis")
            visa = st.text_input("Visa type", placeholder="F-1")
            start = st.date_input("Program start", value=date.today())
            end = st.date_input("Program end", value=date.today() + timedelta(days=365))
            add = st.form_submit_button("Add scenario")

        if add and name.strip():
            new_sc = {
                "id": make_scenario_id(),
                "name": name.strip(),
                "city": city.strip() if city else "-",
                "visa": visa.strip() if visa else "-",
                "program_start": str(start),
                "program_end": str(end),
                "phases": [],
            }
            st.session_state["scenarios"].append(new_sc)
            st.session_state["active_scenario_id"] = new_sc["id"]
            st.success("Scenario created.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Active scenario (always from session list)
    idx = get_active_scenario_index()
    active = st.session_state["scenarios"][idx] if idx is not None else None

    # Add phase
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Add timeline phase")
    st.write("")

    if active is None:
        st.info("Select or create a scenario above, then add phases.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        with st.form("add_phase_form"):
            pname = st.text_input("Phase name", placeholder="Pre-arrival")
            months = st.number_input("Months in this phase", min_value=1, max_value=48, value=4)
            income = st.number_input("Average monthly income ($)", min_value=0.0, step=50.0)
            expenses = st.number_input("Average monthly expenses ($)", min_value=0.0, step=50.0)
            oneoff = st.number_input("One-time costs in this phase ($)", min_value=0.0, step=50.0)
            addp = st.form_submit_button("Add phase")

        if addp and pname.strip():
            active["phases"].append(
                {
                    "name": pname.strip(),
                    "months": int(months),
                    "monthly_income": float(income),
                    "monthly_expenses": float(expenses),
                    "one_time_costs": float(oneoff),
                }
            )
            # write back
            st.session_state["scenarios"][idx] = active
            st.success(f"Phase '{pname.strip()}' added.")

        st.write("")
        if active.get("phases"):
            st.markdown("**Current phases**")
            df_ph = pd.DataFrame(active["phases"])
            st.dataframe(df_ph, use_container_width=True, hide_index=True)
        else:
            st.caption("No phases yet. Add pre-arrival first, then semesters, internship months, and grace period.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Timeline insights
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Balance timeline and insights")
    st.write("")

    if active is None or not active.get("phases"):
        st.info("Add at least one phase to see projected cash balance and warnings.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        starting_cash_key = f"scenario_start_cash__{active['id']}"
        if starting_cash_key not in st.session_state:
            st.session_state[starting_cash_key] = 0.0

        starting_cash = st.number_input(
            "Starting cash before first phase ($)",
            min_value=-50000.0,
            max_value=500000.0,
            value=float(st.session_state[starting_cash_key]),
            step=500.0,
            key=starting_cash_key,
        )

        rows = []
        current_balance = float(starting_cash)

        for order, ph in enumerate(active["phases"], start=1):
            months = int(ph.get("months", 0))
            mi = float(ph.get("monthly_income", 0.0))
            me = float(ph.get("monthly_expenses", 0.0))
            oneoff = float(ph.get("one_time_costs", 0.0))

            net_per_month = mi - me
            recurring_impact = net_per_month * months
            total_impact = recurring_impact - oneoff
            end_balance = current_balance + total_impact

            rows.append(
                {
                    "Order": order,
                    "Phase": ph.get("name", f"Phase {order}"),
                    "Months": months,
                    "Monthly net": net_per_month,
                    "One-time costs": oneoff,
                    "Phase impact": total_impact,
                    "End balance": end_balance,
                }
            )
            current_balance = end_balance

        tl_df = pd.DataFrame(rows)

        c1, c2 = st.columns([1.15, 1.85])
        with c1:
            st.markdown("**Phase summary**")
            st.dataframe(tl_df, use_container_width=True, hide_index=True)

        with c2:
            st.markdown("**Cash balance over phases**")
            fig = px.line(tl_df, x="Order", y="End balance", markers=True, title="Projected cash balance by phase end")
            fig.update_layout(xaxis_title="Phase order", yaxis_title="Balance (USD)")
            st.plotly_chart(fig, use_container_width=True)

        st.write("")
        min_bal = float(tl_df["End balance"].min())
        max_bal = float(tl_df["End balance"].max())
        final_bal = float(tl_df["End balance"].iloc[-1])
        worst_row = tl_df.loc[tl_df["End balance"].idxmin()]

        st.markdown("**Key insights**")
        st.write(f"- Lowest balance: **{money(min_bal)}** (worst phase: **{worst_row['Phase']}**) ")
        st.write(f"- Highest balance: **{money(max_bal)}** ")
        st.write(f"- Final balance after last phase: **{money(final_bal)}** ")

        if min_bal < 0:
            extra_needed = abs(min_bal)
            st.warning(f"You go below zero at some point. To never go negative, you need about **{money(extra_needed)}** more starting cash or funding.")
        else:
            st.success("You never go below zero in this scenario. Cash buffer looks feasible.")

        # Practical recommendation: where to fix first
        st.write("")
        st.markdown("**What to change first**")
        if float(worst_row["Monthly net"]) < 0:
            st.write("- Your worst phase has negative monthly net. First fix is to increase income or reduce expenses during that phase.")
        if float(worst_row["One-time costs"]) > 0:
            st.write("- Your worst phase includes one-time costs. Consider spreading those costs earlier, saving for them, or reducing them.")
        if min_bal < 0 and final_bal > 0:
            st.write("- You recover later. So the gap is a timing problem. Plan a buffer before the dip phase.")

        st.markdown("</div>", unsafe_allow_html=True)


# PAGE C: CITY COMPARE
elif page == "City Compare":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("City comparison (CSV)")
    st.markdown("<div class='small-note'>Compare cities using data/student_costs.csv (month must be YYYY-MM).</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    data = safe_read_csv("data/student_costs.csv")
    if data is None:
        st.error("Could not read data/student_costs.csv. Make sure the file exists.")
        st.stop()

    required_cols = {
        "city", "month", "campus_job_income", "stipend_income",
        "rent", "utilities", "food", "transport", "phone_internet", "misc_basic"
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
        compare_cities = st.multiselect("Cities to compare", cities, default=cities[:2] if len(cities) >= 2 else cities)
    with f2:
        start_month = st.selectbox("Start month", months_sorted, index=0)
    with f3:
        end_month = st.selectbox("End month", months_sorted, index=len(months_sorted) - 1)

    st.write("")
    if len(compare_cities) < 2:
        st.info("Select at least two cities to compare trends and expense mix.")
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
        .agg(avg_income=("total_income", "mean"), avg_expenses=("total_expenses", "mean"), avg_balance=("balance", "mean"), months=("month", "nunique"))
    )
    summary["savings_rate"] = summary.apply(lambda r: (r["avg_balance"] / r["avg_income"]) if r["avg_income"] else 0.0, axis=1)

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
            st.markdown(f"<div class='kpi-sub'>Avg income {money(row['avg_income'])} • Avg expenses {money(row['avg_expenses'])}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-sub'>Months: {int(row['months'])} • Savings rate: {row['savings_rate']*100:.1f}%</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.6, 1.0])
    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### Balance trend (by city)")
        st.write("")
        trend = filt.groupby(["month_dt", "city"], as_index=False).agg(balance=("balance", "mean")).sort_values(["month_dt", "city"])
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
            donut_df = pd.DataFrame({"Expense": expense_columns, "Amount": [float(row[col].iloc[0]) for col in expense_columns]})
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
    show = show[["city", "Avg income", "Avg expenses", "Avg balance", "months", "Savings rate (%)"]].rename(columns={"city": "City", "months": "Months"})
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# PAGE D: MY PLAN
elif page == "My Plan":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("My plan")
    st.markdown("<div class='small-note'>Pick one saved calculation and turn it into a goal plan plus a debt payback view.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    saved = st.session_state.get("saved_calcs", [])
    if not saved:
        st.info("No saved calculations yet. Go to Calculator and click Save calculation.")
        st.stop()

    # choose saved calc
    options = []
    display_to_entry = {}
    for entry in saved:
        label = entry.get("label", "Unnamed")
        city = entry.get("city", "-")
        bal = float(entry.get("balance", 0.0))
        run_date = entry.get("run_date", "")
        display = f"{label}  |  {city}  |  {money(bal)}/month  |  {run_date}"
        options.append(display)
        display_to_entry[display] = entry

    # default selection
    default_index = 0
    active_id = st.session_state.get("active_saved_calc_id")
    if active_id:
        for i, entry in enumerate(saved):
            if entry.get("id") == active_id:
                default_index = i
                break

    selection = st.selectbox("Saved calculation", options, index=default_index)
    chosen = display_to_entry[selection]
    st.session_state["active_saved_calc_id"] = chosen.get("id")

    st.write("")
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Selected calculation snapshot")
    st.write("")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("City", chosen.get("city", "-"))
    s2.metric("Income / month", money(float(chosen.get("total_income", 0.0))))
    s3.metric("Expenses / month", money(float(chosen.get("total_expenses", 0.0))))
    s4.metric("Balance / month", money(float(chosen.get("balance", 0.0))))
    st.markdown("</div>", unsafe_allow_html=True)

    # Goal plan
    goal_amount = float(st.session_state["goal_amount"])
    deadline = st.session_state["goal_deadline"]
    current_saved = float(st.session_state.get("current_saved", 0.0))
    monthly_balance = float(chosen.get("balance", 0.0))

    today = date.today()
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

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Am I on track?")
    st.write("")
    weekly_from_balance = monthly_balance / 4.33 if monthly_balance else 0.0
    delta = weekly_from_balance - weekly_target

    if monthly_balance <= 0:
        st.error("This saved calculation is not saving anything. Improve the Calculator result or save a better scenario.")
    elif delta >= 0:
        st.success(f"On track. Estimated weekly saving is {money(weekly_from_balance)} and your target is {money(weekly_target)}.")
    else:
        st.warning(f"Short by about {money(abs(delta))} per week. Reduce expenses or increase income.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Debt at graduation and payback (PERSISTENT inputs)
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Debt at graduation and payback time")
    st.caption("These inputs stay saved even when you switch pages.")
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        st.number_input("Total tuition and fees for program ($)", min_value=0.0, step=1000.0, key="debt_tuition_total")
        st.number_input("Total living costs during program ($)", min_value=0.0, step=1000.0, key="debt_living_total")
    with dcol2:
        st.number_input("Total scholarships or grants ($)", min_value=0.0, step=1000.0, key="debt_scholarships_total")
        st.number_input("Loan principal at graduation ($)", min_value=0.0, step=1000.0, key="debt_loan_principal")
    with dcol3:
        st.number_input("Loan interest rate (annual, %)", min_value=0.0, max_value=25.0, step=0.25, key="debt_loan_interest_rate")
        st.number_input("Expected starting salary (annual, $)", min_value=0.0, step=5000.0, key="debt_expected_start_salary")

    st.write("")
    rcol1, rcol2, rcol3 = st.columns(3)
    with rcol1:
        st.number_input("Payoff scenario 1: salary share (%)", min_value=0.0, max_value=60.0, step=1.0, key="debt_salary_to_debt_rate_1")
    with rcol2:
        st.number_input("Payoff scenario 2: salary share (%)", min_value=0.0, max_value=60.0, step=1.0, key="debt_salary_to_debt_rate_2")
    with rcol3:
        st.number_input("Payoff scenario 3: salary share (%)", min_value=0.0, max_value=60.0, step=1.0, key="debt_salary_to_debt_rate_3")

    tuition_total = float(st.session_state["debt_tuition_total"])
    living_total = float(st.session_state["debt_living_total"])
    scholarships_total = float(st.session_state["debt_scholarships_total"])
    loan_principal = float(st.session_state["debt_loan_principal"])
    loan_rate_annual = float(st.session_state["debt_loan_interest_rate"])
    salary_annual = float(st.session_state["debt_expected_start_salary"])

    total_program_cost = tuition_total + living_total
    net_cost_after_sch = max(total_program_cost - scholarships_total, 0.0)
    total_debt_at_grad = loan_principal if loan_principal > 0 else net_cost_after_sch

    monthly_salary = salary_annual / 12.0 if salary_annual > 0 else 0.0
    r = loan_rate_annual / 100.0 / 12.0 if loan_rate_annual > 0 else 0.0

    baseline_pmt = monthly_payment(total_debt_at_grad, r, 10)

    st.write("")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total debt at graduation (approx.)", money(total_debt_at_grad))
    m2.metric("Standard 10-year payment", money(baseline_pmt))
    m3.metric("Monthly salary (est.)", money(monthly_salary))

    st.write("")
    st.markdown("**Payback outcomes**")
    rates_pct = [
        float(st.session_state["debt_salary_to_debt_rate_1"]),
        float(st.session_state["debt_salary_to_debt_rate_2"]),
        float(st.session_state["debt_salary_to_debt_rate_3"]),
    ]

    for rp in rates_pct:
        sr = max(rp, 0.0) / 100.0
        m_contrib = monthly_salary * sr
        yrs = years_to_pay(total_debt_at_grad, r, m_contrib)

        if total_debt_at_grad <= 0:
            st.write("- No debt estimated at graduation based on your inputs.")
            break

        if yrs == float("inf"):
            st.warning(f"- If you pay **{rp:.0f}%** of salary (~{money(m_contrib)}/month), it will not clear (payment too low to cover interest).")
        else:
            st.success(f"- If you pay **{rp:.0f}%** of salary (~{money(m_contrib)}/month), you clear in about **{yrs:.1f} years**.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Actionable cut suggestions (ranked)
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### Actionable cut suggestions (ranked)")
    st.write("")

    total_income = float(chosen.get("total_income", 0.0))
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
    exp_rank = pd.DataFrame(rows).sort_values("ShareOfIncome", ascending=False, ignore_index=True).head(2)

    if exp_rank.empty:
        st.info("No expenses found to rank.")
    else:
        st.markdown("<ul>", unsafe_allow_html=True)
        for _, rrow in exp_rank.iterrows():
            cut_amount = 0.10 * float(rrow["Amount"])
            new_balance = monthly_balance + cut_amount
            st.markdown(
                f"""
                <li>
                    Cut <strong>{money(cut_amount)}</strong> from <strong>{rrow['Expense']}</strong>.
                    <br>
                    <span style="opacity:0.8;">
                        This moves your monthly balance from <strong>{money(monthly_balance)}</strong>
                        to <strong>{money(new_balance)}</strong>.
                    </span>
                </li>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</ul>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # All saved calculations table
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("#### All saved calculations")
    st.write("")

    saved_df = pd.DataFrame(saved)
    if not saved_df.empty:
        show_cols = ["label", "city", "run_date", "total_income", "total_expenses", "balance"]
        for c in show_cols:
            if c not in saved_df.columns:
                saved_df[c] = None
        saved_df = saved_df[show_cols].rename(
            columns={
                "label": "Label",
                "city": "City",
                "run_date": "Run date",
                "total_income": "Total income",
                "total_expenses": "Total expenses",
                "balance": "Balance",
            }
        )
        st.dataframe(saved_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No saved calculations to display.")
    st.markdown("</div>", unsafe_allow_html=True)

# PAGE E: SETTINGS
elif page == "Settings":
    st.subheader("Settings")
    st.write("")
    st.info("Preferences and configuration coming soon.")
