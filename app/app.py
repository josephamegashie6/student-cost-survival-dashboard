import pandas as pd
import streamlit as st
import plotly.express as px
st.title("International Student Cost Survival Dashboard")
data = pd.read_csv("data/student_costs.csv")
st.subheader("Monthly Cost Data")
st.dataframe(data)

#calculation
data["total_income"] = data["campus_job_income"] + data["stipend_income"]
expense_columns = [
  "rent",
  "utilities",
  "food",
  "transport",
  "phone_internet",
  "misc_basic"]

data["total_expenses"] = data[expense_columns).sum(axis=1)
data["balance"] = data["total_income"] - data["total_expenses']

st.subheader("Financial_Summary")
st.dataframe(data[["city", "month", "total_income", "total_expenses", "balance", "status"]])

data["balance"] = data["total_income"] - data["total_expenses']
def financial_status(balance): 
    if balance > 0:
        return "Surplus"
    elif balance == 0:
        return "Break-even"
    else:
        return "Deficit"

data["status"] = data["balance"].apply(financial_status)

st.subheader("Key Financial Indicators")

total_income = data["total_income"].iloc[0]
total_expenses = data["total_expenses"].iloc[0]
balance = data["balance"].iloc[0]
status = data["status"].iloc[0]

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
    "Amount": [data[col].iloc[0] for col in expense_columns]
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





