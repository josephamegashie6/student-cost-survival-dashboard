import pandas as pd
import streamlit as st
st.title("International Student Cost Survival Dashboard")
data = pd.read_csv("data/student_Costs.csv")
st.subheader("Monthly Cost Data")
st.dataframe(data)
