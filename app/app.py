import pandas as pd
import streamlit as st
import plotly.express as px

st.title("International Student Cost Survival Dashboard")
data = pd.read_csv("data/student_costs.csv")

data["month_dt"] = pd.to_datetime(data["month"], format="%Y-%m")


st.sidebar.header("Filters")
city = st.sidebar.selectbox("City", sorted(data["city"].unique()))
month = st.sidebar.selectbox(
    "Month",
    sorted(data.loc[data["city"] == city, "month"].unique())
)

selected = data[(data["city"] == city) & (data["month"] == month)].copy()
city_data = data[data["city"] == city].copy()

if selected.empty:
    st.error("No data found for the selected City and Month.")
    st.stop()

st.subheader("Monthly Cost Data")
input_cols = [
    "city", "month",
    "campus_job_income", "stipend_income",
    "rent", "utilities", "food", "transport",
    "phone_internet", "misc_basic"
]
st.dataframe(selected[input_cols])

#calculation
selected["total_income"] = selected["campus_job_income"] + selected["stipend_income"]
expense_columns = [
  "rent",
  "utilities",
  "food",
  "transport",
  "phone_internet",
  "misc_basic"]

def financial_status(balance): 
    if balance > 0:
        return "Surplus"
    elif balance == 0:
        return "Break-even"
    else:
        return "Deficit"

selected["total_expenses"] = selected[expense_columns].sum(axis=1)
selected["balance"] = selected["total_income"] - selected["total_expenses"]
selected["status"] = selected["balance"].apply(financial_status)

city_data["total_income"] = city_data["campus_job_income"] + city_data["stipend_income"]
city_data["total_expenses"] = city_data[expense_columns].sum(axis=1)
city_data["balance"] = city_data["total_income"] - city_data["total_expenses"]
city_data["status"] = city_data["balance"].apply(financial_status)

st.subheader("Financial Summary")

summary = selected[["city", "month", "total_income", "total_expenses", "balance", "status"]].copy()

for col in ["total_income", "total_expenses", "balance"]:
    summary[col] = summary[col].map(lambda x: f"${x:,.0f}")

st.dataframe(summary)
csv = selected.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download selected month as CSV",
    data=csv,
    file_name=f"{city}_{month}_student_costs.csv",
    mime="text/csv"
)

st.subheader("Key Financial Indicators")

total_income = selected["total_income"].iloc[0]
total_expenses = selected["total_expenses"].iloc[0]
balance = selected["balance"].iloc[0]
status = selected["status"].iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric("Total Income ($)", f"{total_income:,.0f}")
col2.metric("Total Expenses ($)", f"{total_expenses:,.0f}")
col3.metric("Balance ($)", f"{balance:,.0f}")

if status == "Surplus":
    st.success("Financial Status: SURPLUS — You are financially stable at baseline.")
elif status == "Break-even":
    st.warning("Financial Status: BREAK-EVEN — Survival is possible but with no buffer.")
else:
    st.error("Financial Status: DEFICIT — Survival requires borrowing or external support.")

#graph_codes
st.subheader("Income vs Expenses")

comparison_df = pd.DataFrame({
    "Category": ["Total Income", "Total Expenses"],
    "Amount": [total_income, total_expenses]
})

fig = px.bar(
    comparison_df,
    x="Category",
    y="Amount",
    text="Amount",
    title="Monthly Income vs Essential Expenses"
)

fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
fig.update_layout(yaxis_title="USD", xaxis_title="", uniformtext_minsize=8, uniformtext_mode="hide")

st.plotly_chart(fig, use_container_width=True)

#expenses_breakdown
st.subheader("Expense Breakdown")

expense_breakdown = pd.DataFrame({
    "Expense": expense_columns,
    "Amount": [selected[col].iloc[0] for col in expense_columns]
})

fig2 = px.bar(
    expense_breakdown,
    x="Expense",
    y="Amount",
    text="Amount",
    title="Monthly Essential Expense Breakdown"
)

fig2.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
fig2.update_layout(yaxis_title="USD", xaxis_title="", uniformtext_minsize=8, uniformtext_mode="hide")

st.plotly_chart(fig2, use_container_width=True)

#balance_trend_chart
st.subheader("Balance Trend Over Time")

city_trend = city_data.sort_values("month_dt")

fig3 = px.line(
    city_trend,
    x="month_dt",
    y="balance",
    markers=True,
    title=f"Monthly Balance Trend - {city}"
)

fig3.update_layout(xaxis_title="Month", yaxis_title="Balance (USD)")
st.plotly_chart(fig3, use_container_width=True)






