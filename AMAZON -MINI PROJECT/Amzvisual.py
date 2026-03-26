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
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=150)

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
# --- REVENUE ANALYTICS PAGES ---
query_q2 = """
    SELECT 
        order_date, 
        final_amount_inr, 
        subcategory,
        customer_id,
        customer_state,  
        customer_city,   
        customer_tier,
        is_prime_member
    FROM public.maintable
    WHERE order_year >= (SELECT MAX(order_year) - 5 FROM public.maintable)
"""
# --- FETCH DATA ---
data_raw2 = fetch_data(query_q2)
if category == "Revenue Analytics":
    # 1. Ensure Data is Pre-processed once for all sub-pages in this category
    if not data_raw2.empty:
        # Create a copy to avoid SettingWithCopy warnings
        df_rev = data_raw2.copy()
        df_rev['order_date'] = pd.to_datetime(df_rev['order_date'])
        
        # --- PAGE: REVENUE TRENDS ---
        if question == "Revenue Trends":
            st.header("📈 Revenue Trend Analysis")
            
            # Interactive Filter
            time_period = st.radio("Select View:", ["Monthly", "Quarterly", "Yearly"], horizontal=True)
            
            # Map selection to pandas resample codes
            resample_map = {"Monthly": "M", "Quarterly": "Q", "Yearly": "Y"}
            resample_code = resample_map[time_period]

            # Aggregating Data
            trend_df = df_rev.set_index('order_date')['final_amount_inr'].resample(resample_code).sum().reset_index()
            trend_df['Growth_Rate'] = trend_df['final_amount_inr'].pct_change() * 100
            
            # Visual 1: Main Trend
            fig_revenue = px.area(
                trend_df, x='order_date', y='final_amount_inr',
                title=f"{time_period} Revenue Trend (6-Year History)",
                markers=True, 
                # title=f"{time_period} Revenue Pattern",
                color_discrete_sequence=["#00A8E1"]
            )
            st.plotly_chart(fig_revenue, use_container_width=True)

            # Visual 2: Growth Rate
            fig_growth = px.bar(
                trend_df, x='order_date', y='Growth_Rate',
                title=f"{time_period} Growth Rate (%)",
                color='Growth_Rate',
                color_continuous_scale='PiYG'
            )
            fig_growth.add_hline(y=0, line_dash="dash", line_color="black")
            st.plotly_chart(fig_growth, use_container_width=True)

            st.divider()

            # Visual 3: Forecasting
            st.subheader("🔮 6-Month Revenue Forecast")
            monthly_data = df_rev.set_index('order_date')['final_amount_inr'].resample('M').sum().reset_index()
            avg_growth = monthly_data['final_amount_inr'].pct_change().mean()
            last_rev = monthly_data['final_amount_inr'].iloc[-1]
            
            future_dates = pd.date_range(start=monthly_data['order_date'].iloc[-1], periods=7, freq='M')[1:]
            forecast_values = [last_rev * (1 + avg_growth)**i for i in range(1, 7)]
            forecast_df = pd.DataFrame({'Date': future_dates, 'Forecasted_Revenue': forecast_values})
            
            fig_forecast = px.line(forecast_df, x='Date', y='Forecasted_Revenue', markers=True, color_discrete_sequence=["#2ECC71"])
            st.plotly_chart(fig_forecast, use_container_width=True)

            # Visual 4: Seasonality
            st.subheader("🍂 Seasonal Variations")
            df_rev['Month_Name'] = df_rev['order_date'].dt.month_name()
            month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December']
            
            seasonal_avg = df_rev.groupby('Month_Name')['final_amount_inr'].mean().reindex(month_order).reset_index()
            fig_season = px.line(seasonal_avg, x='Month_Name', y='final_amount_inr', markers=True)
            st.plotly_chart(fig_season, use_container_width=True)

        # --- PAGE: SALES BY CATEGORY ---
        elif question == "Sales by Category":
            st.header("📂 Subcategory Performance & Market Share")
            
            # 1. Bar Chart: Revenue by Subcategory
            sub_perf = df_rev.groupby('subcategory')['final_amount_inr'].sum().reset_index()
            sub_perf = sub_perf.sort_values('final_amount_inr', ascending=False)
            
            fig_sub_bar = px.bar(
                sub_perf.head(15), x='final_amount_inr', y='subcategory',
                orientation='h', title="Top 15 Subcategories by Revenue",
                color='final_amount_inr', color_continuous_scale='Viridis'
            )
            fig_sub_bar.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_sub_bar, use_container_width=True)

            st.divider()

            # 2. Market Share & Table
            col1, col2 = st.columns(2)
            with col1:
                st.write("📊 **Market Share**")
                fig_pie = px.pie(sub_perf.head(10), values='final_amount_inr', names='subcategory', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                st.write("📈 **Top 10 Details**")
                st.dataframe(sub_perf.head(10), use_container_width=True)

            st.divider()

            # 3. Time Trend for Top Subcategories
            st.subheader("Monthly Trend: Top 5 Subcategories")
            top_5_subs = sub_perf.head(5)['subcategory'].tolist()
            trend_data = df_rev[df_rev['subcategory'].isin(top_5_subs)].copy()
            trend_data['Month_Year'] = trend_data['order_date'].dt.strftime('%Y-%m')
            
            sub_trend = trend_data.groupby(['Month_Year', 'subcategory'])['final_amount_inr'].sum().reset_index()
            fig_trend = px.line(sub_trend, x='Month_Year', y='final_amount_inr', color='subcategory', markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)
        
        # --- PAGE: GEOGRAPHIC REVENUE ANALYSIS (Question 8) ---
        elif question == "Geographic Revenue Analysis":
            st.header("🌎 Geographic Market Penetration")
            
            if not df_rev.empty:
                # 1. STATE-WISE PERFORMANCE (Interactive Map)
                st.subheader("State-level Revenue Distribution")
                state_data = df_rev.groupby('customer_state')['final_amount_inr'].sum().reset_index()
                
                # Note: For a real India map, you'd need a GeoJSON file. 
                # For now, we use a high-impact bar chart and a "Heatmap" style table.
                fig_state = px.bar(
                    state_data.sort_values('final_amount_inr', ascending=False),
                    x='customer_state', y='final_amount_inr',
                    title="Revenue by State",
                    color='final_amount_inr',
                    color_continuous_scale='GnBu',
                    labels={'customer_state': 'State', 'final_amount_inr': 'Revenue (₹)'}
                )
                st.plotly_chart(fig_state, use_container_width=True)

                st.divider()

                # 2. CITY & TIER DRILL-DOWN (Sunburst Chart)
                # This shows the hierarchy: Tier -> State -> City
                st.subheader("📍 Tier & City-wise Growth Patterns")
                
                # Ensure you have 'customer_tier' (Tier 1, Tier 2, etc.) in your data
                # If not, we can simulate it for the visual:
                if 'customer_tier' not in df_rev.columns:
                    df_rev['customer_tier'] = 'Tier 2' # Default fallback
                
                geo_drill = df_rev.groupby(['customer_tier', 'customer_state', 'customer_city'])['final_amount_inr'].sum().reset_index()
                
                fig_sun = px.sunburst(
                    geo_drill, 
                    path=['customer_tier', 'customer_state', 'customer_city'], 
                    values='final_amount_inr',
                    title="Revenue Hierarchy: Tier > State > City",
                    color='final_amount_inr',
                    color_continuous_scale='RdBu'
                )
                st.plotly_chart(fig_sun, use_container_width=True)

                st.divider()

                # 3. MARKET PENETRATION OPPORTUNITIES
                st.subheader("🎯 Market Penetration Insights")
                g1, g2 = st.columns(2)
                
                with g1:
                    # Top Performing Cities
                    top_cities = df_rev.groupby('customer_city')['final_amount_inr'].sum().nlargest(10).reset_index()
                    st.write("**Top 10 Cities by Revenue**")
                    st.table(top_cities)
                
                with g2:
                    # Low Penetration / Growth Areas
                    # Cities with high orders but low AOV (High potential for upsell)
                    penetration = df_rev.groupby('customer_city').agg({
                        'final_amount_inr': 'mean',
                        'customer_id': 'count'
                    }).reset_index()
                    penetration.columns = ['City', 'Avg_Order_Value', 'Order_Count']
                    
                    st.write("**High Volume / Low Value Cities (Growth Opportunity)**")
                    st.dataframe(penetration[penetration['Order_Count'] > 5].nsmallest(10, 'Avg_Order_Value'))

        # --- PAGE: SEASONALITY ANALYSIS (Question 9) ---
        elif question == "Seasonality Analysis":
            st.header("🍂 Seasonality & Peak Performance")
            
            if not df_rev.empty:
                # 1. Force the Heatmap to be larger
                st.subheader("🔥 Sales Intensity Heatmap")
                df_rev['Month'] = df_rev['order_date'].dt.month_name()
                df_rev['Day_of_Week'] = df_rev['order_date'].dt.day_name()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                # Check how many months we actually have
                available_months = df_rev['Month'].unique()
                
                heatmap_data = df_rev.groupby(['Month', 'Day_of_Week'])['final_amount_inr'].sum().unstack().reindex(
                    index=available_months, # Only show months we have data for
                    columns=day_order
                )
                
                fig_heat = px.imshow(
                    heatmap_data,
                    labels=dict(x="Day of Week", y="Month", color="Revenue"),
                    color_continuous_scale='YlOrRd',
                    aspect="auto" # This helps the heatmap fill the space
                )
                # Manually set height so it's not tiny
                fig_heat.update_layout(height=400) 
                st.plotly_chart(fig_heat, use_container_width=True)

                st.divider()

                # 2. Improved Insights Logic
                st.subheader("🎊 Seasonal Optimization Insights")
                
                monthly_total = df_rev.groupby('Month')['final_amount_inr'].sum()
                avg_monthly_rev = monthly_total.mean()
                
                # We find peaks by comparing to the average of available data
                peaks = monthly_total[monthly_total > (avg_monthly_rev * 1.1)].index.tolist()

                if peaks:
                    st.success(f"**Peak Performance Detected:** {', '.join(peaks)}")
                    st.info("💡 **Strategy:** Increase ad spend and inventory levels 30 days prior to these months.")
                else:
                    st.info("No significant seasonal spikes detected. Sales appear steady across the loaded period.")
      
        # --- PAGE: DISCOUNT IMPACT (Question 10) ---
        elif question == "Discount Impact":
            st.header("🏷️ Discount & Price Elasticity Analysis")            
                          
            if not df_rev.empty:
                # 1. KPIs: THE "INSIGHT" CARDS
                prime_stats = df_rev.groupby('is_prime_member')['final_amount_inr'].agg(['mean', 'sum', 'count']).reset_index()
                
                # Get the mean values for comparison
                prime_aov = prime_stats.loc[prime_stats['is_prime_member'] == 1, 'mean'].values[0]
                non_prime_aov = prime_stats.loc[prime_stats['is_prime_member'] == 0, 'mean'].values[0]
                diff_pct = ((prime_aov - non_prime_aov) / non_prime_aov) * 100

                st.subheader("💡 Strategic Value of Prime")
                kpi1, kpi2, kpi3 = st.columns(3)
                
                kpi1.metric("Prime Avg Order Value", f"₹{prime_aov:,.2f}")
                kpi2.metric("Non-Prime Avg Order Value", f"₹{non_prime_aov:,.2f}")
                # This shows the 33.8% as a green "Up" arrow
                kpi3.metric("Prime Value Lift", f"{diff_pct:.1f}%", delta=f"{diff_pct:.1f}%")

                st.divider()

                # 1. PRICE ELASTICITY SCATTER PLOT
                st.subheader("Price Elasticity: Revenue Distribution")
                
                # We use final_amount_inr as the X-axis to see the "spread" of pricing
                fig_scatter = px.scatter(
                    df_rev, 
                    x='final_amount_inr', 
                    y='subcategory',
                    color='is_prime_member',
                    title="Revenue Distribution by Subcategory & Member Type",
                    labels={
                        'final_amount_inr': 'Order Value (₹)', 
                        'subcategory': 'Subcategory',
                        'is_prime_member': 'Prime Member'
                    },
                    color_discrete_map={0: '#232F3E', 1: '#FF9900'},
                    opacity=0.6,
                    template="plotly_white"
                )
                
                # Improve layout for better readability
                fig_scatter.update_layout(
                    height=600,
                    xaxis_title="Transaction Value (INR)",
                    yaxis_title="Product Subcategory"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

                st.divider()

                # 2. PROMOTIONAL EFFECTIVENESS (Existing Prime Stats Logic)
                prime_stats = df_rev.groupby('is_prime_member')['final_amount_inr'].agg(['mean', 'sum', 'count']).reset_index()
                
                # ... [Rest of the Prime KPI and Pie Chart code from the previous step] ...  

                # 2. VISUAL INSIGHT: Comparison Chart
                st.subheader("📊 Spending Behavior Comparison")
                fig_comp = px.bar(
                    prime_stats, 
                    x='is_prime_member', 
                    y='mean',
                    color='is_prime_member',
                    title="Average Spend: Prime vs. Non-Prime",
                    labels={'mean': 'Average Order Value (₹)', 'is_prime_member': 'Is Prime Member?'},
                    color_discrete_map={0: '#232F3E', 1: '#FF9900'}, # Amazon Colors
                    text_auto='.2f'
                )
                # Change X-axis labels from 0/1 to No/Yes
                fig_comp.update_layout(xaxis = dict(tickmode = 'array', tickvals = [0, 1], ticktext = ['Non-Prime', 'Prime']))
                st.plotly_chart(fig_comp, use_container_width=True)

                st.divider()

                # 3. TEXTUAL INSIGHT (The logic you saw earlier)
                if diff_pct > 0:
                    st.success(f"**Insight:** Prime members are your 'Power Users', spending **{diff_pct:.1f}% more** per transaction.")
                    st.info("**Actionable Strategy:** Launch a 'Prime Trial' campaign for high-value Non-Prime customers to lock in this higher spending behavior.")
                else:
                    st.warning("**Insight:** Prime members are spending less. Review if your current Prime discounts are eroding margins too heavily.")

            else:
                st.error("Data missing for Discount Analysis.")
    else:
        st.error("Data connection failed or table is empty.")
# --- ROUTING FOR CUSTOMER ANALYTICS ---
if category == "Customer Analytics":
    if not data_raw.empty:
        df_cust = data_raw.copy()
        df_cust['order_date'] = pd.to_datetime(df_cust['order_date'])
        
        if question == "RFM Segmentation":
            st.header("👤 Advanced Customer Segmentation (RFM)")
            
            # 1. RFM CALCULATION
            snapshot_date = df_cust['order_date'].max()
            rfm = df_cust.groupby('customer_id').agg({
                'order_date': lambda x: (snapshot_date - x.max()).days,
                'customer_id': 'count',
                'final_amount_inr': 'sum'
            }).rename(columns={
                'order_date': 'Recency',
                'customer_id': 'Frequency',
                'final_amount_inr': 'Monetary'
            }).reset_index()

            # 2. SCORING (1 to 5)
            # Lower recency is better (5), higher frequency/monetary is better (5)
            rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
            rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
            rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])
            
            # Create a combined segment logic
            def segment_me(df):
                r, f = int(df['R_Score']), int(df['F_Score'])
                if r >= 4 and f >= 4: return 'Champions'
                if r >= 3 and f >= 3: return 'Loyal Customers'
                if r >= 4 and f < 3: return 'New Customers'
                if r < 3 and f >= 4: return 'At Risk'
                if r <= 2 and f <= 2: return 'Lost'
                return 'Potential Enthusiasts'

            rfm['Segment'] = rfm.apply(segment_me, axis=1)

            # 3. VISUALIZATION: Segment Distribution
            st.subheader("📊 Customer Segment Breakdown")
            seg_counts = rfm['Segment'].value_counts().reset_index()
            
            fig_seg = px.treemap(
                seg_counts, path=['Segment'], values='count',
                color='count', color_continuous_scale='Blues',
                title="Market Share by Customer Segment"
            )
            st.plotly_chart(fig_seg, use_container_width=True)

            st.divider()

            # 4. INTERACTIVE CUSTOMER PROFILES & RECOMMENDATIONS
            st.subheader("🎯 Targeted Marketing Strategy")
            selected_segment = st.selectbox("Select Segment to View Strategy:", rfm['Segment'].unique())
            
            # Recommendation Logic
            recommendations = {
                'Champions': "Offer early access to new products. No discounts needed; focus on VIP loyalty rewards.",
                'Loyal Customers': "Upsell higher-value products. Use personalized 'Thank You' notes.",
                'New Customers': "Provide a 'Second Purchase' discount code. Send a welcome onboarding email.",
                'At Risk': "Send 'We Miss You' emails with a limited-time high-value discount.",
                'Lost': "Don't spend too much on ads here. Try one 'Final Offer' win-back campaign.",
                'Potential Enthusiasts': "Showcase product reviews and social proof to build more trust."
            }
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.info(f"**Strategy for {selected_segment}:**\n\n{recommendations.get(selected_segment)}")
            
            with col2:
                # Show sample profiles for the selected segment
                sample_users = rfm[rfm['Segment'] == selected_segment].head(5)
                st.write(f"**Sample {selected_segment} Profiles:**")
                st.dataframe(sample_users[['customer_id', 'Recency', 'Frequency', 'Monetary']], use_container_width=True)

            # 5. BEHAVIORAL ANALYSIS: Segment Spend
            st.subheader("💰 Revenue Contribution by Segment")
            fig_spend = px.box(rfm, x='Segment', y='Monetary', color='Segment', 
                               title="Spending Distribution per Segment", log_y=True)
            st.plotly_chart(fig_spend, use_container_width=True)
        # --- PAGE: CUSTOMER JOURNEY ANALYTICS (Question 12) ---
        elif question == "Customer Journey":
            st.header("🛣️ Customer Evolution & Journey Mapping")
            
            if not df_cust.empty:
                # 1. ACQUISITION & EVOLUTION: First-Purchase vs. Repeat
                # We identify the first and last purchase for every user
                journey_df = df_cust.sort_values(['customer_id', 'order_date'])
                journey_df['Purchase_Number'] = journey_df.groupby('customer_id').cumcount() + 1
                
                st.subheader("📈 Customer Evolution: First-Time to Loyal")
                evolution = journey_df.groupby('Purchase_Number')['final_amount_inr'].agg(['mean', 'count']).reset_index()
                # Filter for the first 10 purchases to keep the chart clean
                evolution = evolution[evolution['Purchase_Number'] <= 10]
                
                fig_evo = px.line(
                    evolution, x='Purchase_Number', y='mean',
                    title="Average Spend Evolution (Purchase 1 to 10)",
                    markers=True,
                    labels={'mean': 'Avg Spend (₹)', 'Purchase_Number': 'Order Sequence Number'},
                    color_discrete_sequence=['#FF9900']
                )
                st.plotly_chart(fig_evo, use_container_width=True)

                st.divider()

                # 2. CATEGORY TRANSITIONS (Sankey Diagram Logic)
                # Where do they start vs where do they go next?
                st.subheader("🔄 Category Transition Patterns")
                
                # Get the first subcategory and the second subcategory for repeat buyers
                first_purchase = journey_df[journey_df['Purchase_Number'] == 1][['customer_id', 'subcategory']]
                second_purchase = journey_df[journey_df['Purchase_Number'] == 2][['customer_id', 'subcategory']]
                
                transitions = first_purchase.merge(second_purchase, on='customer_id', suffixes=('_First', '_Next'))
                transition_matrix = transitions.groupby(['subcategory_First', 'subcategory_Next']).size().reset_index(name='count')
                
                # For simplicity in Streamlit, we show this as a Heatmap of "Next-Purchase Likelihood"
                fig_trans = px.density_heatmap(
                    transition_matrix.nlargest(20, 'count'),
                    x="subcategory_First", y="subcategory_Next", z="count",
                    title="Path Analysis: What do they buy after their first item?",
                    labels={'subcategory_First': 'Initial Purchase', 'subcategory_Next': 'Follow-up Purchase'},
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig_trans, use_container_width=True)

                st.divider()

                # 3. LOYALTY MILESTONES
                st.subheader("🏆 Loyalty Milestones & Retention")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Conversion to Repeat Buyer
                    total_users = df_cust['customer_id'].nunique()
                    repeat_users = journey_df[journey_df['Purchase_Number'] == 2]['customer_id'].nunique()
                    retention_rate = (repeat_users / total_users) * 100
                    
                    st.metric("Conversion to Repeat Buyer", f"{retention_rate:.1f}%")
                    st.write("This is the percentage of users who moved past their 'First Purchase' barrier.")
                
                with col2:
                    # Average Time to Second Purchase
                    journey_df['Prev_Order_Date'] = journey_df.groupby('customer_id')['order_date'].shift(1)
                    journey_df['Days_Between'] = (journey_df['order_date'] - journey_df['Prev_Order_Date']).dt.days
                    avg_days_to_repeat = journey_df[journey_df['Purchase_Number'] == 2]['Days_Between'].mean()
                    
                    st.metric("Avg Days to 2nd Order", f"{avg_days_to_repeat:.0f} Days")
                    st.write("The critical 'nurture' window for email marketing.")

            else:
                st.error("Journey data requires multiple orders per customer to analyze transitions.")
        # --- PAGE: PRIME MEMBERSHIP ANALYTICS (Question 13) ---
        elif question == "Prime vs Non-Prime":
            st.header("🎗️ Prime vs. Non-Prime Strategic Analysis")
            
            if not df_cust.empty:
                # 1. MEMBERSHIP VALUE ANALYSIS (KPIs)
                prime_df = df_cust[df_cust['is_prime_member'] == 1]
                non_prime_df = df_cust[df_cust['is_prime_member'] == 0]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    prime_aov = prime_df['final_amount_inr'].mean()
                    non_prime_aov = non_prime_df['final_amount_inr'].mean()
                    lift = ((prime_aov - non_prime_aov) / non_prime_aov) * 100
                    st.metric("Prime Avg Order Value", f"₹{prime_aov:,.2f}", delta=f"{lift:.1f}% Lift")
                
                with col2:
                    prime_freq = prime_df.groupby('customer_id').size().mean()
                    st.metric("Prime Purchase Frequency", f"{prime_freq:.2f} orders", help="Avg orders per Prime customer")
                
                with col3:
                    prime_rev_share = (prime_df['final_amount_inr'].sum() / df_cust['final_amount_inr'].sum()) * 100
                    st.metric("Prime Revenue Contribution", f"{prime_rev_share:.1f}%")

                st.divider()

                # 2. BEHAVIORAL ANALYSIS: Category Preference
                st.subheader("📦 Category Affinity: Prime vs. Non-Prime")
                
                # Compare top subcategories for both groups
                p_cat = prime_df['subcategory'].value_counts(normalize=True).head(10).reset_index()
                p_cat['Member_Type'] = 'Prime'
                
                np_cat = non_prime_df['subcategory'].value_counts(normalize=True).head(10).reset_index()
                np_cat['Member_Type'] = 'Non-Prime'
                
                cat_comp = pd.concat([p_cat, np_cat])
                
                fig_cat = px.bar(
                    cat_comp, x='proportion', y='subcategory', color='Member_Type',
                    barmode='group', orientation='h',
                    title="Top 10 Category Distribution (% of total orders)",
                    color_discrete_map={'Prime': '#FF9900', 'Non-Prime': '#232F3E'}
                )
                st.plotly_chart(fig_cat, use_container_width=True)

                st.divider()

                # 3. RETENTION RATES (The "Stickiness" Factor)
                st.subheader("🔗 Membership Retention & Stickiness")
                
                # Calculate % of users with > 1 order
                def get_retention(df):
                    counts = df.groupby('customer_id').size()
                    return (len(counts[counts > 1]) / len(counts)) * 100

                p_retention = get_retention(prime_df)
                np_retention = get_retention(non_prime_df)
                
                fig_ret = px.bar(
                    x=['Non-Prime', 'Prime'], y=[np_retention, p_retention],
                    color=['Non-Prime', 'Prime'],
                    title="Repeat Purchase Rate (%)",
                    labels={'x': 'Membership Status', 'y': 'Repeat Rate %'},
                    color_discrete_map={'Prime': '#FF9900', 'Non-Prime': '#232F3E'},
                    text_auto='.1f'
                )
                st.plotly_chart(fig_ret, use_container_width=True)

                # 4. PRIME-SPECIFIC BUSINESS INSIGHTS
                st.subheader("💡 Strategic Insights")
                if p_retention > np_retention:
                    st.success(f"**Retention Alpha:** Prime members are {(p_retention/np_retention):.1f}x more likely to return than regular customers.")
                    st.info("**Strategy:** Any marketing spend to convert a Non-Prime user to Prime pays for itself via increased lifetime frequency.")
                else:
                    st.warning("Prime retention is currently lower than expected. Investigate if Prime shipping speeds or exclusive deals are meeting expectations.")

            else:
                st.error("Prime data is currently unavailable in the selected dataset.")
        # --- PAGE: CUSTOMER RETENTION & CHURN (Question 14) ---
        elif question == "Retention & Churn":
            st.header("📉 Churn Prediction & Cohort Analysis")
            
            if not df_cust.empty:
                # 1. COHORT ANALYSIS (Retention by Joining Month)
                st.subheader("👥 Monthly Retention Cohorts")
                df_cust['Join_Month'] = df_cust.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
                df_cust['Order_Month'] = df_cust['order_date'].dt.to_period('M')
                
                cohort_data = df_cust.groupby(['Join_Month', 'Order_Month']).agg(n_customers=('customer_id', 'nunique')).reset_index()
                cohort_data['Period_Number'] = (cohort_data['Order_Month'] - cohort_data['Join_Month']).apply(lambda x: x.n)
                
                # Pivot for Heatmap
                cohort_pivot = cohort_data.pivot_table(index='Join_Month', columns='Period_Number', values='n_customers')
                # Calculate percentages
                cohort_size = cohort_pivot.iloc[:, 0]
                retention_matrix = cohort_pivot.divide(cohort_size, axis=0) * 100

                fig_cohort = px.imshow(
                    retention_matrix,
                    labels=dict(x="Months Since Joining", y="Joining Cohort", color="Retention %"),
                    x=retention_matrix.columns,
                    y=retention_matrix.index.astype(str),
                    color_continuous_scale='RdYlGn',
                    text_auto=".1f"
                )
                st.plotly_chart(fig_cohort, use_container_width=True)

                st.divider()

                # 2. CHURN PREDICTION LOGIC (Risk Scoring)
                st.subheader("🚨 Churn Risk Assessment")
                
                # We define churn risk based on Recency vs. Avg Frequency
                snapshot_date = df_cust['order_date'].max()
                churn_df = df_cust.groupby('customer_id').agg({
                    'order_date': lambda x: (snapshot_date - x.max()).days,
                    'customer_id': 'count',
                    'final_amount_inr': 'sum'
                }).rename(columns={'order_date': 'Recency', 'customer_id': 'Frequency', 'final_amount_inr': 'Monetary'}).reset_index()

                # Calculate Avg Time Between Orders per user (simulated)
                avg_gap = 60 # Assume 60 days is the standard Amazon churn window
                churn_df['Churn_Risk_Score'] = (churn_df['Recency'] / avg_gap).clip(0, 1.5) 
                
                def get_risk_label(score):
                    if score > 1.2: return "High Risk (Churned)"
                    if score > 0.8: return "Medium Risk (Warning)"
                    return "Low Risk (Active)"

                churn_df['Risk_Category'] = churn_df['Churn_Risk_Score'].apply(get_risk_label)

                c1, c2 = st.columns([1, 2])
                with c1:
                    risk_counts = churn_df['Risk_Category'].value_counts()
                    fig_risk = px.pie(
                        names=risk_counts.index, values=risk_counts.values,
                        hole=0.5, title="Current Portfolio Risk",
                        color=risk_counts.index,
                        color_discrete_map={
                            "Low Risk (Active)": "#2ECC71",
                            "Medium Risk (Warning)": "#F1C40F",
                            "High Risk (Churned)": "#E74C3C"
                        }
                    )
                    st.plotly_chart(fig_risk, use_container_width=True)

                with c2:
                    st.write("🔍 **High-Value At-Risk Customers**")
                    # Focus on people who spent a lot but haven't been back
                    at_risk_vip = churn_df[churn_df['Risk_Category'] != "Low Risk (Active)"].sort_values('Monetary', ascending=False).head(10)
                    st.dataframe(at_risk_vip[['customer_id', 'Recency', 'Monetary', 'Risk_Category']], use_container_width=True)

                st.divider()

                # 3. RETENTION STRATEGY EFFECTIVENESS
                st.subheader("💡 Lifecycle Management Insights")
                
                st.info("""
                **Recommended Retention Actions:**
                * **For High Risk VIPs:** Trigger manual outreach or a high-value (20%+) 'Win-Back' coupon.
                * **For Medium Risk:** Send a 'New Arrivals' newsletter personalized to their last-bought subcategory.
                * **For Low Risk:** Enroll in 'Subscribe & Save' programs to lock in future recurring revenue.
                """)

            else:
                st.error("Cohort analysis requires a minimum of 3 months of historical data.")
        # --- PAGE: DEMOGRAPHICS & BEHAVIOR (Question 15) ---
        elif question == "Demographics":
            st.header("👥 Demographics & Behavioral Profiling")
            df_rev = data_raw2.copy()
            if not df_rev.empty:
                # 1. BEHAVIORAL SEGMENTATION (Archetype Logic)
                # We infer "Age/Persona" based on what they buy
                def infer_persona(cat):
                    tech_cats = ['Smartphones', 'Laptops', 'Gaming', 'Audio']
                    home_cats = ['Appliances', 'Furniture', 'Kitchen', 'Home Decor']
                    if cat in tech_cats: return 'Tech Enthusiast (Gen Z/Millennial)'
                    if cat in home_cats: return 'Home Maker (Gen X/Boomer)'
                    return 'General Consumer'

                df_rev['Persona'] = df_rev['subcategory'].apply(infer_persona)

                # 2. SPENDING PATTERNS BY PERSONA
                st.subheader("💰 Spending Patterns by Persona")
                persona_spend = df_rev.groupby('Persona')['final_amount_inr'].agg(['mean', 'sum']).reset_index()
                
                fig_persona = px.bar(
                    persona_spend, x='Persona', y='mean',
                    title="Average Order Value by Behavioral Persona",
                    color='Persona',
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    text_auto='.2f'
                )
                st.plotly_chart(fig_persona, use_container_width=True)

                st.divider()

                # 3. GEOGRAPHIC BEHAVIOR (State vs. Persona)
                st.subheader("📍 Geographic Distribution of Personas")
                geo_persona = df_rev.groupby(['customer_state', 'Persona']).size().reset_index(name='Order_Count')
                
                fig_geo_per = px.bar(
                    geo_persona, x='customer_state', y='Order_Count', color='Persona',
                    title="Persona Density per State",
                    barmode='stack'
                )
                st.plotly_chart(fig_geo_per, use_container_width=True)

                st.divider()

                # 4. TARGETED MARKETING OPPORTUNITIES
                st.subheader("🎯 Targeted Marketing Opportunities")
                
                # Logic: Find the most popular subcategory for each persona to recommend ads
                top_offer = df_rev.groupby(['Persona', 'subcategory']).size().reset_index(name='Count')
                top_offer = top_offer.sort_values(['Persona', 'Count'], ascending=[True, False]).groupby('Persona').first().reset_index()

                cols = st.columns(len(top_offer))
                for i, row in top_offer.iterrows():
                    with cols[i]:
                        st.metric(row['Persona'], row['subcategory'])
                        st.write(f"**Recommended Ad:** Focus on '{row['subcategory']}' benefits.")

                st.info("""
                **Strategic Note:** * **Tech Enthusiasts:** High frequency, lower AOV. Use social media (Instagram/YouTube) for marketing.
                * **Home Makers:** Lower frequency, much higher AOV. Use Email/WhatsApp marketing with 'Long-term Warranty' messaging.
                """)

            else:
                st.error("Demographic data requires subcategory and state information to process.")
# --- ROUTING FOR PRODUCT & INVENTORY ---
query_q3 = """
    SELECT 
        transaction_id,          -- Unique ID to count units
        order_date,        -- For lifecycle/recency
        final_amount_inr,  -- For revenue
        subcategory,       -- For grouping
        brand,
        category,          -- For high-level views
        customer_id,        -- For repeat purchase logic
        quantity,
        product_name,
        discounted_price_inr,
        discount_percent,
        return_status,
        delivery_days,is_festival_sale,
        product_rating
                FROM public.maintable
    WHERE order_year >= (SELECT MAX(order_year) - 5 FROM public.maintable)
"""
df_prod = fetch_data(query_q3)
if category == "Product & Inventory":
# --- PAGE: PRODUCT PERFORMANCE (Question 16) ---
    if question == "Product Performance":
        st.header("📦 Product Performance & Lifecycle Tracking")
        
        if not df_prod.empty:
            # 1. AGGREGATE PERFORMANCE METRICS
            # We group by subcategory and calculate totals
            prod_metrics = df_prod.groupby('subcategory').agg({
                'final_amount_inr': 'sum',
                'transaction_id': 'count',  # Number of unique orders
                'quantity': 'sum',          # Total physical units sold
                'product_rating': 'mean'    # Average customer satisfaction
            }).rename(columns={
                'final_amount_inr': 'Total Revenue',
                'transaction_id': 'Order Count',
                'quantity': 'Total Units Sold',
                'product_rating': 'Avg Rating'
            }).reset_index()

            # 2. BRAND PERFORMANCE (Top 10)
            st.subheader("🏭 Top Performing Brands")
            brand_data = df_prod.groupby('brand')['final_amount_inr'].sum().nlargest(10).reset_index()
            fig_brand = px.bar(
                brand_data, x='final_amount_inr', y='brand',
                orientation='h', title="Top 10 Brands by Revenue (₹)",
                color='final_amount_inr', color_continuous_scale='Blues',
                text_auto='.2s'
            )
            fig_brand.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_brand, use_container_width=True)

            st.divider()

            # 3. TOP RANKINGS: REVENUE VS. UNITS
            st.subheader("🏆 Category Leaderboard")
            c1, c2 = st.columns(2)
            
            with c1:
                fig_rev = px.bar(
                    prod_metrics.nlargest(10, 'Total Revenue'),
                    x='Total Revenue', y='subcategory',
                    orientation='h', title="Top 10 by Revenue (₹)",
                    color='Total Revenue', color_continuous_scale='Viridis'
                )
                fig_rev.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_rev, use_container_width=True)

            with c2:
                fig_qty = px.bar(
                    prod_metrics.nlargest(10, 'Total Units Sold'),
                    x='Total Units Sold', y='subcategory',
                    orientation='h', title="Top 10 by Units Sold",
                    color='Total Units Sold', color_continuous_scale='Cividis'
                )
                fig_qty.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_qty, use_container_width=True)

            st.divider()

            # 4. LIFECYCLE TRACKING (Volume vs. Rating)
            st.subheader("⏳ Product Maturity Matrix")
            # Logic: We define status based on high/low revenue and rating
            avg_rev = prod_metrics['Total Revenue'].median()
            
            def get_status(row):
                if row['Total Revenue'] > avg_rev and row['Avg Rating'] >= 4.0:
                    return 'Star (High Value & Quality)'
                if row['Total Revenue'] > avg_rev:
                    return 'Cash Cow (High Value)'
                if row['Avg Rating'] < 3.5:
                    return 'Underperformer (Quality Issue)'
                return 'Niche / Emerging'

            prod_metrics['Status'] = prod_metrics.apply(get_status, axis=1)

            fig_matrix = px.scatter(
                prod_metrics, x='Total Units Sold', y='Total Revenue',
                size='Total Revenue', color='Status',
                hover_name='subcategory',
                title="Maturity: Volume vs. Value Distribution",
                color_discrete_map={
                    'Star (High Value & Quality)': '#FF9900', # Amazon Orange
                    'Cash Cow (High Value)': '#232F3E',        # Amazon Navy
                    'Underperformer (Quality Issue)': '#E74C3C', # Red
                    'Niche / Emerging': '#95A5A6'              # Grey
                }
            )
            st.plotly_chart(fig_matrix, use_container_width=True)

            # 5. DATA TABLE
            st.subheader("📋 Performance Audit Table")
            st.dataframe(
                prod_metrics.sort_values('Total Revenue', ascending=False).style.format({
                    'Total Revenue': '₹{:,.0f}',
                    'Avg Rating': '{:.1f} ⭐'
                }), 
                use_container_width=True
            )

        else:
            st.error("No data found. Ensure 'transaction_id' is included in your query.")
# --- PAGE: INVENTORY TURNOVER (Question 17) ---
    elif question == "Inventory Turnover":
        st.header("📉 Inventory Turnover & Sales Velocity")
            
        if not df_prod.empty:
        # 1. SALES VELOCITY (Units Sold Per Day)
            st.subheader("⚡ Sales Velocity Analysis")
            df_prod['order_date'] = pd.to_datetime(df_prod['order_date'])
                
            # Calculate the time window of the dataset
            days_in_dataset = (df_prod['order_date'].max() - df_prod['order_date'].min()).days or 1
                
            # Group by subcategory to see how many units move daily
            velocity_df = df_prod.groupby('subcategory').agg({
                    'quantity': 'sum',
                    'transaction_id': 'nunique'
                }).reset_index()
                
            velocity_df['Daily_Velocity'] = velocity_df['quantity'] / days_in_dataset
                
            fig_vel = px.bar(
                    velocity_df.nlargest(15, 'Daily_Velocity'),
                    x='subcategory', y='Daily_Velocity',
                    title="Average Units Sold Per Day",
                    color='Daily_Velocity', color_continuous_scale='YlGnBu',
                    labels={'Daily_Velocity': 'Avg Units/Day'},
                    text_auto='.2f'
                )
            st.plotly_chart(fig_vel, use_container_width=True)

            st.divider()

                # 2. INVENTORY TURNOVER RATIO (Simulated)
                # Turnover = Sales / Average Inventory
                # Since we don't have "Average Inventory" in a transaction table, 
                # we simulate it as 15% of total units sold to show the logic.
            st.subheader("🔄 Inventory Turnover Ratio")
            velocity_df['Avg_Inventory'] = velocity_df['quantity'] * 0.15 
            velocity_df['Turnover_Ratio'] = velocity_df['quantity'] / velocity_df['Avg_Inventory']
                
            c1, c2 = st.columns(2)
            with c1:
                # High Turnover (Fast Moving)
                st.write("🚀 **Fastest Moving Categories**")
                st.table(velocity_df.nlargest(5, 'Turnover_Ratio')[['subcategory', 'Turnover_Ratio']])
                
            with c2:
                # Low Turnover (Potential Dead Stock)
                st.write("🧊 **Slowest Moving Categories**")
                st.table(velocity_df.nsmallest(5, 'Turnover_Ratio')[['subcategory', 'Turnover_Ratio']])

            st.divider()

                # 3. STOCKOUT RISK (Run-out Date Prediction)
            st.subheader("⚠️ Stockout Risk Warning")
                
                # Assume a fixed current stock for the simulation
            velocity_df['Current_Stock'] = 150 
            velocity_df['Days_Until_Stockout'] = velocity_df['Current_Stock'] / velocity_df['Daily_Velocity']
                
                # Filter for products running out in less than 30 days
            risk_df = velocity_df[velocity_df['Days_Until_Stockout'] < 30].sort_values('Days_Until_Stockout')
                
            if not risk_df.empty:
                fig_risk = px.scatter(
                        risk_df, x='Days_Until_Stockout', y='subcategory',
                        size='Daily_Velocity', color='Days_Until_Stockout',
                        color_continuous_scale='Reds_r',
                        title="Urgent: Days of Supply Remaining",
                        labels={'Days_Until_Stockout': 'Days Left'}
                    )
                st.plotly_chart(fig_risk, use_container_width=True)
                st.error(f"Alert: {len(risk_df)} categories are projected to go out of stock within 30 days.")
            else:
                st.success("All categories have sufficient stock levels based on current velocity.")
# --- PAGE: Stockout Analysis (Question 18) ---
    elif question == "Stockout Analysis": 
        st.header("⚖️ Inventory Optimization & Demand Planning")
                
        if not df_prod.empty:
            # --- 1. AUTO-GENERATING MONTH (The Safety Fix) ---
            # We convert to datetime and create consistent columns
            df_prod['order_date'] = pd.to_datetime(df_prod['order_date'])
            df_prod['quantity'] = pd.to_numeric(df_prod['quantity'], errors='coerce')
            df_prod['delivery_days'] = pd.to_numeric(df_prod['delivery_days'], errors='coerce')

            df_prod['Month_name'] = df_prod['order_date'].dt.strftime('%b') # Added quotes here
            df_prod['Month_num'] = df_prod['order_date'].dt.month

            # 2. SEASONAL DEMAND PATTERNS
            st.subheader("📅 Seasonal Demand Fluctuations")
            
            # FIX: Group by 'Month_num' and 'Month_name' instead of 'order_month'
            monthly_demand = df_prod.groupby(['Month_num', 'Month_name'])['quantity'].sum().reset_index()
            monthly_demand = monthly_demand.sort_values('Month_num') # Ensures Jan -> Dec order
                    
            fig_season = px.line(
                monthly_demand, x='Month_name', y='quantity',
                title="Monthly Unit Demand (Seasonality Trends)",
                markers=True, line_shape="spline",
                color_discrete_sequence=['#FF9900'] # Amazon Orange
            )
            st.plotly_chart(fig_season, use_container_width=True)

            st.divider()
                
            # 3. FESTIVAL SALE IMPACT
            st.subheader("🎉 Festival vs. Non-Festival Demand")
            if 'is_festival_sale' in df_prod.columns:
                fest_comp = df_prod.groupby('is_festival_sale')['quantity'].mean().reset_index()
                # Ensure mapping handles numeric 1/0 or boolean
                fest_comp['is_festival_sale'] = fest_comp['is_festival_sale'].astype(int).map({1: 'Festival Sale', 0: 'Normal Day'})
                        
                fig_fest = px.bar(
                    fest_comp, x='is_festival_sale', y='quantity',
                    title="Avg Units Sold: Normal vs. Festival Days",
                    color='is_festival_sale',
                    color_discrete_map={'Festival Sale': '#FF9900', 'Normal Day': '#232F3E'}
                )
                st.plotly_chart(fig_fest, use_container_width=True)
                    
            st.divider()

            # 4. DEMAND FORECASTING (Safety Stock & Reorder Points)
            st.subheader("🛡️ Safety Stock & Reorder Points")
            # Logic: We use the Reorder Point (ROP) Formula
            # ROP = (Average Daily Demand * Lead Time) + Safety Stock
            planning = df_prod.groupby('subcategory').agg({
                'quantity': ['mean', 'std'],
                'delivery_days': 'mean' 
            })
            planning.columns = ['avg_daily', 'std_dev', 'avg_lead_time']
            planning = planning.reset_index()
            # Safety Stock calculation (Z-score 1.65 for 95% service level)
            planning['std_dev'] = planning['std_dev'].fillna(0)
            planning['Safety_Stock'] = planning['std_dev'] * 1.65 * (planning['avg_lead_time']**0.5)
            planning['Reorder_Point'] = (planning['avg_daily'] * planning['avg_lead_time']) + planning['Safety_Stock']
            
            st.write("📊 **Inventory Procurement & Planning Table**")
            st.dataframe(
                planning[['subcategory', 'avg_daily', 'avg_lead_time', 'Safety_Stock', 'Reorder_Point']].style.format({
                    'avg_daily': '{:.2f}',
                    'avg_lead_time': '{:.1f} days',
                    'Safety_Stock': '{:.0f} units',
                    'Reorder_Point': '{:.0f} units'
                }), use_container_width=True
            )

            st.info("""
            **Inventory Management Guide:**
            - **Reorder Point (ROP):** When your physical stock hits this number, it's time to reorder.
            - **Safety Stock:** This is your 'Buffer' to handle unexpected spikes in customer demand.
            """)

        else:
            st.error("Data table is empty. Please check your SQL query and database connection.")
# --- PAGE: PRODUCT RATING & REVIEWS (Question 19) ---
    elif question == "Supplier Performance": # Using your sidebar label for Q19
        st.header("⭐ Product Rating & Quality Analytics")
                
        if not df_prod.empty:
            # 1. DATA CLEANING
            # Ensure ratings are numeric and handle return status
            df_prod['product_rating'] = pd.to_numeric(df_prod['product_rating'], errors='coerce')
            df_prod['final_amount_inr'] = pd.to_numeric(df_prod['final_amount_inr'], errors='coerce')
            
            # 2. RATING DISTRIBUTION (The "Sentiment" Pulse)
            st.subheader("📊 Global Rating Distribution")
            rating_dist = df_prod['product_rating'].value_counts().reset_index()
            rating_dist.columns = ['Rating', 'Count']
            
            fig_dist = px.bar(
                rating_dist.sort_values('Rating'), 
                x='Rating', y='Count',
                title="Frequency of Star Ratings",
                color='Rating', color_continuous_scale='RdYlGn',
                text_auto=True
            )
            st.plotly_chart(fig_dist, use_container_width=True)

            st.divider()

            # 3. CORRELATION: RATINGS VS. SALES
            st.subheader("💰 Does Quality Drive Revenue?")
            # Grouping by subcategory to see if higher rated categories make more money
            quality_corr = df_prod.groupby('subcategory').agg({
                'product_rating': 'mean',
                'final_amount_inr': 'sum',
                'transaction_id': 'count'
            }).reset_index()
            
            fig_corr = px.scatter(
                quality_corr, x='product_rating', y='final_amount_inr',
                size='transaction_id', color='subcategory',
                hover_name='subcategory',
                title="Revenue vs. Average Rating (Bubble Size = Order Volume)",
                labels={'product_rating': 'Avg Star Rating', 'final_amount_inr': 'Total Revenue (₹)'},
                trendline="ols" # Adds a trendline to show the correlation
            )
            st.plotly_chart(fig_corr, use_container_width=True)

            st.divider()

            # 4. RETURN ANALYSIS (Quality Risk)
            # 4. RETURN ANALYSIS (Quality Risk)
        st.subheader("🔄 Return Rate by Category")
        
        if 'return_status' in df_prod.columns:
            # --- DEBUG CHECK (Removable once fixed) ---
            # st.write("Debug: Unique values in return_status:", df_prod['return_status'].unique())
            
            # --- FLEXIBLE LOGIC ---
            # This captures 'Returned', 'True', '1', 'yes', or any string containing 'return'
            def check_return(val):
                v = str(val).strip().lower()
                if v in ['1', '1.0', 'true', 'yes', 'returned', 'y']:
                    return 1
                if 'return' in v: # Catches "Returned to seller" etc.
                    return 1
                return 0

            df_prod['is_returned'] = df_prod['return_status'].apply(check_return)
            
            # Aggregate
            return_stats = df_prod.groupby('subcategory').agg({
                'is_returned': ['sum', 'count'],
                'product_rating': 'mean'
            }).reset_index()
            
            # Flatten columns from aggregation
            return_stats.columns = ['subcategory', 'returns', 'total_orders', 'avg_rating']
            
            # Calculate Rate
            return_stats['Return_Rate'] = (return_stats['returns'] / return_stats['total_orders']) * 100
            
            # Only show categories that actually have orders
            return_stats = return_stats[return_stats['total_orders'] > 0]

            if return_stats['returns'].sum() > 0:
                fig_return = px.bar(
                    return_stats.nlargest(10, 'Return_Rate'),
                    x='Return_Rate', y='subcategory',
                    orientation='h', 
                    title="Top 10 High-Return Categories (%)",
                    color='Return_Rate', 
                    color_continuous_scale='Reds',
                    text_auto='.1f',
                    labels={'Return_Rate': 'Return Percentage (%)'}
                )
                fig_return.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_return, use_container_width=True)
                
                st.warning("💡 **Insight:** High return rates often correlate with low ratings. Investigate these categories for quality issues.")
            else:
                st.info("ℹ️ No returns detected in the current dataset based on the 'return_status' column.")
        else:
            st.error("❌ The column 'return_status' was not found in the dataframe.")
            # 5. PRODUCT LEADERBOARD
        st.subheader("🏆 Top Rated Products (Hero Items)")
        # Filter for products with at least 5 sales to avoid "one-hit wonder" 5-star ratings
        leaderboard = df_prod.groupby('product_name').agg({
                'product_rating': 'mean',
                'transaction_id': 'count'
            }).rename(columns={'transaction_id': 'Total_Orders', 'product_rating': 'Avg_Rating'})
            
        top_heroes = leaderboard[leaderboard['Total_Orders'] > 5].nlargest(10, 'Avg_Rating')
        st.table(top_heroes)

    # --- PAGE: PRICING STRATEGY (Question 20) ---
    elif question == "Pricing Strategy": # Button Name for Q20
        st.header("🚀 New Product Launch & Pricing Strategy")
                
        if not df_prod.empty:
            # 1. DATA PREP: Identify "New" Products
            # We define a 'New Launch' as any product whose first sale was in the last 180 days
            df_prod['order_date'] = pd.to_datetime(df_prod['order_date'])
            launch_dates = df_prod.groupby('product_name')['order_date'].min().reset_index()
            launch_dates.columns = ['product_name', 'launch_date']
            
            # Merge launch date back to main dataframe
            df_launch = df_prod.merge(launch_dates, on='product_name')
            
            # Filter for products launched in the last 6 months of the dataset
            max_date = df_prod['order_date'].max()
            df_new = df_launch[df_launch['launch_date'] >= (max_date - pd.Timedelta(days=180))]

            if not df_new.empty:
                # 2. MARKET ACCEPTANCE (Launch Velocity)
                st.subheader("📈 Launch Velocity (Units Sold since Launch)")
                launch_velocity = df_new.groupby('product_name').agg({
                    'quantity': 'sum',
                    'final_amount_inr': 'sum',
                    'discount_percent': 'mean'
                }).nlargest(10, 'quantity').reset_index()

                fig_launch = px.bar(
                    launch_velocity, x='quantity', y='product_name',
                    orientation='h', title="Top 10 New Launches by Volume",
                    color='discount_percent', color_continuous_scale='Oranges',
                    labels={'discount_percent': 'Avg Discount %', 'quantity': 'Units Sold'}
                )
                fig_launch.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_launch, use_container_width=True)

                st.divider()

                # 3. PRICING SENSITIVITY (Discount vs. Volume)
                st.subheader("💸 Discount Impact on Market Acceptance")
                # Analyze if higher discounts lead to faster adoption for new products
                fig_price = px.scatter(
                    df_new, x='discount_percent', y='quantity',
                    size='final_amount_inr', color='category',
                    hover_name='product_name',
                    title="Price Elasticity: Does a 10% extra discount drive 2x sales?",
                    trendline="ols"
                )
                st.plotly_chart(fig_price, use_container_width=True)

                st.divider()

                # 4. SUCCESS METRICS (KPI Scorecard)
                st.subheader("🎯 Launch Success Scorecard")
                k1, k2, k3 = st.columns(3)
                
                with k1:
                    avg_disc = df_new['discount_percent'].mean()
                    st.metric("Avg Launch Discount", f"{avg_disc:.1f}%")
                
                with k2:
                    total_new_rev = df_new['final_amount_inr'].sum()
                    st.metric("Total New Product Revenue", f"₹{total_new_rev:,.0f}")

                with k3:
                    success_rate = (df_new.groupby('product_name')['product_rating'].mean() >= 4.0).mean() * 100
                    st.metric("High-Quality Launch Rate", f"{success_rate:.1f}%", help="% of new products with >4 star rating")

                # 5. COMPETITIVE PRICING POSITIONING
                st.subheader("🏷️ Brand Pricing Positioning")
                # Comparing how different brands price their new items
                brand_price = df_new.groupby('brand')['discounted_price_inr'].mean().reset_index()
                fig_brand_price = px.box(
                    df_new, x='brand', y='discounted_price_inr',
                    title="Price Range Distribution by Brand (New Launches)",
                    color='brand'
                )
                st.plotly_chart(fig_brand_price, use_container_width=True)

            else:
                st.info("No 'New' products (launched in the last 180 days) found in the dataset.")
                st.write("Displaying all-time pricing strategy instead:")
                # Fallback to general pricing analysis
                fig_all_price = px.histogram(df_prod, x="discount_percent", nbins=20, 
                                            title="Global Discount Distribution", color_discrete_sequence=['#232F3E'])
                st.plotly_chart(fig_all_price, use_container_width=True)

        else:
            st.error("Data table is empty. Check your SQL query.")
query_ops = """
    SELECT 
        transaction_id, 
        order_date,
        customer_id,
        payment_method,
        return_status,
        delivery_charges,
        product_rating,
        customer_tier,
        brand,
        customer_rating, 
        delivery_days,      -- Actual days taken
        delivery_type,      -- Standard, Express, etc.
        customer_city,      -- Geographic analysis
        customer_state,     -- Geographic analysis
        is_prime_member,    -- For Prime vs. Non-Prime speed benchmarks
        final_amount_inr,   -- To see if expensive orders get faster shipping
        subcategory         -- To see if certain products (e.g., bulky) take longer
    FROM public.maintable
    WHERE order_year >= (SELECT MAX(order_year) - 2 FROM public.maintable)
"""
df_ops = fetch_data(query_ops)
# --- PAGE: FULFILLMENT EFFICIENCY (Question 21) ---
if question == "Fulfillment Efficiency":
    st.header("🚚 Delivery Performance & Fulfillment Efficiency")
    
    if not df_ops.empty:
        # 1. DATA PREP: Ensure numeric types
        df_ops['delivery_days'] = pd.to_numeric(df_ops['delivery_days'], errors='coerce')
        
        # Define a benchmark: Let's assume > 5 days is "Delayed"
        benchmark = 5
        df_ops['Status'] = df_ops['delivery_days'].apply(lambda x: 'On-Time' if x <= benchmark else 'Delayed')

        # 2. KEY METRICS (KPIs)
        k1, k2, k3 = st.columns(3)
        with k1:
            avg_days = df_ops['delivery_days'].mean()
            st.metric("Avg. Delivery Time", f"{avg_days:.1f} Days")
        with k2:
            on_time_rate = (df_ops['Status'] == 'On-Time').mean() * 100
            st.metric("On-Time Delivery Rate", f"{on_time_rate:.1f}%")
        with k3:
            fastest_mode = df_ops.groupby('delivery_type')['delivery_days'].mean().idxmin()
            st.metric("Most Efficient Mode", fastest_mode)

        st.divider()

        # 3. GEOGRAPHIC PERFORMANCE (Heatmap)
        st.subheader("📍 Delivery Speed by State")
        geo_perf = df_ops.groupby('customer_state')['delivery_days'].mean().reset_index()
        
        fig_geo = px.choropleth(
            geo_perf,
            # Note: For India map, you'd usually need a GeoJSON, 
            # but a bar chart is a safer fallback for standard Streamlit
            locations='customer_state', locationmode='USA-states', # Placeholder logic
            color='delivery_days',
            title="Avg Delivery Days by Region (Heatmap)",
            color_continuous_scale='RdYlGn_r'
        )
        # Fallback to Bar Chart if GeoJSON isn't configured
        fig_bar_geo = px.bar(geo_perf.sort_values('delivery_days'), 
                             x='delivery_days', y='customer_state', 
                             orientation='h', title="Avg Delivery Days by State",
                             color='delivery_days', color_continuous_scale='RdYlGn_r')
        st.plotly_chart(fig_bar_geo, use_container_width=True)

        st.divider()

        # 4. DELIVERY TYPE ANALYSIS
        st.subheader("⚡ Speed vs. Shipping Method")
        fig_type = px.box(
            df_ops, x='delivery_type', y='delivery_days',
            color='is_prime_member',
            title="Delivery Days Distribution: Prime vs. Non-Prime",
            points="all"
        )
        st.plotly_chart(fig_type, use_container_width=True)

        # 5. DATA TABLE FOR BOTTLENECKS
        st.subheader("🚩 Operational Bottleneck Audit")
        bottlenecks = df_ops[df_ops['delivery_days'] > benchmark].groupby('subcategory').size().reset_index(name='Delay_Count')
        st.write("Subcategories with the most frequent delays:")
        st.dataframe(bottlenecks.sort_values('Delay_Count', ascending=False), use_container_width=True)

    else:
        st.error("Operations data could not be loaded. Check your column names.")
# --- PAGE: PAYMENT ANALYTICS (Question 22) ---
elif question == "Payment Analytics": # Sidebar label for Q22
    st.header("💳 Payment Analytics & Financial Insights")
    
    if not df_ops.empty:
        # 1. PAYMENT METHOD PREFERENCES
        st.subheader("🏦 Popular Payment Methods")
        pay_dist = df_ops.groupby('payment_method').agg({
            'transaction_id': 'count',
            'final_amount_inr': 'sum'
        }).reset_index()
        pay_dist.columns = ['Method', 'Transaction_Count', 'Total_Revenue']

        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(
                pay_dist, names='Method', values='Transaction_Count',
                title="Transaction Volume by Method",
                hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            fig_rev = px.bar(
                pay_dist.sort_values('Total_Revenue'), 
                x='Total_Revenue', y='Method',
                orientation='h', title="Revenue by Payment Method (₹)",
                color='Total_Revenue', color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()

        # 2. PAYMENT TRENDS EVOLUTION
        st.subheader("📈 Payment Method Adoption Over Time")
        # Ensure dates are correct for time-series
        df_ops['order_date'] = pd.to_datetime(df_ops['order_date'])
        df_ops['Month_Year'] = df_ops['order_date'].dt.to_period('M').astype(str)
        
        trend_data = df_ops.groupby(['Month_Year', 'payment_method']).size().reset_index(name='Count')
        
        fig_trend = px.line(
            trend_data, x='Month_Year', y='Count', color='payment_method',
            title="Monthly Growth of Payment Methods",
            markers=True, line_shape="spline"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        st.divider()

        # 3. FINANCIAL PARTNERSHIP INSIGHTS (Ticket Size Analysis)
        st.subheader("🔍 Average Transaction Value (ATV) by Method")
        # This helps identify which partners (e.g., Credit Cards) handle high-value sales
        atv_data = df_ops.groupby('payment_method')['final_amount_inr'].mean().reset_index()
        atv_data.columns = ['Method', 'Avg_Ticket_Size']
        
        fig_atv = px.strip(
            df_ops, x='payment_method', y='final_amount_inr',
            color='payment_method', title="Transaction Value Spread per Method",
            labels={'final_amount_inr': 'Order Value (₹)'}
        )
        st.plotly_chart(fig_atv, use_container_width=True)

        # 4. KPI SUMMARY
        st.subheader("📊 Partnership KPI Summary")
        top_method = pay_dist.loc[pay_dist['Transaction_Count'].idxmax(), 'Method']
        highest_val_method = atv_data.loc[atv_data['Avg_Ticket_Size'].idxmax(), 'Method']
        
        k1, k2 = st.columns(2)
        k1.info(f"🏆 **Most Popular:** {top_method} drives the highest volume of orders.")
        k2.success(f"💎 **High Value:** {highest_val_method} has the highest average order value.")

    else:
        st.error("No payment data available in the current selection.")
# --- PAGE: RETURNS ANALYSIS (Question 23) ---
elif question == "Returns Analysis": # Sidebar label for Q23
    st.header("🔄 Returns & Cancellations: Revenue Leakage Analysis")
    
    if not df_ops.empty:
        # 1. DATA PREP: Identify Return/Cancellation Events
        # We normalize the column to identify 'Failure' cases
        def classify_status(val):
            v = str(val).strip().lower()
            if v in ['returned', '1', '1.0', 'yes']: return 'Returned'
            if v in ['cancelled', 'canceled']: return 'Cancelled'
            return 'Successful'

        df_ops['Order_Result'] = df_ops['return_status'].apply(classify_status)
        
        # 2. FINANCIAL IMPACT (The "Cost of Failure")
        # Leakage = Revenue Lost + Shipping Costs Wasted
        leakage_df = df_ops[df_ops['Order_Result'] != 'Successful']
        total_leakage = leakage_df['final_amount_inr'].sum() + leakage_df['delivery_charges'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue Leakage", f"₹{total_leakage:,.0f}", delta="- Profit Impact", delta_color="inverse")
        c2.metric("Return Rate", f"{(df_ops['Order_Result'] == 'Returned').mean()*100:.1f}%")
        c3.metric("Cancellation Rate", f"{(df_ops['Order_Result'] == 'Cancelled').mean()*100:.1f}%")

        st.divider()

        # 3. CATEGORY-WISE BREAKDOWN
        st.subheader("📁 High-Risk Categories (Return Rate %)")
        cat_returns = df_ops.groupby('subcategory').agg({
            'transaction_id': 'count',
            'Order_Result': lambda x: (x == 'Returned').sum()
        }).reset_index()
        cat_returns['Return_Rate'] = (cat_returns['Order_Result'] / cat_returns['transaction_id']) * 100
        
        fig_cat = px.bar(
            cat_returns.nlargest(10, 'Return_Rate'),
            x='Return_Rate', y='subcategory',
            orientation='h', title="Top 10 Categories by Return Rate",
            color='Return_Rate', color_continuous_scale='Reds',
            text_auto='.1f'
        )
        fig_cat.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_cat, use_container_width=True)

        st.divider()

        # 4. QUALITY IMPROVEMENT OPPORTUNITIES (Correlation)
        st.subheader("📉 Volume vs. Return Rate Matrix")
        # High Volume + High Return Rate = CRITICAL Quality Issue
        fig_matrix = px.scatter(
            cat_returns, x='transaction_id', y='Return_Rate',
            size='transaction_id', hover_name='subcategory',
            title="Identifying Systematic Quality Issues",
            labels={'transaction_id': 'Total Orders', 'Return_Rate': 'Return %'},
            color='Return_Rate', color_continuous_scale='Portland'
        )
        # Add a benchmark line at 10% return rate
        fig_matrix.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="Critical Threshold")
        st.plotly_chart(fig_matrix, use_container_width=True)

        # 5. ACTIONABLE INSIGHTS
        st.info("""
        **🔍 Operational Strategy:**
        * **Top-Left (Low Volume, High Return):** Likely niche products with poor descriptions.
        * **Bottom-Right (High Volume, Low Return):** Your most stable 'Cash Cow' categories.
        * **Top-Right (High Volume, High Return):** **CRITICAL RISK.** These categories are destroying margins. Check for manufacturing defects or sizing issues immediately.
        """)
        

    else:
        st.error("Operations data could not be loaded. Please check your SQL connection.")
# --- PAGE: CUSTOMER SERVICE DASHBOARD (Question 24) ---
elif question == "Warehouse Utilization": # Sidebar label for Q24
    st.header("🎧 Customer Service & Satisfaction (CSAT) Tracking")
    
    if not df_ops.empty:
        # 1. DATA PREP: Metrics & Classification
        # Convert columns to numeric, turning errors into 'NaN' (Not a Number)
        df_ops['delivery_days'] = pd.to_numeric(df_ops['delivery_days'], errors='coerce')
        df_ops['customer_rating'] = pd.to_numeric(df_ops['customer_rating'], errors='coerce')

        # Fill any missing values with 0 so the math doesn't break
        df_ops['delivery_days'] = df_ops['delivery_days'].fillna(0)
        df_ops['customer_rating'] = df_ops['customer_rating'].fillna(0)
        # --- CRITICAL FIX END ---
        # Now the rest of your code will work perfectly
        avg_csat = df_ops['customer_rating'].mean()
        
        # Classifying Sentiment based on Rating
        def classify_sentiment(score):
            if score >= 4: return 'Promoter (Happy)'
            if score == 3: return 'Passive'
            return 'Detractor (Unhappy)'
        
        df_ops['Sentiment'] = df_ops['customer_rating'].apply(classify_sentiment)

        # 2. EXECUTIVE SCORECARD
        avg_csat = df_ops['customer_rating'].mean()
        promoter_count = (df_ops['Sentiment'] == 'Promoter (Happy)').sum()
        total_resp = len(df_ops)
        nps_proxy = (promoter_count / total_resp) * 100

        k1, k2, k3 = st.columns(3)
        k1.metric("Average CSAT Score", f"{avg_csat:.2f} ⭐")
        k2.metric("Promoter % (NPS Proxy)", f"{nps_proxy:.1f}%")
        k3.metric("Avg Resolution (Delivery)", f"{df_ops['delivery_days'].mean():.1f} Days")

        st.divider()

        # 3. COMPLAINT CATEGORIES (Based on Returns)
        st.subheader("⚠️ Complaint Categories (by Subcategory Returns)")
        # We assume every 'Returned' status represents a service interaction/complaint
        complaints = df_ops[df_ops['return_status'].isin(['Returned', '1', 1])].groupby('subcategory').size().reset_index(name='Complaint_Volume')
        
        fig_complaints = px.bar(
            complaints.nlargest(10, 'Complaint_Volume'),
            x='Complaint_Volume', y='subcategory',
            orientation='h', title="Top 10 Categories by Complaint Volume",
            color='Complaint_Volume', color_continuous_scale='Reds'
        )
        fig_complaints.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_complaints, use_container_width=True)

        st.divider()

        # 4. SATISFACTION VS. DELIVERY TIME (Resolution Correlation)
        st.subheader("⏱️ Speed vs. Satisfaction Analysis")
        # Does faster delivery (resolution) lead to higher ratings?
        speed_sat = df_ops.groupby('delivery_days')['customer_rating'].mean().reset_index()
        
        fig_speed = px.scatter(
            speed_sat, x='delivery_days', y='customer_rating',
            trendline="ols", title="Impact of Delivery Speed on Customer Rating",
            labels={'delivery_days': 'Days to Deliver', 'customer_rating': 'Avg Rating'},
            color_discrete_sequence=['#FF9900']
        )
        st.plotly_chart(fig_speed, use_container_width=True)

        # 5. SERVICE QUALITY BY CUSTOMER TIER
        st.subheader("💎 Service Quality by Customer Tier")
        fig_tier = px.box(
            df_ops, x='customer_tier', y='customer_rating',
            color='customer_tier', title="Rating Distribution by Membership Level"
        )
        st.plotly_chart(fig_tier, use_container_width=True)

        st.info("""
        **💡 Service Insight:** If the trendline in 'Speed vs. Satisfaction' is steep, it means your customers value **delivery speed** over everything else. Improving your 'Last-Mile Delivery' will be the fastest way to raise your CSAT scores.
        """)

    else:
        st.error("No customer service data available.")
# --- PAGE: SUPPLY CHAIN & VENDOR INSIGHTS (Question 25) ---
elif question == "Last-Mile Delivery": # Sidebar label for Q25
    st.header("📦 Supply Chain & Vendor Performance Audit")
    
    if not df_ops.empty:
        # 1. DATA CLEANING
        cols = ['delivery_days', 'delivery_charges', 'product_rating', 'final_amount_inr']
        for col in cols:
            df_ops[col] = pd.to_numeric(df_ops[col], errors='coerce').fillna(0)

        # 2. VENDOR RELIABILITY SCORECARD
        st.subheader("🥇 Top Performing Vendors (Brands)")
        # A good vendor has Low Delivery Days and High Product Ratings
        vendor_stats = df_ops.groupby('brand').agg({
            'delivery_days': 'mean',
            'product_rating': 'mean',
            'transaction_id': 'count',
            'delivery_charges': 'sum'
        }).reset_index()
        
        vendor_stats.columns = ['Brand', 'Avg_Lead_Time', 'Avg_Quality_Rating', 'Order_Volume', 'Total_Logistics_Cost']
        # Add this line to make the table appear in your dashboard!
        st.dataframe(vendor_stats.sort_values('Avg_Quality_Rating', ascending=False), use_container_width=True)

        # 3. VENDOR EFFICIENCY MATRIX
        st.subheader("📉 Logistics Cost vs. Lead Time")
        # Identifying "Expensive & Slow" vs "Cheap & Fast" vendors
        fig_vendor = px.scatter(
            vendor_stats, x='Avg_Lead_Time', y='Total_Logistics_Cost',
            size='Order_Volume', color='Avg_Quality_Rating',
            hover_name='Brand', title="Vendor Performance: Lead Time vs. Shipping Cost",
            color_continuous_scale='RdYlGn',
            labels={'Avg_Lead_Time': 'Avg Delivery Days', 'Total_Logistics_Cost': 'Total Shipping Spent (₹)'}
        )
        # Add a reference line for average delivery speed
        fig_vendor.add_vline(x=vendor_stats['Avg_Lead_Time'].mean(), line_dash="dot", line_color="gray")
        st.plotly_chart(fig_vendor, use_container_width=True)

        st.divider()

        # 4. BRAND QUALITY DISTRIBUTION
        st.subheader("⭐ Brand Quality Benchmarking")
        # Comparing the consistency of quality across major brands
        top_brands = vendor_stats.nlargest(10, 'Order_Volume')['Brand'].tolist()
        df_top_brands = df_ops[df_ops['brand'].isin(top_brands)]
        
        fig_quality = px.box(
            df_top_brands, x='brand', y='product_rating',
            color='brand', title="Product Quality Consistency by Top Brands",
            points="outliers"
        )
        st.plotly_chart(fig_quality, use_container_width=True)

        # 5. STRATEGIC INSIGHTS TABLE
        st.subheader("📑 Vendor Management Action Plan")
        # Identify "At Risk" Vendors: Slow delivery (> avg) AND low rating (< 3)
        avg_speed = vendor_stats['Avg_Lead_Time'].mean()
        at_risk = vendor_stats[(vendor_stats['Avg_Lead_Time'] > avg_speed) & (vendor_stats['Avg_Quality_Rating'] < 3.5)]
        
        if not at_risk.empty:
            st.warning("🚩 **Attention:** The following vendors are underperforming (Slow delivery & Low quality). Consider renegotiating contracts or switching suppliers.")
            st.dataframe(at_risk.sort_values('Avg_Quality_Rating'), use_container_width=True)
        else:
            st.success("✅ All major vendors are meeting basic performance benchmarks.")

    else:
        st.error("Supply Chain data could not be loaded. Please check your SQL connection.")
query_advanced = """
    SELECT 
        transaction_id, 
        order_date, 
        customer_id,
        customer_rating,
        final_amount_inr,
        quantity,
        delivery_days,
        return_status,
        brand,
        subcategory,
        category
    FROM public.maintable
    WHERE order_year >= (SELECT MAX(order_year) - 3 FROM public.maintable)
"""
df_adv = fetch_data(query_advanced)
# --- PAGE: PREDICTIVE ANALYTICS (Question 26) ---
if question == "Predictive Sales":
    st.header("🔮 Advanced Predictive Analytics & Forecasting")
    
    if not df_adv.empty:
        # 1. DATA CLEANING
        df_adv['order_date'] = pd.to_datetime(df_adv['order_date'])
        df_adv['final_amount_inr'] = pd.to_numeric(df_adv['final_amount_inr'], errors='coerce').fillna(0)

        # 2. REVENUE FORECASTING (Linear Regression Trend)
        st.subheader("📈 3-Month Revenue Forecast")
        # Resample data to monthly totals
        monthly_sales = df_adv.set_index('order_date').resample('ME')['final_amount_inr'].sum().reset_index()
        
        if len(monthly_sales) > 3:
            # Calculate Trendline
            monthly_sales['Month_Index'] = range(len(monthly_sales))
            slope, intercept = np.polyfit(monthly_sales['Month_Index'], monthly_sales['final_amount_inr'], 1)
            
            # Project future 3 months
            future_indices = np.array([len(monthly_sales), len(monthly_sales)+1, len(monthly_sales)+2])
            future_dates = [monthly_sales['order_date'].max() + pd.DateOffset(months=i+1) for i in range(3)]
            predictions = slope * future_indices + intercept

            fig_forecast = px.line(monthly_sales, x='order_date', y='final_amount_inr', title="Historical Trend vs. Future Projection")
            fig_forecast.add_scatter(x=future_dates, y=predictions, name="Forecasted Sales", line=dict(dash='dot', color='red'))
            st.plotly_chart(fig_forecast, use_container_width=True)
        else:
            st.warning("Insufficient historical data (need >3 months) for statistical forecasting.")

        st.divider()

        # 3. CHURN PREDICTION (Requires customer_id)
        st.subheader("🚪 Customer Churn Risk Index")
        if 'customer_id' in df_adv.columns:
            latest_date = df_adv['order_date'].max()
            # Calculate days since last purchase for each user
            churn_data = df_adv.groupby('customer_id')['order_date'].max().reset_index()
            churn_data['Days_Since_Last'] = (latest_date - churn_data['order_date']).dt.days
            
            def classify_churn(days):
                if days > 180: return 'High Risk (Churned)'
                if days > 90: return 'Medium Risk (Inactive)'
                return 'Low Risk (Active)'
            
            churn_data['Risk_Level'] = churn_data['Days_Since_Last'].apply(classify_churn)
            
            fig_churn = px.pie(churn_data, names='Risk_Level', title="User Retention Health",
                               color_discrete_map={'Low Risk (Active)':'#2ecc71', 'Medium Risk (Inactive)':'#f1c40f', 'High Risk (Churned)':'#e74c3c'})
            st.plotly_chart(fig_churn, use_container_width=True)
        else:
            st.error("Error: 'customer_id' missing from query. Churn analysis disabled.")

        st.divider()

        # 4. BUSINESS SCENARIO ANALYSIS (Prescriptive Analytics)
        st.subheader("💡 'What-If' Scenario Simulator")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("Adjust variables:")
            price_change = st.slider("Price Adjustment (%)", -20, 20, 0)
            marketing_boost = st.slider("Marketing Spend Increase (%)", 0, 100, 10)
        
        with col2:
            # Simulation Logic: Assumes price elasticity of -0.5 and marketing ROI of 0.2
            current_rev = monthly_sales['final_amount_inr'].iloc[-1]
            simulated_rev = current_rev * (1 + (price_change * -0.005)) * (1 + (marketing_boost * 0.002))
            
            st.metric("Predicted Monthly Revenue", f"₹{simulated_rev:,.0f}", 
                      delta=f"{((simulated_rev/current_rev)-1)*100:.1f}% Impact")
            st.caption("Simulation based on historical Price Elasticity and Marketing ROI models.")

    else:
        st.error("Predictive Analytics requires a populated dataset.")
# --- PAGE: MARKET INTELLIGENCE (Question 27) ---
elif question == "Customer Churn Prediction":
    st.header("🏢 Market Intelligence & Strategic Positioning")
    
    if not df_adv.empty:
        # 1. PRICING INTELLIGENCE (Price Point Distribution)
        st.subheader("💰 Pricing Intelligence: Premium vs. Economy")
        # We look at the average price point per brand within a subcategory
        selected_sub = st.selectbox("Select Segment to Analyze", df_adv['subcategory'].unique())
        
        market_segment = df_adv[df_adv['subcategory'] == selected_sub]
        price_dist = market_segment.groupby('brand')['final_amount_inr'].mean().reset_index()
        
        fig_price = px.violin(
            market_segment, x='brand', y='final_amount_inr',
            box=True, points="all", title=f"Price Positioning in {selected_sub}",
            color='brand', labels={'final_amount_inr': 'Price Point (₹)'}
        )
        st.plotly_chart(fig_price, use_container_width=True)

        st.divider()

        # 2. MARKET SHARE ANALYSIS (Competitive Tracking)
        st.subheader("🥧 Market Share by Brand (Volume vs. Value)")
        share_data = df_adv.groupby('brand').agg({
            'transaction_id': 'count',
            'final_amount_inr': 'sum'
        }).reset_index()
        share_data.columns = ['Brand', 'Units_Sold', 'Total_Revenue']

        c1, c2 = st.columns(2)
        with c1:
            fig_vol = px.pie(share_data, names='Brand', values='Units_Sold', 
                             title="Volume Share (Units)", hole=0.3)
            st.plotly_chart(fig_vol, use_container_width=True)
        with c2:
            fig_val = px.pie(share_data, names='Brand', values='Total_Revenue', 
                             title="Value Share (Revenue)", hole=0.3)
            st.plotly_chart(fig_val, use_container_width=True)

        st.divider()

        # 3. STRATEGIC POSITIONING MATRIX
        st.subheader("📍 Strategic Positioning Map")
        # X = Volume, Y = Avg Price, Size = Revenue
        positioning = df_adv.groupby('brand').agg({
            'transaction_id': 'count',
            'final_amount_inr': ['mean', 'sum']
        }).reset_index()
        positioning.columns = ['Brand', 'Volume', 'Avg_Price', 'Revenue']

        fig_map = px.scatter(
            positioning, x='Volume', y='Avg_Price',
            size='Revenue', color='Brand', hover_name='Brand',
            title="Market Landscape: Leaders, Challengers, and Niche Players",
            labels={'Avg_Price': 'Avg Unit Price (₹)', 'Volume': 'Total Units Sold'}
        )
        # Quadrant Lines
        fig_map.add_hline(y=positioning['Avg_Price'].median(), line_dash="dot", line_color="gray")
        fig_map.add_vline(x=positioning['Volume'].median(), line_dash="dot", line_color="gray")
        st.plotly_chart(fig_map, use_container_width=True)

        st.info("""
        **🔍 Strategy Guide:**
        * **Top-Right (High Vol, High Price):** Market Leaders / Premium Giants.
        * **Bottom-Right (High Vol, Low Price):** Mass Market Challengers.
        * **Top-Left (Low Vol, High Price):** Luxury / Niche Specialists.
        * **Bottom-Left (Low Vol, Low Price):** Potential Laggards / Emerging Brands.
        """)

    else:
        st.error("Market data unavailable.")
# --- PAGE: CROSS-SELL & UPSELL (Question 28) ---
elif question == "Product Recommendation":
    st.header("🎯 Cross-selling & Upselling Strategy")
    
    if not df_adv.empty:
        # 1. IDENTIFYING PRODUCT ASSOCIATIONS (Market Basket)
        st.subheader("🛒 Frequently Bought Together (Bundle Opportunities)")
        
        # Group items by transaction
        basket = df_adv.groupby(['customer_id', 'order_date'])['subcategory'].apply(list).reset_index()
        # Filter for transactions with more than 1 item
        multi_item_basket = basket[basket['subcategory'].map(len) > 1]

        if not multi_item_basket.empty:
            from itertools import combinations
            from collections import Counter

            # Generate all possible pairs within each transaction
            item_pairs = []
            for items in multi_item_basket['subcategory']:
                item_pairs.extend(list(combinations(sorted(items), 2)))
            
            # Count occurrences of each pair
            most_common_pairs = Counter(item_pairs).most_common(10)
            
            # Prepare data for plotting
            pair_names = [f"{p[0][0]} + {p[0][1]}" for p in most_common_pairs]
            pair_counts = [p[1] for p in most_common_pairs]

            fig_bundle = px.bar(
                x=pair_counts, y=pair_names, orientation='h',
                title="Top 10 High-Affinity Product Pairs",
                color=pair_counts, color_continuous_scale='Sunsetdark',
                labels={'x': 'Co-occurrence Frequency', 'y': 'Product Pair'}
            )
            fig_bundle.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_bundle, use_container_width=True)
        else:
            st.info("No multi-item transactions found to generate associations.")

        st.divider()

        # 2. UPSELLING POTENTIAL (Category Tiering)
        st.subheader("⬆️ Upselling: Higher-Value Alternatives")
        # Identify subcategories with the widest price range (opportunity to move customers up)
        upsell_data = df_adv.groupby('subcategory')['final_amount_inr'].agg(['min', 'max', 'mean']).reset_index()
        upsell_data['Price_Gap'] = upsell_data['max'] - upsell_data['min']
        
        fig_upsell = px.scatter(
            upsell_data.nlargest(15, 'Price_Gap'), 
            x='mean', y='Price_Gap', size='max', color='subcategory',
            title="Upsell Potential: Price Spread per Subcategory",
            labels={'mean': 'Average Price (₹)', 'Price_Gap': 'Upgrade Range (Max - Min)'}
        )
        st.plotly_chart(fig_upsell, use_container_width=True)

        # 3. STRATEGIC INSIGHTS
        st.info("""
        **💡 Revenue Optimization Strategy:**
        * **Bundling:** Use the 'High-Affinity' chart to create pre-packaged kits (e.g., Laptops + Sleeves).
        * **Upselling:** Target customers in categories with high 'Price Gaps' by showing 'Premium' alternatives during checkout.
        """)
# --- PAGE: SEASONAL PLANNING (Question 29) ---
elif question == "Sentiment Analysis":
    st.header("📅 Seasonal Planning & Inventory Optimization")
    
    if not df_adv.empty:
        # 1. TIME PREP
        df_adv['order_date'] = pd.to_datetime(df_adv['order_date'])
        df_adv['Month'] = df_adv['order_date'].dt.month_name()
        df_adv['Month_Num'] = df_adv['order_date'].dt.month
        
        # 2. SEASONAL DEMAND HEATMAP
        st.subheader("🔥 Monthly Demand Heatmap (By Category)")
        # This shows WHICH categories peak in WHICH months
        seasonal_heat = df_adv.groupby(['Month_Num', 'Month', 'category'])['quantity'].sum().reset_index()
        seasonal_heat = seasonal_heat.sort_values('Month_Num')

        fig_heat = px.density_heatmap(
            seasonal_heat, x='Month', y='category', z='quantity',
            title="Seasonal Demand: When to Stock Up?",
            color_continuous_scale='YlOrRd',
            category_orders={'Month': ['January', 'February', 'March', 'April', 'May', 'June', 
                                       'July', 'August', 'September', 'October', 'November', 'December']}
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        st.divider()

        # 3. PROMOTIONAL CALENDAR PLANNING
        st.subheader("🎟️ Promotional Strategy Planner")
        # Identify "Slump" months where promotions are needed
        monthly_revenue = df_adv.groupby(['Month_Num', 'Month'])['final_amount_inr'].sum().reset_index()
        monthly_revenue = monthly_revenue.sort_values('Month_Num')
        
        avg_rev = monthly_revenue['final_amount_inr'].mean()
        monthly_revenue['Performance'] = monthly_revenue['final_amount_inr'].apply(
            lambda x: 'Peak (Overstock)' if x > avg_rev * 1.2 else ('Slump (Promote)' if x < avg_rev * 0.8 else 'Stable')
        )

        fig_promo = px.bar(
            monthly_revenue, x='Month', y='final_amount_inr', color='Performance',
            title="Revenue Cycles: Peak vs. Slump Months",
            color_discrete_map={'Peak (Overstock)': '#e74c3c', 'Slump (Promote)': '#3498db', 'Stable': '#95a5a6'}
        )
        st.plotly_chart(fig_promo, use_container_width=True)

        # 4. RESOURCE ALLOCATION INSIGHTS
        st.info("""
        **🚀 Strategic Resource Allocation:**
        * **Red Months (Peak):** Increase warehouse staff by 20% and double safety stock for Top Categories.
        * **Blue Months (Slump):** Run "Clearance Sales" or "Bundling Offers" (from Q28) to maintain cash flow.
        """)

# --- PAGE: BI COMMAND CENTER (Question 30) ---
elif question == "Supply Chain Optimization":
    st.header("🛡️ BI Command Center: Executive Oversight")
    
    if not df_adv.empty:
        # 1. LIVE PERFORMANCE MONITORING (Top KPI Tiles)
        df_adv['delivery_days'] = pd.to_numeric(df_adv['delivery_days'], errors='coerce').fillna(0)
        df_adv['final_amount_inr'] = pd.to_numeric(df_adv['final_amount_inr'], errors='coerce').fillna(0)
        df_adv['customer_rating'] = pd.to_numeric(df_adv['customer_rating'], errors='coerce').fillna(0)
        df_adv['order_date'] = pd.to_datetime(df_adv['order_date'])
        
        # # Calculate growth vs previous period
        current_rev = df_adv['final_amount_inr'].sum()
        avg_delivery = df_adv['delivery_days'].mean()
        avg_rating = df_adv['customer_rating'].mean()
        return_rate = (df_adv['return_status'] == 'Returned').mean() * 100

        # 2. Calculate Return Rate ONLY if the column exists
        if 'return_status' in df_adv.columns:
            return_rate = (df_adv['return_status'] == 'Returned').mean() * 100
            return_display = f"{return_rate:.1f}%"
        else:
            return_display = "Data N/A"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Revenue", f"₹{current_rev/1e7:.2f}Cr", "Active")
        c2.metric("Avg Delivery", f"{avg_delivery:.1f} Days", "-0.2d", delta_color="inverse")
        c3.metric("Customer CSAT", f"{avg_rating:.2f} ⭐", "+5%")
        c4.metric("Return Rate", f"{return_rate:.1f}%", "Target < 5%")

        st.divider()

        # 2. AUTOMATED ALERTS & STRATEGIC DECISION SUPPORT
        st.subheader("⚠️ System Alerts & Threshold Monitoring")
        
        alert_col1, alert_col2 = st.columns(2)
        
        with alert_col1:
            if avg_delivery > 5:
                st.error("🚨 **CRITICAL:** Logistics Bottleneck detected. Delivery times exceed 5-day threshold.")
            else:
                st.success("✅ Logistics Health: Normal")
                
            if return_rate > 8:
                st.warning("⚠️ **WARNING:** High Return Volume. Audit subcategory quality immediately.")
            else:
                st.success("✅ Product Quality: Stable")

        with alert_col2:
            # Decision Support: Calculating "Runway" or "Momentum"
            recent_trend = df_adv.set_index('order_date').resample('D')['transaction_id'].count().tail(7).mean()
            st.info(f"💡 **Strategic Insight:** Current daily velocity is **{recent_trend:.0f} orders/day**. Ensure warehouse staffing is optimized for this load.")

        st.divider()

        # 3. MULTI-DIMENSIONAL PERFORMANCE MATRIX
        st.subheader("🌐 Global Performance Pulse")
        # Combining Revenue and Delivery Speed to find "Efficiency Hotspots"
        daily_perf = df_adv.groupby('order_date').agg({
            'final_amount_inr': 'sum',
            'delivery_days': 'mean'
        }).reset_index()

        fig_pulse = px.scatter(
            daily_perf, x='order_date', y='final_amount_inr',
            size='delivery_days', color='delivery_days',
            title="Revenue vs. Delivery Latency (Bubble Size = Delay)",
            color_continuous_scale='Portland'
        )
        st.plotly_chart(fig_pulse, use_container_width=True)

        # 4. EXPORT COMMAND
        st.download_button(
            label="📥 Download Executive Summary (CSV)",
            data=df_adv.to_csv(index=False),
            file_name="Amazon_Executive_Summary.csv",
            mime="text/csv"
        )

    else:
        st.error("Command Center offline. No data stream detected.")