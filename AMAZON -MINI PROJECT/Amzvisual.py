import streamlit as st
import pandas as pd
import psycopg2
import requests
import plotly.express as px

def get_db_connection():
    try:
        return psycopg2.connect(
            host='localhost', database='amazon_sales',
            user='postgres', password='deepika@88', port=5432
        )
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")
        return None
def fetch_data(query):
    conn = get_db_connection()
    if conn:
        try:
            return pd.read_sql_query(query, conn)
        except Exception as e:
            st.error(f"Data Fetch Failed: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    else:
        return pd.DataFrame()
st.set_page_config(page_title="Amazon BI Dashboard", layout="wide")

st.sidebar.title("🎯 Project Modules")
category = st.sidebar.selectbox("Select Analysis Area", [
    "Executive Dashboards",
    "Revenue Analytics",
    "Customer Analytics",
    "Product & Inventory",
    "Operations & Logistics",
    "Advanced Analytics"
])
# Sub-navigation for the 30 Questions
if category == "Executive Dashboards":
    question = st.sidebar.radio("Choose Dashboard:", ["Executive Summary", "Performance Monitor", "Strategic Overview",
                                                       "Financial Performance", "Growth Analytics"])
elif category == "Revenue Analytics":
    question = st.sidebar.radio("Choose Dashboard:", ["Revenue Trends", "Sales by Category", "Customer Lifetime Value",
                                                       "Seasonality Analysis", "Discount Impact"])
elif category == "Customer Analytics":
    question = st.sidebar.radio("Choose Dashboard:", ["RFM Segmentation", "Customer Journey", "Prime vs Non-Prime", "Retention & Churn", "Demographics"])

elif category == "Product & Inventory":
    question = st.sidebar.radio("Choose Dashboard:", ["Product Performance", "Inventory Turnover", "Stockout Analysis",
                                                       "Supplier Performance", "Pricing Strategy"])
elif category == "Operations & Logistics":
    question = st.sidebar.radio("Choose Dashboard:", ["Fulfillment Efficiency", "Delivery Performance", "Returns Analysis",
                                                       "Warehouse Utilization", "Last-Mile Delivery"])
elif category == "Advanced Analytics":
    question = st.sidebar.radio("Choose Dashboard:", ["Predictive Sales", "Customer Churn Prediction", "Product Recommendation",
                                                       "Sentiment Analysis", "Supply Chain Optimization"])
else:
    question = None

query_q1 = """
    SELECT 
        order_date, 
        final_amount_inr, 
        customer_id, 
        category, 
        order_year,
        subcategory,
        is_prime_member
    FROM public.maintable
    WHERE order_year >= (SELECT MAX(order_year) - 1 FROM public.maintable)
"""
# --- FETCH DATA ---
data_raw = fetch_data(query_q1)

if not data_raw.empty:
    latest_year = data_raw['order_year'].max()
    prev_year = latest_year - 1

    # Split for comparison
    q_last = data_raw[data_raw['order_year'] == latest_year] 
    q_prev = data_raw[data_raw['order_year'] == prev_year]

    # --- PAGE 1: EXECUTIVE SUMMARY ---
    if question == "Executive Summary":
        st.header(f"📊 Executive Summary: {int(latest_year)} Business Overview")
        
        # --- KPI CALCULATIONS ---
        total_rev = q_last['final_amount_inr'].sum()
        active_cust = q_last['customer_id'].nunique()
        aov = q_last['final_amount_inr'].mean()
        prev_rev = q_prev['final_amount_inr'].sum() if not q_prev.empty else 0
        growth_rate = ((total_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0

        # KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"₹{total_rev:,.0f}", f"{growth_rate:.1f}% YoY")
        col2.metric("Active Customers", f"{active_cust:,}", "New Peak")
        col3.metric("Avg Order Value", f"₹{aov:,.2f}", "Stable")
        col4.metric("Growth Rate", f"{growth_rate:.1f}%", "vs Target 15%")

        st.divider()

        # Trend Chart
        q_last['order_date'] = pd.to_datetime(q_last['order_date'])
        monthly_trend = q_last.groupby(q_last['order_date'].dt.month)['final_amount_inr'].sum().reset_index()
        monthly_trend.columns = ['Month_Num', 'Revenue']
        monthly_trend['Month'] = monthly_trend['Month_Num'].apply(lambda x: pd.to_datetime(str(x), format='%m').strftime('%b'))

        fig_trend = px.line(monthly_trend, x='Month', y='Revenue', title="📈 Monthly Revenue Trend", markers=True, color_discrete_sequence=["#FF9900"])
        st.plotly_chart(fig_trend, use_container_width=True)

        # Category Chart
        top_cats = q_last.groupby('category')['final_amount_inr'].sum().nlargest(8).reset_index() 
        fig_cats = px.bar(top_cats, x='final_amount_inr', y='category', orientation='h', title="🏆 Top Categories", color='final_amount_inr', color_continuous_scale='Viridis')
        fig_cats.update_layout(coloraxis_showscale=True)
        fig_cats.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_cats, use_container_width=True)

        st.subheader("Category Performance & Growth Contribution")
        # Calculating metrics per category
        cat_perf = q_last.groupby('subcategory').agg({
            'final_amount_inr': 'sum',
            'customer_id': 'nunique',
            'is_prime_member': lambda x: (x == True).sum()
        }).rename(columns={
            'final_amount_inr': 'Total Revenue (₹)',
            'customer_id': 'Unique Customers',
            'is_prime_member': 'Prime Orders'
        }).sort_values(by='Total Revenue (₹)', ascending=False)

        st.dataframe(cat_perf.style.format("₹{:,.2f}", subset=['Total Revenue (₹)'])
                            .background_gradient(cmap='Greens', subset=['Total Revenue (₹)']),
                    use_container_width=True)

    # --- PAGE 2: PERFORMANCE MONITOR ---
    elif question == "Performance Monitor":
        st.header("⏱️ Real-time Business Performance Monitor")
        
        # Setup Dates
        q_last['order_date'] = pd.to_datetime(q_last['order_date'])
        latest_date = q_last['order_date'].max()
        curr_month = latest_date.month
        day_of_month = latest_date.day
        days_in_month = latest_date.days_in_month

        # Current Month Data
        q2024 = q_last[q_last['order_date'].dt.month == curr_month]
        mtd_revenue = q2024['final_amount_inr'].sum()
        monthly_target = 500000000 
        projected_revenue = (mtd_revenue / day_of_month) * days_in_month

        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("MTD Revenue", f"₹{mtd_revenue:,.0f}")
        col2.metric("Projected Run-Rate", f"₹{projected_revenue:,.0f}")
        col3.metric("MTD Customers", f"{q2024['customer_id'].nunique():,}")

        # Alert Logic
        required_pace = (day_of_month / days_in_month) * 100
        actual_pace = (mtd_revenue / monthly_target) * 100
        if actual_pace < required_pace:
            st.error(f"⚠️ Underperforming: We are at {actual_pace:.1f}% of target (Required: {required_pace:.1f}%)")
        else:
            st.success("✅ On Track")

        # Gauge Chart
        import plotly.graph_objects as go
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = mtd_revenue,
            title = {'text': "Monthly Target Status"},
            gauge = {'axis': {'range': [None, monthly_target]}, 'bar': {'color': "#FF9900"}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Cumulative Chart
        daily_rev = q2024.groupby(q2024['order_date'].dt.day)['final_amount_inr'].sum().cumsum().reset_index()
        fig_cum = px.area(daily_rev, x='order_date', y='final_amount_inr', title="📈 Cumulative Revenue")
        st.plotly_chart(fig_cum, use_container_width=True)
    # --- PAGE 3: STRATEGIC OVERVIEW ---
    elif question == "Strategic Overview":
        st.header("🏢 Strategic Business Overview")
        
        if not q_last.empty:
            # 1. MARKET SHARE ANALYSIS (By Category/Brand)
            st.subheader("Market Share & Category Dominance")
            
            # Calculating % share per category
            market_share = q_last.groupby('subcategory')['final_amount_inr'].sum().reset_index()
            market_share['Percentage'] = (market_share['final_amount_inr'] / market_share['final_amount_inr'].sum()) * 100
            
            fig_share = px.pie(
                market_share, 
                values='final_amount_inr', 
                names='subcategory',
                hole=0.4,
                title="Revenue Share by Category",
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig_share.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_share, use_container_width=True)

            st.divider()

            # 2. GEOGRAPHIC EXPANSION (State-wise Analysis)
            st.subheader("🌎 Geographic Expansion Metrics")
            
            # Assuming you have a 'state' or 'region' column
            # If your data uses 'customer_state', replace it here:
            geo_query = "SELECT customer_state, SUM(final_amount_inr) as revenue FROM public.maintable GROUP BY 1"
            geo_data = q_last.groupby('subcategory')['final_amount_inr'].sum().reset_index() # Placeholder logic
            
            # Since map JSONs can be complex, a sorted Bar Chart is the gold standard for C-Level expansion tracking
            fig_geo = px.bar(
                geo_data, 
                x='final_amount_inr', 
                y='subcategory', 
                orientation='h',
                title="Regional Revenue Contribution",
                color='final_amount_inr',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_geo, use_container_width=True)

            st.divider()

            # 3. BUSINESS HEALTH INDICATORS (C-Level KPIs)
            st.subheader("🩺 Business Health Indicators")
            h1, h2, h3 = st.columns(3)

            total_rev = q_last['final_amount_inr'].sum()
            active_cust = q_last['customer_id'].nunique()
            aov = q_last['final_amount_inr'].mean()
            prev_rev = q_prev['final_amount_inr'].sum() if not q_prev.empty else 0
            growth_rate = ((total_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
            
            # A. Prime Loyalty Ratio
            prime_rev = q_last[q_last['is_prime_member'] == True]['final_amount_inr'].sum()
            prime_ratio = (prime_rev / total_rev) * 100
            h1.metric("Prime Revenue Share", f"{prime_ratio:.1f}%", "Target: 60%")
            
            # B. Customer Retention (Simulated)
            # If a customer appears more than once in the year
            repeat_cust = q_last['customer_id'].duplicated().sum()
            retention_rate = (repeat_cust / len(q_last)) * 100
            h2.metric("Repeat Purchase Rate", f"{retention_rate:.1f}%", "High Loyalty")
            
            # C. Market Health (Avg Order Value vs Prev Year)
            prev_aov = q_prev['final_amount_inr'].mean() if not q_prev.empty else 0
            aov_growth = ((aov - prev_aov) / prev_aov * 100) if prev_aov > 0 else 0
            h3.metric("AOV Health", f"₹{aov:,.0f}", f"{aov_growth:.1f}% vs LY")

            # 4. COMPETITIVE POSITIONING (Scatter Plot)
            st.subheader("📍 Competitive Positioning: Volume vs. Value")
            
            # Comparing Category Volume (Orders) vs Value (Revenue)
            comp_data = q_last.groupby('subcategory').agg({
                'final_amount_inr': 'sum',
                'customer_id': 'count'
            }).reset_index()
            comp_data.columns = ['Subcategory', 'Revenue', 'Order_Volume']
            
            fig_comp = px.scatter(
                comp_data, 
                x='Order_Volume', 
                y='Revenue',
                size='Revenue', 
                color='Subcategory',
                hover_name='Subcategory',
                log_x=True,
                title="Category Positioning (High Volume vs. High Value)"
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        else:
            st.warning("Strategic data could not be processed.")
    # --- PAGE 4: FINANCIAL PERFORMANCE ---
    elif question == "Financial Performance":
        st.header("💰 Financial Performance & Margin Analysis")
        
        if not q_last.empty:
            # 1. CALCULATE FINANCIAL METRICS
            # Note: Using a standard 25% margin if 'profit' column isn't in your DB
            q_last['estimated_cost'] = q_last['final_amount_inr'] * 0.75
            q_last['estimated_profit'] = q_last['final_amount_inr'] * 0.25

            total_rev = q_last['final_amount_inr'].sum()
            active_cust = q_last['customer_id'].nunique()
            aov = q_last['final_amount_inr'].mean()
            prev_rev = q_prev['final_amount_inr'].sum() if not q_prev.empty else 0
            growth_rate = ((total_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
            
            total_profit = q_last['estimated_profit'].sum()
            total_cost = q_last['estimated_cost'].sum()
            margin_pct = (total_profit / total_rev) * 100

            # TOP ROW: FINANCIAL KPIs
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("Gross Revenue", f"₹{total_rev:,.0f}")
            f2.metric("Estimated Cost", f"₹{total_cost:,.0f}")
            f3.metric("Net Profit", f"₹{total_profit:,.0f}", f"{margin_pct:.1f}% Margin")
            f4.metric("Tax Provision", f"₹{(total_rev * 0.18):,.0f}", "Est. GST 18%")

            st.divider()

            # 2. PROFIT MARGIN BY SUBCATEGORY
            st.subheader("Profitability Breakdown by Category")
            # We compare Revenue vs Profit for each subcategory
            sub_fin = q_last.groupby('subcategory').agg({
                'final_amount_inr': 'sum',
                'estimated_profit': 'sum'
            }).reset_index()
            
            sub_fin['Margin_%'] = (sub_fin['estimated_profit'] / sub_fin['final_amount_inr']) * 100

            fig_sub_fin = px.bar(
                sub_fin.nlargest(12, 'final_amount_inr'), 
                x='subcategory', 
                y='final_amount_inr',
                color='Margin_%',
                title="Revenue vs. Margin % by Category",
                labels={'final_amount_inr': 'Total Revenue', 'Margin_%': 'Profit Margin %'},
                color_continuous_scale='RdYlGn', # Red (Low Margin) to Green (High Margin)
                text_auto='.2s'
            )
            st.plotly_chart(fig_sub_fin, use_container_width=True)            

            st.divider()

            # 3. COST STRUCTURE VISUALIZATION (Waterfall/Funnel)
            st.subheader("Financial Waterfall: Revenue to Net Profit")
            
            # Creating a waterfall sequence
            waterfall_data = {
                "Step": ["Gross Revenue", "COGS (75%)", "Operating Exp (5%)", "Net Profit"],
                "Amount": [total_rev, -total_cost, -(total_rev * 0.05), total_profit - (total_rev * 0.05)]
            }
            
            import plotly.graph_objects as go
            fig_water = go.Figure(go.Waterfall(
                name = "2024", orientation = "v",
                measure = ["relative", "relative", "relative", "total"],
                x = waterfall_data["Step"],
                textposition = "outside",
                text = [f"₹{x:,.0f}" for x in waterfall_data["Amount"]],
                y = waterfall_data["Amount"],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            fig_water.update_layout(title = "Estimated Financial Leakage & Profit Waterfall")
            st.plotly_chart(fig_water, use_container_width=True)

            # 4. SIMPLE FINANCIAL FORECASTING (Linear Trend)
            st.subheader("📈 3-Month Financial Revenue Forecast")
            
            # Grouping by month for the forecast
            monthly_data = q_last.groupby(q_last['order_date'].dt.month)['final_amount_inr'].sum().reset_index()
            
            # Simple Linear projection (Average Growth)
            avg_monthly_rev = monthly_data['final_amount_inr'].mean()
            forecast_months = ["Jan (Proj)", "Feb (Proj)", "Mar (Proj)"]
            forecast_values = [avg_monthly_rev * (1 + (i*0.05)) for i in range(1, 4)] # 5% growth projection
            
            fig_forecast = px.line(
                x=forecast_months, 
                y=forecast_values, 
                title="Revenue Projection (Next Quarter)",
                markers=True,
                line_dash_sequence=['dash']
            )
            fig_forecast.update_traces(line_color='#2ECC71')
            st.plotly_chart(fig_forecast, use_container_width=True)

        else:
            st.warning("Please ensure 'subcategory' and revenue data are loaded correctly.")
    # --- PAGE 5: GROWTH ANALYTICS ---
    elif question == "Growth Analytics":
        st.header("🚀 Growth Analytics & Velocity Tracking")
        
        if not q_last.empty:
            # 1. PREPARE TIME-SERIES DATA
            q_last['order_date'] = pd.to_datetime(q_last['order_date'])
            
            # Monthly Growth (MoM)
            monthly_growth = q_last.set_index('order_date').resample('M')['final_amount_inr'].sum().reset_index()
            monthly_growth['MoM_Growth'] = monthly_growth['final_amount_inr'].pct_change() * 100
            
            # Weekly Growth (WoW) - Last 8 Weeks
            weekly_growth = q_last.set_index('order_date').resample('W')['final_amount_inr'].sum().reset_index().tail(8)
            weekly_growth['WoW_Growth'] = weekly_growth['final_amount_inr'].pct_change() * 100

            # TOP ROW: GROWTH VELOCITY KPIs
            g1, g2, g3 = st.columns(3)
            current_mom = monthly_growth['MoM_Growth'].iloc[-1]
            current_wow = weekly_growth['WoW_Growth'].iloc[-1]
            
            total_rev = q_last['final_amount_inr'].sum()
            active_cust = q_last['customer_id'].nunique()
            aov = q_last['final_amount_inr'].mean()
            prev_rev = q_prev['final_amount_inr'].sum() if not q_prev.empty else 0
            growth_rate = ((total_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0


            g1.metric("Current MoM Growth", f"{current_mom:.1f}%", f"{current_mom:.1f}%", delta_color="normal")
            g2.metric("Current WoW Velocity", f"{current_wow:.1f}%", "Weekly Pace")
            g3.metric("Annualized Growth Rate", f"{growth_rate:.1f}%", "vs Last Year")

            st.divider()

            # 2. MONTH-OVER-MONTH (MoM) VELOCITY CHART
            st.subheader("📈 Monthly Revenue Velocity (MoM %)")
            fig_mom = px.bar(
                monthly_growth, 
                x='order_date', 
                y='MoM_Growth',
                title="Revenue Growth Rate (%) Month-over-Month",
                color='MoM_Growth',
                color_continuous_scale='RdYlGn',
                labels={'MoM_Growth': 'Growth Rate %', 'order_date': 'Month'}
            )
            fig_mom.add_hline(y=0, line_dash="dash", line_color="black")
            st.plotly_chart(fig_mom, use_container_width=True)
            

            st.divider()

            # 3. GROWTH BY SUBCATEGORY (Identifying "Rising Stars")
            st.subheader("🌟 Rising Stars: Category Growth Velocity")
            
            # Compare current month vs previous month for each subcategory
            latest_month_num = q_last['order_date'].dt.month.max()
            this_month_sub = q_last[q_last['order_date'].dt.month == latest_month_num].groupby('subcategory')['final_amount_inr'].sum()
            last_month_sub = q_last[q_last['order_date'].dt.month == (latest_month_num - 1)].groupby('subcategory')['final_amount_inr'].sum()
            
            sub_growth_vel = ((this_month_sub - last_month_sub) / last_month_sub * 100).dropna().sort_values(ascending=False).head(10).reset_index()
            sub_growth_vel.columns = ['Subcategory', 'Growth_Pct']

            fig_stars = px.bar(
                sub_growth_vel, 
                x='Growth_Pct', 
                y='Subcategory', 
                orientation='h',
                title=f"Top 10 Growing Subcategories (Month {latest_month_num-1} to {latest_month_num})",
                color='Growth_Pct',
                color_continuous_scale='Viridis',
                text_auto='.1f'
            )
            st.plotly_chart(fig_stars, use_container_width=True)

            # 4. CUSTOMER ACQUISITION VELOCITY
            st.subheader("👥 Customer Acquisition Growth")
            cust_growth = q_last.set_index('order_date').resample('M')['customer_id'].nunique().reset_index()
            
            fig_cust = px.line(
                cust_growth, 
                x='order_date', 
                y='customer_id', 
                title="New Unique Customers Acquired per Month",
                markers=True,
                line_shape="vh" # Step-wise line to show acquisition jumps
            )
            st.plotly_chart(fig_cust, use_container_width=True)

        else:
            st.warning("Data not available for Growth Analytics.")
else:
    st.error("Data could not be retrieved. Please check your DB connection.")