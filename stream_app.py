import streamlit as st
import requests
import pandas as pd

# --- 1. GLOBAL UI SETTINGS & FUNCTIONS ---
st.set_page_config(page_title="Cricket Dashboard", layout="wide")

def custom_metric(label, value):
    """Ensures small labels and big bold values without truncation."""
    st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <p style="font-size: 14px; color: #808495; margin-bottom: -5px; font-weight: 500;">{label}</p>
            <p style="font-size: 24px; font-weight: 700; white-space: nowrap;">{value}</p>
        </div>
    """, unsafe_allow_html=True)

# Session State Initialization
if 'search_val' not in st.session_state: st.session_state['search_val'] = ""
if 'q2024' not in st.session_state: st.session_state['q2024'] = None

st.title("🏏 Cricket Player Dashboard")

# --- 2. SEARCH SECTION ---
col1, col2 = st.columns([4, 1])
with col1:
    player_query = st.text_input("Search", value=st.session_state['search_val'], placeholder="Enter name...", label_visibility="collapsed")
with col2:
    search_button = st.button("Find Matches", use_container_width=True)

headers = {
    "x-rapidapi-key": "35af2ec44amsh9bf8173e77da1c2p13358ejsn3a9ce0e712f9",
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}

# API Search Logic
if search_button and player_query:
    try:
        url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/search"
        response = requests.get(url, headers=headers, params={"plrN": player_query})
        data = response.json()
        if 'player' in data:
            raw_df = pd.DataFrame(data['player'])
            st.session_state['q2024'] = raw_df[['id', 'name', 'teamName']].copy()
            st.session_state['q2024'].columns = ['player_id', 'name', 'team_name']
    except Exception as e: st.error(f"Search Error: {e}")

# --- 3. MAIN TABBED INTERFACE ---
if st.session_state['q2024'] is not None:
    q2024 = st.session_state['q2024']
    q2024['display'] = q2024['name'] + " (" + q2024['team_name'] + ")"
    options = ["-- Select Player --"] + q2024['display'].tolist()
    
    selected_option = st.selectbox("Select Result:", options)

    if selected_option != "-- Select Player --":
        player_info = q2024[q2024['display'] == selected_option].iloc[0]
        player_id = player_info['player_id']

        # --- CREATE TABS ---
        tab_prof, tab_bat, tab_bowl = st.tabs(["👤 Profile", "🏏 Batting Stats", "⚡ Bowling Stats"])

        # --- TAB 1: PROFILE ---
        with tab_prof:
            try:
                details_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}"
                det_data = requests.get(details_url, headers=headers).json()
                
                st.subheader(f"Profile: {player_info['name']}")
                p1, p2, p3, p4 = st.columns(4)
                with p1: custom_metric("Height", det_data.get("height", "N/A"))
                with p2: custom_metric("Role", det_data.get("role", "N/A"))
                with p3: custom_metric("Birth Place", det_data.get("birthPlace", "N/A"))
                with p4: custom_metric("Date of Birth", det_data.get("DoB", "N/A"))
            except: st.error("Error loading profile.")

        # --- TAB 2: BATTING ---
        with tab_bat:
            try:
                bat_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/batting"
                bat_data = requests.get(bat_url, headers=headers).json()
                if 'values' in bat_data:
                    st.subheader("Career Batting Overview")
                    b_cols = st.columns(4)
                    fmts = {"Test": 1, "ODI": 2, "T20": 3, "IPL": 4}
                    rows = bat_data['values']
                    for i, (f_name, c_idx) in enumerate(fmts.items()):
                        with b_cols[i]:
                            st.markdown(f"**{f_name}**")
                            custom_metric("Matches", rows[0]['values'][c_idx])
                            custom_metric("Runs", rows[2]['values'][c_idx])
                            custom_metric("Average", rows[5]['values'][c_idx])
                            custom_metric("SR", rows[6]['values'][c_idx])
            except: st.info("Batting data unavailable.")

        # --- TAB 3: BOWLING ---
        with tab_bowl:
            try:
                bowl_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/bowling"
                bowl_data = requests.get(bowl_url, headers=headers).json()
                if 'values' in bowl_data:
                    st.subheader("Career Bowling Overview")
                    bw_cols = st.columns(4)
                    for i, (f_name, c_idx) in enumerate(fmts.items()):
                        with bw_cols[i]:
                            st.markdown(f"**{f_name}**")
                            custom_metric("Matches", bowl_data['values'][0]['values'][c_idx])
                            custom_metric("Wickets", bowl_data['values'][2]['values'][c_idx])
                            custom_metric("Economy", bowl_data['values'][9]['values'][c_idx])
                            custom_metric("BBI", bowl_data['values'][7]['values'][c_idx])
            except: st.info("Bowling data unavailable.")