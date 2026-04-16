import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from mlflow.tracking import MlflowClient

# 1. SIDEBAR NAVIGATION (Define 'page' here!)
st.sidebar.title("🚀 Navigation")
page = st.sidebar.radio("Go to", ["Home", "Predictions", "Data Insights", "Admin Dashboard"])

# 2. DEFINE THE DATA INSIGHTS FUNCTION
def show_data_insights():
    st.title("📊 Data Insights & Model Governance")
    
    try:
        # Using the dataset you uploaded
        df = pd.read_csv("emi_prediction_dataset.csv")
        
        tab1, tab2 = st.tabs(["📈 Business Analytics", "⚙️ MLflow Tracking"])

        with tab1:
            st.subheader("Financial Distributions")
            # Interactive Credit Score Plot
            fig = px.histogram(df, x="credit_score", color="emi_eligibility", barmode="overlay")
            st.plotly_chart(fig, use_container_width=True)
            
            # Salary vs EMI Capacity
            fig2 = px.scatter(df, x="monthly_salary", y="max_monthly_emi", color="emi_eligibility")
            st.plotly_chart(fig2, use_container_width=True)

        with tab2:
            st.subheader("Model Registry Info")
            client = MlflowClient()
            # This pulls the metrics you logged in your 'ttemi.ipynb'
            try:
                latest = client.get_latest_versions("EMI_Loan_RandomForest_Model", stages=["None"])[0]
                st.write(f"**Active Model Version:** {latest.version}")
                st.write(f"**Run ID:** {latest.run_id}")
            except:
                st.warning("Could not connect to MLflow Registry.")

    except Exception as e:
        st.error(f"Error loading insights: {e}")

# 3. PAGE ROUTING (The Logic Gate)
if page == "Home":
    st.write("Welcome to the Home Page")

elif page == "Predictions":
    st.write("Prediction Form goes here")

elif page == "Data Insights":
    # NOW we call the function because 'page' is defined
    show_data_insights()

elif page == "Admin Dashboard":
    st.write("Admin Settings")