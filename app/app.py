import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_option_menu import option_menu

# ✅ Single page config – FIRST Streamlit command
st.set_page_config(
    page_title="Student Cost Survival Dashboard",
    page_icon="📊",
    layout="wide",
)

# ✅ CSS styles
st.markdown("""<style>...your css here...</style>""", unsafe_allow_html=True)

# ✅ Sidebar navigation
with st.sidebar:
    st.markdown("### Student Cost Survival")
    page = option_menu(
        menu_title=None,
        options=["Calculator", "City Compare", "My Plan", "Settings"],
        icons=["calculator", "globe2", "wallet2", "gear"],
        default_index=0,
    )

# Top bar
st.markdown("""
<div class="top-bar">
  <div class="top-left">
    <div class="logo-box">SC</div>
    <div>
      <div class="top-title">Student Cost Survival</div>
      <div style="font-size:0.8rem; opacity:0.7;">International Student Dashboard</div>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:0.6rem;">
    <span class="tag-pill">My City Plan</span>
    <span style="font-size:0.9rem; opacity:0.7;">Last updated: today</span>
  </div>
</div>
""", unsafe_allow_html=True)

# MAIN PAGE CONTENT
# TAB 2: PERSONAL CALCULATOR (USER INPUT)
if page == "Calculator":
    with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Enter your details (no constant rerun)")
    st.markdown("<div class='small-note'>Fill the form and click <b>Calculate</b>. "
                "We use City minimum wage to estimate job income.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- FORM (inputs only) ---
    with st.form("calculator_form"):
        # all your inputs here (city, wage, weeks_per_month, hours, expenses...)
        # ...
        submitted = st.form_submit_button("✅ Calculate")

    # --- RESULTS ONLY AFTER CLICK ---
    if not submitted:
        st.info("Fill the form above and click **Calculate** to see your budget, charts and download.")
    else:
        # Monthly job income estimate
        weekly_job_income = (wage * (hours_mon_fri + hours_sat)) + (wage * hours_sun * sunday_multiplier)
        monthly_job_income = weekly_job_income * weeks_per_month

        total_income = monthly_job_income + stipend
        total_expenses = rent + utilities + food + transport + phone_internet + misc_basic
        balance = total_income - total_expenses
        status = financial_status(balance)

        # Results cards
        st.markdown("<div class='card'>", unsafe_allow_html=True)
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

        # Charts (only after submitted)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Charts")

        ch1, ch2 = st.columns(2)
        with ch1:
            comparison_df = pd.DataFrame({
                "Category": ["Total Income", "Total Expenses"],
                "Amount": [total_income, total_expenses]
            })
            fig = px.bar(
                comparison_df,
                x="Category",
                y="Amount",
                text="Amount",
                title="Income vs Essential Expenses"
            )
            fig.update_traces(
                texttemplate="$%{text:,.0f}",
                textposition="outside",
                cliponaxis=False,
            )
            max_val = max(total_income, total_expenses)
            fig.update_yaxes(range=[0, max_val * 1.25])
            fig.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            exp_df = pd.DataFrame({
                "Expense": ["rent","utilities","food","transport","phone_internet","misc_basic"],
                "Amount": [rent, utilities, food, transport, phone_internet, misc_basic]
            })
            fig2 = px.bar(
                exp_df,
                x="Expense",
                y="Amount",
                text="Amount",
                title="Expense Breakdown"
            )
            fig2.update_traces(
                texttemplate="$%{text:,.0f}",
                textposition="outside",
                cliponaxis=False,
            )
            max_exp = max(exp_df["Amount"])
            fig2.update_yaxes(range=[0, max_exp * 1.25])
            fig2.update_layout(yaxis_title="USD", xaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Download user input summary (also only after submit)
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
        
 # TAB 3: CITY COMPARE
elif page == "City Compare":
with tab3:
    data = safe_read_csv("data/student_costs.csv")
    if data is None:
        st.error("Could not read data/student_costs.csv. Make sure the file path and name are correct.")
        st.stop()

    required_cols = {"city", "month", "campus_job_income", "stipend_income", "rent", "utilities", "food",
                     "transport", "phone_internet", "misc_basic"}
    missing = required_cols - set(data.columns)
    if missing:
        st.error(f"Your CSV is missing these columns: {sorted(list(missing))}")
        st.stop()

    # Prep
    expense_columns = ["rent", "utilities", "food", "transport", "phone_internet", "misc_basic"]
    data["month_dt"] = pd.to_datetime(data["month"], format="%Y-%m", errors="coerce")
    data["total_income"] = data["campus_job_income"] + data["stipend_income"]
    data["total_expenses"] = data[expense_columns].sum(axis=1)
    data["balance"] = data["total_income"] - data["total_expenses"]
    data["status"] = data["balance"].apply(financial_status)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("City Compare")
    st.markdown("<div class='small-note'>Compare cities across a selected month range using GA-style KPI tiles.</div>",
                unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Filters
    min_dt = data["month_dt"].min()
    max_dt = data["month_dt"].max()
    if pd.isna(min_dt) or pd.isna(max_dt):
        st.error("Month parsing failed. Ensure month column is in YYYY-MM format.")
        st.stop()

    cities = sorted(data["city"].dropna().unique().tolist())

    f1, f2, f3 = st.columns([1.4, 1.3, 1.3])
    with f1:
        compare_cities = st.multiselect("Cities to compare", cities, default=cities[:2] if len(cities) >= 2 else cities)
    with f2:
        start_month = st.selectbox(
            "Start month",
            sorted(data["month"].unique()),
            index=0
        )
    with f3:
        end_month = st.selectbox(
            "End month",
            sorted(data["month"].unique()),
            index=len(sorted(data["month"].unique())) - 1
        )

    if not compare_cities:
        st.warning("Select at least one city.")
        st.stop()

    start_dt = pd.to_datetime(start_month, format="%Y-%m", errors="coerce")
    end_dt = pd.to_datetime(end_month, format="%Y-%m", errors="coerce")

    if pd.isna(start_dt) or pd.isna(end_dt):
        st.error("Start/end month parsing failed. Use YYYY-MM.")
        st.stop()

    if start_dt > end_dt:
        st.error("Start month cannot be after end month.")
        st.stop()

    filt = data[
        (data["city"].isin(compare_cities)) &
        (data["month_dt"] >= start_dt) &
        (data["month_dt"] <= end_dt)
    ].copy()

    if filt.empty:
        st.warning("No rows found for the selected cities and month range.")
        st.stop()

    # GA-style KPI tiles per city (Avg per month over the selected range)
    summary = (
        filt.groupby("city", as_index=False)
            .agg(
                avg_income=("total_income", "mean"),
                avg_expenses=("total_expenses", "mean"),
                avg_balance=("balance", "mean"),
                months=("month", "nunique")
            )
    )

    # Add "savings rate" style metric
    summary["savings_rate"] = summary.apply(
        lambda r: (r["avg_balance"] / r["avg_income"]) if r["avg_income"] else 0.0, axis=1
    )

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### KPI Tiles (Average per month)")
    cols = st.columns(min(4, len(summary)))  # up to 4 tiles in one row
    for i, row in summary.iterrows():
        col = cols[i % len(cols)]
        with col:
            st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-label'>{row['city']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-value'>{money(row['avg_balance'])}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='kpi-sub'>Avg income {money(row['avg_income'])} • Avg expenses {money(row['avg_expenses'])}</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div class='kpi-sub'>Months: {int(row['months'])} • Savings rate: {row['savings_rate']*100:.1f}%</div>",
                unsafe_allow_html=True
            )
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Charts: Balance trend + expense mix like GA donut
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
        exp_mix = (
            filt.groupby("city", as_index=False)[expense_columns]
                .sum()
        )

        # Choose which city to view the donut for
        donut_city = st.selectbox("Donut city", compare_cities, index=0)
        row = exp_mix[exp_mix["city"] == donut_city]
        if not row.empty:
            amounts = [float(row[col].iloc[0]) for col in expense_columns]
            donut_df = pd.DataFrame({"Expense": expense_columns, "Amount": amounts})
            fig2 = px.pie(donut_df, names="Expense", values="Amount", hole=0.55)
            fig2.update_layout(title=f"{donut_city}: Total expenses by category")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No expense data for donut.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Table comparison (GA-style “top cities” table)
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
        "savings_rate": "Savings Rate (%)"
    })
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

#result row manipulation
if submitted:
    # Monthly job income estimate
    weekly_job_income = (wage * (hours_mon_fri + hours_sat)) + (wage * hours_sun * sunday_multiplier)
    monthly_job_income = weekly_job_income * weeks_per_month

    total_income = monthly_job_income + stipend
    total_expenses = rent + utilities + food + transport + phone_internet + misc_basic
    balance = total_income - total_expenses
    status = financial_status(balance)

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


elif page == "My Plan":
    st.subheader("My Plan")
    st.info("Savings goals, budgets, and plans coming soon.")

elif page == "Settings":
    st.subheader("Settings")
    st.info("Preferences and configuration coming soon.")


#the styling
st.markdown("""
<style>
.block-container {
    padding-top: 3.0rem;
    max-width: 1300px;
}

/* Top bar */
.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 0.4rem 0.3rem 0.4rem;
    margin-bottom: 0.4rem;
}
.top-left {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.logo-box {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: #2563eb22;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.9rem;
}
.top-title {
    font-size: 1.05rem;
    font-weight: 600;
}
.tag-pill {
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.75rem;
    background: #111827;
    border: 1px solid #374151;
}

/* Sidebar icons (fake nav on left) */
.fake-sidebar {
    position: fixed;
    left: 12px;
    top: 80px;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    font-size: 1.1rem;
    opacity: 0.85;
}
.fake-sidebar div {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #020617;
    border: 1px solid #1f2933;
}
.fake-sidebar div.active {
    background: #111827;
    border-color: #f97316;
}

/* Generic card */
.card {
    padding: 0.75rem 0.9rem;
    border-radius: 14px;
    background: #020617;
    border: 1px solid #1f2937;
    margin-bottom: 0.6rem;
}
.card h3, .card h4 {
    margin: 0 0 0.2rem 0;
}

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

/* Small note */
.small-note {opacity: 0.75; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)



# Minimum wage defaults 
CITY_MIN_WAGE = {
    "Saint Louis": 12.30,   # example placeholder (you can update)
    "Chicago": 15.80,
    "New York City": 16.00,
    "Los Angeles": 16.90,
}

DEFAULT_CITY = "Saint Louis" if "Saint Louis" in CITY_MIN_WAGE else list(CITY_MIN_WAGE.keys())[0]


# Helpers
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

# Title
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.title("International Student Cost Survival Dashboard")
st.markdown("<div class='small-note'>Use the sample dashboard or switch to the calculator to enter your own numbers.</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

tab2, tab3 = st.tabs(["🧮 Personal Calculator (Input)", "🌍 City Compare"])
