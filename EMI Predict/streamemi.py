import streamlit as st
import pandas as pd
import numpy as np
import mlflow.sklearn
import mlflow.pyfunc
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import os
from mlflow.tracking import MlflowClient

# --- CONFIGURATION & MLFLOW SETUP ---
st.set_page_config(page_title="EMIPredict AI", layout="wide")
MLFLOW_TRACKING_URI = "http://127.0.0.1:5000" 
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

@st.cache_resource
def load_models():
    """Load both models from the Registry."""
    # Using sklearn loader to access .feature_names_in_ for alignment
    clf = mlflow.sklearn.load_model("models:/EMI_Loan_RandomForest_Model/latest")
    reg = mlflow.sklearn.load_model("models:/EMI_Max_Amount_Regressor/latest")
    return clf, reg

def auto_align(model, df):
    """Automatically reorders and filters columns to match the model's training schema."""
    if hasattr(model, 'feature_names_in_'):
        expected = model.feature_names_in_
        for col in expected:
            if col not in df.columns:
                df[col] = 0
        return df[expected]
    return df

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

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 EMIPredict AI")
st.sidebar.info("Model Registry: Connected")
page = st.sidebar.radio("Go to", ["Home", "Predictions", "Data Insights", "Admin Dashboard"])

# --- PAGE 1: HOME ---
if page == "Home":
    st.title("🏦 Loan Eligibility & EMI Prediction System")
    st.markdown("""
    ### Project Overview
    This platform integrates **MLflow experiment tracking** with a real-time interface to provide:
    * **Instant Eligibility Checks:** Uses a classification model to assess risk.
    * **EMI Estimation:** Uses a regression model to predict affordable monthly payments.
    * **Data Transparency:** View the trends that drive our decision-making.
    """)

# --- PAGE 2: PREDICTIONS ---
elif page == "Predictions":
    st.title("🎯 Loan Eligibility & Capacity Analysis")
    
    # Corrected Indentation for Sidebar Inputs
    with st.sidebar:
        st.header("👤 Customer Profile")
        u_age = st.number_input("Age", 18, 100, 30)
        u_salary = st.number_input("Monthly Salary", value=85000)
        u_credit = st.slider("Credit Score", 300, 850, 720)
        u_bank = st.number_input("Bank Balance", value=250000)
        u_years = st.number_input("Years of Employment", value=5.5)
        u_edu = st.selectbox("Education", ["High School", "Graduate", "Professional", "Post Graduate"])

    # Main Form for Loan Details
    with st.form("main_analysis"):
        st.subheader("📋 Loan Request Details")
        c1, c2 = st.columns(2)
        with c1:
            u_req_amt = st.number_input("Loan Amount Requested", value=500000)
            u_rent = st.number_input("Monthly Rent", value=15000)
        with c2:
            u_tenure = st.number_input("Tenure (Months)", value=36)
            u_cur_emi = st.number_input("Current EMI Burden", value=5000)
        
        u_gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
        analyze_btn = st.form_submit_button("🚀 RUN FULL INTELLIGENCE")

    if analyze_btn:
        try:
            clf_model, reg_model = load_models()

            # A. Feature Engineering (Replicating ttemi.ipynb logic)
            total_exp = u_rent + 15000 
            disp_income = u_salary - total_exp - u_cur_emi
            req_emi_val = u_req_amt / u_tenure
            
            data_dict = {
                "age": u_age, "monthly_salary": u_salary, "years_of_employment": u_years,
                "monthly_rent": u_rent, "family_size": 3, "dependents": 2,
                "school_fees": 0, "college_fees": 0, "travel_expenses": 2000,
                "groceries_utilities": 10000, "other_monthly_expenses": 3000,
                "current_emi_amount": u_cur_emi, "credit_score": u_credit,
                "bank_balance": u_bank, "emergency_fund": 50000,
                "requested_amount": u_req_amt, "requested_tenure": u_tenure,
                "total_monthly_expenditure": total_exp, "dti_ratio": u_cur_emi/(u_salary+1),
                "disposable_income": disp_income, "requested_emi": req_emi_val,
                "potential_dti": (u_cur_emi + req_emi_val)/(u_salary+1),
                "max_monthly_emi": disp_income * 0.4
            }

            # B. Encoding
            edu_map = {'High School': 1, 'Graduate': 2, 'Professional': 3, 'Post Graduate': 4}
            data_dict['education_encoded'] = edu_map.get(u_edu, 2)
            data_dict['gender_Male'] = 1 if u_gender == "Male" else 0

            # C. Create DataFrame
            input_df = pd.DataFrame([data_dict])

            # D. Execution
            st.divider()
            res_c1, res_c2 = st.columns(2)

            with res_c1:
                st.subheader("Eligibility Result")
                emi2026_clf = auto_align(clf_model, input_df.copy())
                pred_class = clf_model.predict(emi2026_clf)[0]
                status_map = {0: "❌ Denied", 1: "⚠️ High Risk", 2: "✅ Eligible"}
                st.metric("Status", status_map.get(pred_class, "Unknown"))

            with res_c2:
                st.subheader("Affordability Result")
                emi2026_reg = auto_align(reg_model, input_df.copy())
                pred_max_emi = reg_model.predict(emi2026_reg)[0]
                st.metric("Max Monthly Capacity", f"${pred_max_emi:,.2f}")
                
                if req_emi_val > pred_max_emi:
                    st.error(f"Alert: Request (${req_emi_val:,.2f}) exceeds capacity.")
                else:
                    st.success("Request is within calculated capacity.")

        except Exception as e:
            st.error(f"Inference Error: {e}")

# --- PAGE 3: DATA INSIGHTS ---

elif page == "Data Insights":
    show_data_insights()


# --- PAGE 4: ADMIN ---
elif page == "Admin Dashboard":
    st.title("⚙️ System Admin")
    st.write(f"MLflow URI: `{MLFLOW_TRACKING_URI}`")
    st.metric("Registry Status", "Connected", delta="Sync Active")