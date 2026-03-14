import streamlit as st
import pandas as pd
import requests

# API Config
headers = {
    "x-rapidapi-key": "095038d962msh9068af945c80bc9p1ad37cjsna03b2a42de54",
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}

st.set_page_config(page_title="Cricket Live Scorecard", layout="wide")
st.title("🏏 Live Match Scorecard")

# 1. Fetch Live Matches List
live_url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
response = requests.get(live_url, headers=headers)
data = response.json()

matches = []
if data and "typeMatches" in data:
    for type_match in data.get("typeMatches", []):
        for series_matches in type_match.get('seriesMatches', []):
            series_data = series_matches.get('seriesAdWrapper', {})
            series_name = series_data.get('seriesName', "Unknown Series")

            # Check for matches within this series wrapper
            for match in series_data.get('matches', []):
                info = match.get('matchInfo', {})
                if info:
                    matches.append({
                        "matchId": info.get('matchId'),
                        "series_name": series_name,
                        "team1": info.get('team1', {}).get('teamName'),
                        "team2": info.get('team2', {}).get('teamName'),
                        "status": info.get('status'),
                        "format": info.get('matchFormat'),
                        "venue": info.get('venueInfo', {}).get('ground'),
                        "display_name": f"{info.get('team1',{}).get('teamName')} vs {info.get('team2',{}).get('teamName')} ({series_name})"
                    })

if matches:
    df_live = pd.DataFrame(matches)

    # Match Selector UI
    selected_index = st.selectbox(
        "Choose an ongoing match:",
        options=range(len(df_live)),
        format_func=lambda i: df_live.iloc[i]["display_name"]
    )

    selected_match = df_live.iloc[selected_index]
    selected_id = selected_match["matchId"]

    # Quick Summary Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Format", selected_match["format"])
    col2.metric("Venue", selected_match["venue"])
    col3.info(f"**Status:** {selected_match['status']}")

    st.divider()

    # 2. Fetch Detailed Scorecard using the Selected ID
    scard_url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{selected_id}/scard"
    scard_data = requests.get(scard_url, headers=headers).json()
    scorecard_data = scard_data.get('scorecard', [])

    if not scorecard_data:
        st.warning("Scorecard data not available for this specific match yet.")
    else:
        # Create Tabs for Innings
        tabs = st.tabs([f"{inn.get('batteamname')} Innings" for inn in scorecard_data])

        for i, inn in enumerate(scorecard_data):
            with tabs[i]:
                # Inning Metrics
                c1, c2, c3 = st.columns(3)
                c1.metric("Score", f"{inn.get('score')}/{inn.get('wickets')}")
                c2.metric("Overs", f"{inn.get('overs')}")
                c3.metric("Run Rate", f"{inn.get('runrate')}")

                # Batting Table
                st.markdown("### **Batting**")
                bat_list = []
                for b in inn.get('batsman', []):
                    bat_list.append({
                        "Batsman": b.get('name'),
                        "Status": b.get('outdec'),
                        "R": b.get('runs'),
                        "B": b.get('balls'),
                        "4s": b.get('fours'), 
                        "6s": b.get('sixes'),
                        "SR": b.get('strkrate')
                    })
                if bat_list:
                    st.table(pd.DataFrame(bat_list))

                # Bowling Table
                st.markdown("### **Bowling**")
                bowl_list = []
                for bw in inn.get('bowler', []):
                    bowl_list.append({
                        "Bowler": bw.get('name'),
                        "O": bw.get('overs'),
                        "M": bw.get('maidens'),
                        "R": bw.get('runs'),
                        "W": bw.get('wickets'),
                        "Eco": bw.get('economy')
                    })
                if bowl_list:
                    st.table(pd.DataFrame(bowl_list))
else:
    st.info("No live matches found currently.")