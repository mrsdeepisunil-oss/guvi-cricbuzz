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

# --- HELPER: FEATURE ALIGNMENT ---
def auto_align(model, df):
    """Aligns user features to match the exact schema used during model training."""
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
    st.title("🧬 EMI Eligibility")
    st.markdown("This engine calculates your **Eligibility Status** and **Affordability Limit** based on your unique features.")

    with st.form("feature_intelligence_form"):
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("👤 Profile & Income")
            u_salary = st.number_input("Monthly Net Income (₹)", value=85000)
            u_age = st.number_input("Current Age", 18, 70, 30)
            u_credit = st.slider("Credit Score", 300, 850, 720)
            u_years = st.number_input("Employment Years", value=5.0)

        with c2:
            st.subheader("💳 Obligations & Assets")
            u_rent = st.number_input("Monthly Rent/Home Exp (₹)", value=15000)
            u_cur_emi = st.number_input("Existing Monthly EMIs (₹)", value=5000)
            u_bank = st.number_input("Liquid Bank Balance (₹)", value=250000)
            u_dependents = st.number_input("Number of Dependents", 0, 10, 2)

        st.divider()
        st.subheader("🎯 Test Scenario")
        sc1, sc2 = st.columns(2)
        u_req_amt = sc1.number_input("Loan Amount to Test (₹)", value=500000)
        u_tenure = sc2.number_input("Desired Tenure (Months)", value=36)
        
        run_analysis = st.form_submit_button("🚀 CALCULATE ELIGIBILITY")

    # --- 3. THE ANALYTICAL CORE ---
    if run_analysis:
        try:
            clf, reg = load_models()

            # Feature Engineering: Generating the inputs the models crave
            total_exp = u_rent + u_cur_emi + 20000 # 20k baseline for living costs
            disp_income = u_salary - total_exp
            test_emi = u_req_amt / u_tenure
            
            feature_data = {
                "age": u_age,
                "monthly_salary": u_salary,
                "years_of_employment": u_years,
                "current_emi_amount": u_cur_emi,
                "credit_score": u_credit,
                "bank_balance": u_bank,
                "total_monthly_expenditure": total_exp,
                "disposable_income": disp_income,
                "requested_emi": test_emi,
                "dti_ratio": u_cur_emi / (u_salary + 1),
                "potential_dti": (u_cur_emi + test_emi) / (u_salary + 1)
            }

            # --- DATA VARIABLE: emi2026 ---
            emi2026 = pd.DataFrame([feature_data])

            # --- 4. PREDICTIONS ---
            # Eligibility Check (Classification)
            emi2026_clf = auto_align(clf, emi2026.copy())
            elig_pred = clf.predict(emi2026_clf)[0]
            
            # Max Capacity Check (Regression)
            emi2026_reg = auto_align(reg, emi2026.copy())
            max_capacity = reg.predict(emi2026_reg)[0]

            # --- 5. RESULTS DISPLAY ---
            st.divider()
            res1, res2 = st.columns(2)

            with res1:
                status_map = {0: "❌ Denied", 1: "⚠️ High Risk", 2: "✅ Eligible"}
                result_label = status_map.get(elig_pred, "Unknown")
                st.metric("Eligibility Status", result_label)
                
                if elig_pred == 2:
                    st.success("Your profile features suggest a strong likelihood of approval.")
                elif elig_pred == 1:
                    st.warning("You are on the edge. High DTI or Credit Score may be a factor.")
                else:
                    st.error("Financial features do not meet current approval thresholds.")

            with res2:
                st.metric("Max EMI Capacity", f"₹{max_capacity:,.2f}")
                
                # Affordability Comparison
                capacity_usage = (test_emi / max_capacity) * 100
                if test_emi > max_capacity:
                    st.error(f"Test EMI (₹{test_emi:,.0f}) exceeds your predicted limit!")
                else:
                    progress_val = float(min(capacity_usage / 100, 1.0))
                    st.progress(progress_val)
                    st.info(f"You are using {capacity_usage:.1f}% of your AI-predicted EMI capacity.")

        except Exception as e:
            st.error(f"System Error: {e}")

# --- PAGE 3: DATA INSIGHTS ---

elif page == "Data Insights":
    show_data_insights()


# --- PAGE 4: ADMIN ---
elif page == "Admin Dashboard":
    st.title("⚙️ System Admin")
    st.write(f"MLflow URI: `{MLFLOW_TRACKING_URI}`")
    st.metric("Registry Status", "Connected", delta="Sync Active")