import pandas as pd
import streamlit as st
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


