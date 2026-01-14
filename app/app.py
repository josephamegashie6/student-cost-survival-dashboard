import pandas as pd
import streamlit as st
import plotly.express as px


# Page config + light styling

st.set_page_config(
    page_title="Student Cost Survival Dashboard",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; max-width: 1200px;}
h1, h2, h3 {margin-bottom: 0.4rem;}
.section-card {
    padding: 1rem 1.1rem;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    background: rgba(255,255,255,0.03);
    margin-bottom: 0.8rem;
}
.small-note {opacity: 0.75; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Minimum wage defaults (edit these)
# -----------------------------
CITY_MIN_WAGE = {
    "Saint Louis": 12.30,   # example placeholder (you can update)
    "Chicago": 15.80,
    "New York City": 16.00,
    "Los Angeles": 16.90,
}

DEFAULT_CITY = "Saint Louis" if "Saint Louis" in CITY_MIN_WAGE else list(CITY_MIN_WAGE.keys())[0]

# -----------------------------
# Helpers
# -----------------------------
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

# -----------------------------
# Title
# -----------------------------
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.title("International Student Cost Survival Dashboard")
st.markdown("<div class='small-note'>Use the sample dashboard or switch to the calculator to enter your own numbers.</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📌 Sample Dashboard (CSV)", "🧮 Personal Calculator (Input)"])

# =========================================================
# TAB 1: SAMPLE DASHBOARD
# =========================================================
with tab1:
    data = safe_read_csv("data/student_costs.csv")

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Filters")
    if data is None:
        st.error("Could not read data/student_costs.csv. Make sure the file path and name are correct.")
        st.stop()

    # Basic guard if columns missing
    required_cols = {"city", "month", "campus_job_income", "stipend_income", "rent", "utilities", "food", "transport", "phone_internet", "misc_basic"}
    missing = required_cols - set(data.columns)
    if missing:
        st.error(f"Your CSV is missing these columns: {sorted(list(missing))}")
        st.stop()

    data["month_dt"] = pd.to_datetime(data["month"], format="%Y-%m", errors="coerce")

    c1, c2, c3 = st.columns([1.2, 1.2, 2])
    with c1:
        city = st.selectbox("City", sorted(data["city"].unique()))
    with c2:
        month = st.selectbox("Month", sorted(data.loc[data["city"] == city, "month"].unique()))
    with c3:
        st.markdown("<div class='small-note'>Tip: This tab uses your CSV. For user-entered data, use the Calculator tab.</div>", unsafe_allow_html=True)

    selected = data[(data["city"] == city) & (data["month"] == month)].copy()
    city_data = data[data["city"] == city].copy()

    if selected.empty:
        st.warning("No data found for that City + Month combination.")
        st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

    # Calculations
    expense_columns = ["rent", "utilities", "food", "transport", "phone_internet", "misc_basic"]

    selected["total_income"] = selected["campus_job_income"] + selected["stipend_income"]
    selected["total_expenses"] = selected[expense_columns].sum(axis=1)
    selected["balance"] = selected["total_income"] - selected["total_expenses"]
    selected["status"] = selected["balance"].apply(financial_status)

    city_data["total_income"] = city_data["campus_job_income"] + city_data["stipend_income"]
    city_data["total_expenses"] = city_data[expense_columns].sum(axis=1)
    city_data["balance"] = city_data["total_income"] - city_data["total_expenses"]
    city_data["status"] = city_data["balance"].apply(financial_status)

    # Layout: Data + Summary side-by-side
    left, right = st.columns([1.4, 1])

    with left:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Monthly Cost Data")
        input_cols = ["city","month","campus_job_income","stipend_income"] + expense_columns
        st.dataframe(selected[input_cols], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Key Indicators")
        total_income = float(selected["total_income"].iloc[0])
        total_expenses = float(selected["total_expenses"].iloc[0])
        balance = float(selected["balance"].iloc[0])
        status = selected["status"].iloc[0]

        m1, m2, m3 = st.columns(3)
        m1.metric("Income", money(total_income))
        m2.metric("Expenses", money(total_expenses))
        m3.metric("Balance", money(balance))

        if status == "Surplus":
            st.success("SURPLUS — You have buffer after essentials.")
        elif status == "Break-even":
            st.warning("BREAK-EVEN — You’re surviving, but no buffer.")
        else:
            st.error("DEFICIT — You’ll likely need support or expense cuts.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Download")
        csv = selected.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download selected month as CSV",
            data=csv,
            file_name=f"{city}_{month}_student_costs.csv",
            mime="text/csv"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Charts row
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Charts")

    ch1, ch2 = st.columns(2)

    with ch1:
        comparison_df = pd.DataFrame({
            "Category": ["Total Income", "Total Expenses"],
            "Amount": [total_income, total_expenses]
        })
        fig = px.bar(comparison_df, x="Category", y="Amount", text="Amount",
                     title="Monthly Income vs Essential Expenses")
        fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig.update_layout(yaxis_title="USD", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        expense_breakdown = pd.DataFrame({
            "Expense": expense_columns,
            "Amount": [float(selected[col].iloc[0]) for col in expense_columns]
        })
        fig2 = px.bar(expense_breakdown, x="Expense", y="Amount", text="Amount",
                      title="Monthly Essential Expense Breakdown")
        fig2.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig2.update_layout(yaxis_title="USD", xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    # Trend chart full width
    city_data["month_dt"] = pd.to_datetime(city_data["month"], format="%Y-%m", errors="coerce")
    city_trend = city_data.sort_values("month_dt")
    fig3 = px.line(city_trend, x="month_dt", y="balance", markers=True,
                   title=f"Monthly Balance Trend - {city}")
    fig3.update_layout(xaxis_title="Month", yaxis_title="Balance (USD)")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 2: PERSONAL CALCULATOR (USER INPUT)
# =========================================================
with tab2:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Enter your details (no constant rerun)")
    st.markdown("<div class='small-note'>Fill the form and click <b>Calculate</b>. We use City minimum wage to estimate job income.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Put inputs in a form so it only updates on button click
    with st.form("calculator_form"):
        top1, top2, top3 = st.columns([1.2, 1, 1])

        with top1:
            calc_city = st.selectbox("City", list(CITY_MIN_WAGE.keys()), index=list(CITY_MIN_WAGE.keys()).index(DEFAULT_CITY))
        with top2:
            min_wage = CITY_MIN_WAGE.get(calc_city, 15.0)
            wage = st.number_input("Minimum wage ($/hour)", min_value=0.0, value=float(min_wage), step=0.25)
        with top3:
            # This is how many weeks per month on average
            weeks_per_month = st.number_input("Weeks per month", min_value=3.0, max_value=5.0, value=4.33, step=0.01)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("### Other monthly income")
        stipend = st.number_input("Monthly stipend / support ($)", min_value=0.0, value=0.0, step=50.0)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("✅ Calculate")

    if submitted:
        # Monthly job income estimate
        weekly_job_income = (wage * (hours_mon_fri + hours_sat)) + (wage * hours_sun * sunday_multiplier)
        monthly_job_income = weekly_job_income * weeks_per_month

        total_income = monthly_job_income + stipend
        total_expenses = rent + utilities + food + transport + phone_internet + misc_basic
        balance = total_income - total_expenses
        status = financial_status(balance)

        # Results cards
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Results")

        r1, r2, r3, r4 = st.columns([1, 1, 1, 1])
        r1.metric("City", calc_city)
        r2.metric("Min wage", f"${wage:,.2f}/hr")
        r3.metric("Monthly job income (est.)", money(monthly_job_income))
        r4.metric("Monthly stipend", money(stipend))

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Income", money(total_income))
        k2.metric("Total Expenses", money(total_expenses))
        k3.metric("Balance", money(balance))

        if status == "Surplus":
            st.success("SURPLUS — You have buffer after essentials.")
        elif status == "Break-even":
            st.warning("BREAK-EVEN — You’re surviving, but no buffer.")
        else:
            st.error("DEFICIT — You’ll likely need support or expense cuts.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Charts
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("Charts")

        ch1, ch2 = st.columns(2)
        with ch1:
            comparison_df = pd.DataFrame({
                "Category": ["Total Income", "Total Expenses"],
                "Amount": [total_income, total_expenses]
            })
            fig = px.bar(comparison_df, x="Category", y="Amount", text="Amount",
                         title="Income vs Essential Expenses")
            fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
            fig.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            exp_df = pd.DataFrame({
                "Expense": ["rent","utilities","food","transport","phone_internet","misc_basic"],
                "Amount": [rent, utilities, food, transport, phone_internet, misc_basic]
            })
            fig2 = px.bar(exp_df, x="Expense", y="Amount", text="Amount",
                          title="Expense Breakdown")
            fig2.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
            fig2.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Download user input summary
        result_row = {
            "city": calc_city,
            "min_wage": wage,
            "weeks_per_month": weeks_per_month,
            "hours_mon_fri": hours_mon_fri,
            "hours_sat": hours_sat,
            "hours_sun": hours_sun,
            "sunday_multiplier": sunday_multiplier,
            "monthly_job_income_est": monthly_job_income,
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
            "misc_basic": misc_basic
        }
        out_df = pd.DataFrame([result_row])
        csv = out_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download your calculation as CSV",
            data=csv,
            file_name=f"{calc_city}_calculator_result.csv",
            mime="text/csv"
        )






