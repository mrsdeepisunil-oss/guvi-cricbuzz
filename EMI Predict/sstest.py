# import streamlit as st
# import pandas as pd
# import numpy as np
# import mlflow.sklearn

# # --- 1. CONFIGURATION & MLFLOW SETUP ---
# st.set_page_config(page_title="EMIPredict AI", layout="wide")
# # Ensure this matches your running MLflow server
# mlflow.set_tracking_uri("http://127.0.0.1:5000")

# # --- 2. HELPERS ---
# @st.cache_resource
# def load_models():
#     """Load both models from the MLflow Registry."""
#     clf = mlflow.sklearn.load_model("models:/EMI_Loan_RandomForest_Model/latest")
#     reg = mlflow.sklearn.load_model("models:/EMI_Max_Amount_Regressor/latest")
#     return clf, reg

# def auto_align(model, df):
#     """Aligns the input DataFrame columns to match the model's training schema."""
#     if hasattr(model, 'feature_names_in_'):
#         expected = model.feature_names_in_
#         for col in expected:
#             if col not in df.columns:
#                 df[col] = 0
#         return df[expected]
#     return df

# # --- 3. MAIN NAVIGATION ---
# page = st.sidebar.radio("Navigation", ["Home", "Predictions"])

# if page == "Home":
#     st.title("🏦 Welcome to EMIPredict AI")
#     st.write("Use the sidebar to navigate to the Predictive Engine.")

# elif page == "Predictions":
#     st.title("🎯 Dual-Engine Predictive Analysis")
    
#     # --- SIDEBAR INPUTS ---
#     with st.sidebar:
#         st.header("👤 Customer Profile")
#         u_age = st.number_input("Age", 18, 100, 30)
#         u_salary = st.number_input("Monthly Salary", value=85000)
#         u_credit = st.slider("Credit Score", 300, 850, 720)
#         u_bank = st.number_input("Bank Balance", value=250000)
#         u_years = st.number_input("Years of Employment", value=5.5)
#         u_edu = st.selectbox("Education", ["High School", "Graduate", "Professional", "Post Graduate"])

#     # --- MAIN FORM ---
#     with st.form("main_analysis"):
#         st.subheader("💰 Loan Request Details")
#         c1, c2 = st.columns(2)
#         with c1:
#             u_req_amt = st.number_input("Loan Amount Requested", value=500000)
#             u_rent = st.number_input("Monthly Rent", value=15000)
#         with c2:
#             u_tenure = st.number_input("Tenure (Months)", value=36)
#             u_cur_emi = st.number_input("Current EMI", value=5000)
        
#         u_gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
#         analyze_btn = st.form_submit_button("🚀 RUN FULL INTELLIGENCE")

#     # --- 4. PROCESSING & INFERENCE ---
#     if analyze_btn:
#         try:
#             clf_model, reg_model = load_models()

#             # Simple Feature Engineering
#             total_exp = u_rent + 25000 
#             disp_income = u_salary - total_exp - u_cur_emi
#             req_emi_val = u_req_amt / u_tenure
            
#             data_dict = {
#                 "age": u_age, 
#                 "monthly_salary": u_salary, 
#                 "years_of_employment": u_years,
#                 "monthly_rent": u_rent, 
#                 "current_emi_amount": u_cur_emi, 
#                 "credit_score": u_credit, 
#                 "bank_balance": u_bank, 
#                 "requested_amount": u_req_amt, 
#                 "requested_tenure": u_tenure,
#                 "total_monthly_expenditure": total_exp, 
#                 "disposable_income": disp_income, 
#                 "requested_emi": req_emi_val, 
#                 "dti_ratio": u_cur_emi / (u_salary + 1)
#             }

#             # Handle Encodings
#             data_dict['gender_Male'] = 1 if u_gender == "Male" else 0
#             data_dict['gender_Female'] = 1 if u_gender == "Female" else 0

#             # --- ASSIGN TO q2024 ---
#             q2024 = pd.DataFrame([data_dict])

#             st.divider()
#             st.subheader("Results Dashboard")
#             res_c1, res_c2 = st.columns(2)

#             # Engine 1: Risk Analysis
#             with res_c1:
#                 st.markdown("### 🛡️ Risk Analysis")
#                 q2024_clf = auto_align(clf_model, q2024.copy())
#                 pred_class = clf_model.predict(q2024_clf)[0]
                
#                 status_map = {0: "❌ Denied", 1: "⚠️ High Risk", 2: "✅ Eligible"}
#                 st.metric("Eligibility Status", status_map.get(pred_class, "Unknown"))
#                 st.progress(min(1.0, 0.33 * (pred_class + 1)))

#             # Engine 2: Capacity Analysis
#             with res_c2:
#                 st.markdown("### 💰 Capacity Analysis")
#                 q2024_reg = auto_align(reg_model, q2024.copy())
#                 pred_max_emi = reg_model.predict(q2024_reg)[0]
                
#                 st.metric("Max Affordable EMI", f"₹{pred_max_emi:,.2f}")
                
#                 if req_emi_val > pred_max_emi:
#                     st.error(f"Alert: Requested EMI (₹{req_emi_val:,.0f}) exceeds capacity.")
#                 else:
#                     st.success("Safe: EMI is within capacity.")

#         except Exception as e:
#             st.error(f"Critical System Error: {e}")
#             st.info("💡 Make sure your MLflow server is running and models are registered correctly.")


import streamlit as st
import pandas as pd
import numpy as np
import mlflow.sklearn

# --- 1. SETUP & MODEL LOADING ---
mlflow.set_tracking_uri("http://127.0.0.1:5000")

@st.cache_resource
def load_analysis_engines():
    """Fetches the latest registered models from MLflow."""
    clf = mlflow.sklearn.load_model("models:/EMI_Loan_RandomForest_Model/latest")
    reg = mlflow.sklearn.load_model("models:/EMI_Max_Amount_Regressor/latest")
    return clf, reg

def auto_align(model, df):
    """Aligns user features to match the exact schema used during model training."""
    if hasattr(model, 'feature_names_in_'):
        expected = model.feature_names_in_
        for col in expected:
            if col not in df.columns:
                df[col] = 0
        return df[expected]
    return df

# --- 2. USER INTERFACE ---
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
        clf, reg = load_analysis_engines()

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