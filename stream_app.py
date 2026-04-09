import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIGURATION ---
# This must be the very first Streamlit command
st.set_page_config(page_title="Cricket Test: Live Scores", layout="wide")

# Using the API key from your provided snippet
HEADERS = {
    "x-rapidapi-key": "35af2ec44amsh9bf8173e77da1c2p13358ejsn3a9ce0e712f9",
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}

# # --- 2. HELPER FUNCTION ---
# @st.cache_data(ttl=10)
# def fetch_api(endpoint, params=None):
#     url = f"https://cricbuzz-cricket.p.rapidapi.com/{endpoint}"
#     try:
#         response = requests.get(url, headers=HEADERS, params=params)
#         response.raise_for_status() # Check for HTTP errors
#         return response.json()
#     except Exception as e:
#         st.error(f"API Error: {e}")
#         return None
@st.cache_data(ttl=10)
def fetch_api(endpoint, params=None):
    url = f"https://cricbuzz-cricket.p.rapidapi.com/{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        
        # Check if the response is actually a success (200 OK)
        if response.status_code == 200:
            return response.json()
        
        # Handle common RapidAPI errors specifically
        elif response.status_code == 429:
            st.error("Rate Limit Exceeded: You have used all your free requests for today.")
        elif response.status_code == 403:
            st.error("Forbidden: Check if your API key is still active in RapidAPI.")
        else:
            st.error(f"API returned status {response.status_code}: {response.text[:100]}")
            
    except Exception as e:
        st.error(f"Connection Error: {e}")
    
    return None

# --- 3. TEST PAGE LOGIC ---
st.title("🏏 Live Match Scorecard Test")

# Fetching the list of all live matches
with st.spinner("Fetching live matches..."):
    data = fetch_api("matches/v1/recent")

matches = []
if data and "typeMatches" in data:
    for type_match in data.get("typeMatches", []):
        for series_matches in type_match.get('seriesMatches', []):
            series_wrapper = series_matches.get('seriesAdWrapper')
            if not series_wrapper:
                continue
            
            series_name = series_wrapper.get('seriesName', "Unknown Series")
            
            for match in series_wrapper.get('matches', []):
                info = match.get('matchInfo')
                if info:
                    matches.append({
                        "matchId": info.get('matchId'),
                        "display_name": f"{info.get('team1',{}).get('teamName')} vs {info.get('team2',{}).get('teamName')} ({series_name})",
                        "status": info.get('status', "No status available")
                    })

if matches:
    df_live = pd.DataFrame(matches)
    
    # Selectbox to pick a specific match
    selected_index = st.selectbox(
        "Choose a match to view details:", 
        range(len(df_live)), 
        format_func=lambda i: df_live.iloc[i]["display_name"]
    )
    selected_match = df_live.iloc[selected_index]
    
    st.metric("Current Status", selected_match["status"])
    
    # Fetching the detailed scorecard for the chosen match
    with st.spinner("Loading detailed scorecard..."):
        scard_data = fetch_api(f"mcenter/v1/{selected_match['matchId']}/scard")
        scorecard = scard_data.get('scorecard', []) if scard_data else []

    if not scorecard:
        st.warning("Detailed scorecard data is not yet available for this match.")
    else:
        # Create tabs for each innings (e.g., Team A Innings, Team B Innings)
        tabs = st.tabs([f"{inn.get('batteamname', 'Team')} Innings" for inn in scorecard])
        
        for i, inn in enumerate(scorecard):
            with tabs[i]:
                st.subheader(f"Score: {inn.get('score')}/{inn.get('wickets')} ({inn.get('overs')} ov)")
                
                # BATTING TABLE
                bat_list = inn.get('batsman', [])
                if bat_list:
                    st.markdown("#### Batting")
                    df_bat = pd.DataFrame(bat_list)
                    # Filter for columns that actually exist in the API response
                    cols_to_show = ['name', 'outdec', 'runs', 'balls', 'fours', 'sixes', 'strkrate']
                    available_cols = [c for c in cols_to_show if c in df_bat.columns]
                    st.table(df_bat[available_cols])
                
                # BOWLING TABLE
                bowl_list = inn.get('bowler', [])
                if bowl_list:
                    st.markdown("#### Bowling")
                    df_bowl = pd.DataFrame(bowl_list)
                    cols_to_show = ['name', 'overs', 'maidens', 'runs', 'wickets', 'economy']
                    available_cols = [c for c in cols_to_show if c in df_bowl.columns]
                    st.table(df_bowl[available_cols])
else:
    st.info("No live matches were found in the API response. This happens if no matches are currently being played.")