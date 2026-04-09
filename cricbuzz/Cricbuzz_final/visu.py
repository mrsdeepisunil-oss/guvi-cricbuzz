import streamlit as st
import pandas as pd
import psycopg2
import requests

# --- 1. CONFIGURATION ---
# IMPORTANT: st.set_page_config MUST be the very first Streamlit command
st.set_page_config(page_title="Cricbuzz Dashboard Pro", layout="wide")

HEADERS = {
    "x-rapidapi-key": "35af2ec44amsh9bf8173e77da1c2p13358ejsn3a9ce0e712f9",
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}

# --- 2. HELPER FUNCTIONS ---

def get_db_connection():
    try:
        return psycopg2.connect(
            host='localhost', database='cricbuzz',
            user='postgres', password='deepika@88', port=5432
        )
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")
        return None

@st.cache_data(ttl=10)
def fetch_api(endpoint, params=None):
    url = f"https://cricbuzz-cricket.p.rapidapi.com/{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🏏 Cricket Dashboard")
page = st.sidebar.selectbox(
    "Go to:",
    ["Home Page", "Live Match Page", "Player Stats", "SQL Queries & Analytics", "CRUD Operations"]
)

# --- 4. PAGE LOGIC ---

# ---------------- HOME PAGE ----------------
if page == "Home Page":
    st.title("🏠 Cricket Analytics Hub")
    st.markdown("### **Welcome to your comprehensive cricket management system.**")
    st.info("👈 Select a page from the sidebar to navigate.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🛠️ Tools & Technologies")
        st.write("- **Frontend:** Streamlit")
        st.write("- **Database:** PostgreSQL")
    with col2:
        st.markdown("#### 📊 Key Features")
        st.write("- **Real-time:** Live match scorecards.")
        st.write("- **CRUD:** Manage your own cricket records.")

# ---------------- LIVE MATCH PAGE ----------------
elif page == "Live Match Page":
    st.title("🏏 Live Match Scorecard")
    data = fetch_api("matches/v1/recent")
    
    matches = []
    if data and "typeMatches" in data:
        for type_match in data.get("typeMatches", []):
            for series_matches in type_match.get('seriesMatches', []):
                series_data = series_matches.get('seriesAdWrapper', {})
                series_name = series_data.get('seriesName', "Unknown Series")
                for match in series_data.get('matches', []):
                    info = match.get('matchInfo', {})
                    if info:
                        matches.append({
                            "matchId": info.get('matchId'),
                            "display_name": f"{info.get('team1',{}).get('teamName')} vs {info.get('team2',{}).get('teamName')} ({series_name})",
                            "format": info.get('matchFormat'),
                            "venue": info.get('venueInfo', {}).get('ground'),
                            "status": info.get('status')
                        })

    if matches:
        df_live = pd.DataFrame(matches)
        selected_index = st.selectbox("Choose a match:", range(len(df_live)), format_func=lambda i: df_live.iloc[i]["display_name"])
        selected_match = df_live.iloc[selected_index]
        
        st.metric("Status", selected_match["status"])
        
        scard_data = fetch_api(f"mcenter/v1/{selected_match['matchId']}/scard")
        scorecard = scard_data.get('scorecard', []) if scard_data else []

        if not scorecard:
            st.warning("Detailed scorecard not yet available.")
        else:
            tabs = st.tabs([f"{inn.get('batteamname')} Innings" for inn in scorecard])
            for i, inn in enumerate(scorecard):
                with tabs[i]:
                    st.subheader(f"Score: {inn.get('score')}/{inn.get('wickets')} ({inn.get('overs')} ov)")
                    st.markdown("#### Batting")
                    st.table(pd.DataFrame(inn.get('batsman', []))[['name', 'outdec', 'runs', 'balls', 'fours', 'sixes', 'strkrate']])
                    st.markdown("#### Bowling")
                    st.table(pd.DataFrame(inn.get('bowler', []))[['name', 'overs', 'maidens', 'runs', 'wickets', 'economy']])
    else:
        st.info("No live matches found.")

# ---------------- PLAYER STATS ----------------
elif page == "Player Stats":
    
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
        search_button = st.button("Search player", use_container_width=True)

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
                    p1, p2 = st.columns(2)
                    with p1: custom_metric("Height", det_data.get("height", "N/A"))
                    with p2: custom_metric("Role", det_data.get("role", "N/A"))
                    p3, p4 = st.columns(2)
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
   
elif page == "SQL Queries & Analytics":

    st.title("📊 SQL Analytics")

    query_option = st.selectbox(
        "Select Analysis",
        ["Players Representing India",
        "Recent Matches (Last Few Days)",
        "Top 10 highest run in ODI",
        "Top 10 Largest Cricket Venues (2026)",
        "Most Successful International Cricket Teams",
        "Player Role Count",
        "Highest Individual Scores by Format",
        "2024 Cricket Series",
        "All-rounders: Runs >1000 & Wickets >50",
        "Last 20 Completed Matches Details",
        "Player Performance Across Formats (Test, ODI, T20I)",
        "Team Performance: Home vs Away Wins",
        "Century Partnerships",
        "Venue Economy",
        "Close Game Performers",
        "Player Performance by Year",
        "Toss Outcome Analysis",
        "Limited-Overs Economy",
        "Player Consistency",
        "Player Format Stats",
        "Player Format Ranking",
        "Head-to-Head Analysis",
        "Player Form Status",
        "Successful Partnerships",
        "Time-series analysis"
        ]
    )
    queries = {

        "Players Representing India": """
        SELECT 
            full_name,
            playingrole,
            batting_style,
            bowling_style
        FROM public.q1_players_india
        """,
        "Recent Matches (Last Few Days)": """
        SELECT
            team1,
            team2,
            venue,
            match_date
        FROM public.q2_recent_matches
        ORDER BY match_date DESC
        """,
        "Top 10 highest run in ODI": """
        SELECT
            playerid,
            player,
            matches,
            innings,
            runs,
            average,
            century
        FROM public.top10_odi
        LIMIT 10
        """,
        "Top 10 Largest Cricket Venues (2026)": """
        SELECT
            venue_ground,
            city,
            country,
            capacity
        FROM public.q4_venu;
        """,
         "Most Successful International Cricket Teams": """
        SELECT
            team_name,
            total_wins
	    FROM public.q5_most_wins;
        """,
         "Player Role Count": """
        SELECT
            simplified_role,
            player_count
	    FROM public.q6_player_roles;
        """,
        "Highest Individual Scores by Format": """
        SELECT 'ODI' AS format, MAX(runs) AS highest_score FROM odi
        UNION ALL
        SELECT 'Test' AS format, MAX(runs) AS highest_score
        FROM test_mat
        UNION ALL
        SELECT 'T20I' AS format, MAX(runs) AS highest_score
        FROM t20_mat;
        """,
        "2024 Cricket Series": """
        SELECT * from q8_match_2024;
        """,
        "All-rounders: Runs >1000 & Wickets >50": """
        select * from public.q9_allround_rank
        """,
        "Last 20 Completed Matches Details": """
        select * from public.q10_last20matches
        """,
        "Player Performance Across Formats (Test, ODI, T20I)": """
        select * from public.play_diff_match
        """,
        "Team Performance: Home vs Away Wins": """
        select * from public.q12_count_of_wins
        """,
        "Century Partnerships": """
        select * from public.scard_partner
        """,
        "Venue Economy": """
        select * from public.q14_bowler_perf
        """,
        "Close Game Performers": """
        select * from public.q15_performance
        """,
        "Player Performance by Year": """
        select * from public.q16_2020
        """,
        "Toss Outcome Analysis": """
        select * from public.q17_toss
        """,
        "Limited-Overs Economy": """
        select * from q18_bowl_economy
        """,
        "Player Consistency": """
        select * from q19_stddevi_2022
        """,
        "Player Format Stats": """
        select * from q20_diff_match
        """,
        "Player Format Ranking": """
        select * from q21_players_ranking
        """,
         "Head-to-Head Analysis": """
        select * from public.q22_3years
        """,
         "Player Form Status": """
        select * from public.q23
        """,
         "Successful Partnerships": """
        select * from public.q24_batting_partner
        """,
        "Time-series analysis": """
        select * from public.q25_performance_trend
        """,
    }

    try:
        conn = get_db_connection()

        if query_option == "Team Performance: Home vs Away Wins":

            col1, col2 = st.columns(2)

            # Home Wins
            with col1:
                st.subheader("🏠 Home Wins")
                df_home = pd.read_sql("SELECT * FROM public.q12_count_of_wins", conn)
                st.dataframe(df_home)

            # Away Wins
            with col2:
                st.subheader("✈️ Away Wins")
                df_away = pd.read_sql("SELECT * FROM public.away_wins", conn)
                st.dataframe(df_away)

        elif query_option == "Head-to-Head Analysis":
            col1, col2 = st.columns(2)

            # Wins for each team
            with col1:
                st.subheader("Wins for Each Team")
                df_wins = pd.read_sql("""
                    SELECT result_short AS team, COUNT(*) AS wins
                    FROM public.q22_test
                    GROUP BY result_short
                """, conn)
                st.dataframe(df_wins)

            # Total Matches
            with col2:
                st.subheader("Total Matches Played")
                df_total = pd.read_sql("""
                    SELECT team1, team2, COUNT(*) AS total_matches
                    FROM public.q22_final
                    GROUP BY team1, team2
                """, conn)
                st.dataframe(df_total)

            # NEW TABLE BELOW (Draw Matches)
            st.subheader("H2H Matches Details")
            df_h2h = pd.read_sql("""
                 select * from public.q22_3years
            """, conn)
            st.dataframe(df_h2h)

        elif query_option == "Time-series analysis":
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Wins for Each Team")
                df_timeseries = pd.read_sql("""
                    SELECT * FROM public.q25_performance_trend
                """, conn)
                st.dataframe(df_timeseries)
            with col2:
            # Quarterly Average Performance
                st.subheader("Quarterly Average Performance")
                df_qaperf = pd.read_sql("SELECT * FROM public.q25_quarterly_avg", conn)
                st.dataframe(df_qaperf)   

        else:
            query = queries[query_option]
            df = pd.read_sql(query, conn)
            st.dataframe(df)

        conn.close()

    except Exception as e:
        st.error(f"Database Error: {e}")
  
elif page == "CRUD Operations":
    st.title("⚙️ Database CRUD")
    
    conn = get_db_connection()
    cur = conn.cursor()

    tab1, tab2, tab3, tab4 = st.tabs(["Create", "Read", "Update", "Delete"])

    # ---------------- CREATE ----------------
    with tab1:

        st.subheader("Add Player")

        with st.form("create_form"):

            player_id = st.text_input("Player ID")
            full_name = st.text_input("Full Name")
            batting_style = st.text_input("Batting Style")
            bowling_style = st.text_input("Bowling Style")
            role = st.text_input("Playing Role")

            submit = st.form_submit_button("Add Player")

            if submit:
                try:
                    cur.execute("""
                        INSERT INTO player_test
                        (player_id, full_name, batting_style, bowling_style, playingrole)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (player_id, full_name, batting_style, bowling_style, role))

                    conn.commit()

                    st.success("Player Added Successfully")

                except Exception as e:
                    conn.rollback()   # undo failed transaction
                    st.error(f"Error inserting player: {e}")

            # if submit:

            #     cur.execute("""
            #     INSERT INTO player_test
            #     (player_id, full_name, batting_style, bowling_style, playingrole)
            #     VALUES (%s,%s,%s,%s,%s)
            #     """,
            #     (player_id, full_name, batting_style, bowling_style, role)
            #     )

            #     conn.commit()

            #     st.success("Player Added Successfully")


    # ---------------- READ ----------------
    with tab2:

        st.subheader("Player List")

        df = pd.read_sql("SELECT * FROM player_test", conn)

        st.dataframe(df)


    # ---------------- UPDATE ----------------
    with tab3:

        st.subheader("Update Player")

        player_id = st.text_input("Player ID to Update")

        new_name = st.text_input("New Name")
        new_batting = st.text_input("New Batting Style")
        new_bowling = st.text_input("New Bowling Style")
        new_role = st.text_input("New Role")

        if st.button("Update Player"):

            cur.execute("""
            UPDATE player_test
            SET full_name=%s,
                batting_style=%s,
                bowling_style=%s,
                playingrole=%s
            WHERE player_id=%s
            """,
            (new_name, new_batting, new_bowling, new_role, player_id)
            )

            conn.commit()

            st.success("Player Updated Successfully")


    # ---------------- DELETE ----------------
    with tab4:

        st.subheader("Delete Player")

        delete_id = st.text_input("Player ID to Delete")

        if st.button("Delete Player"):

            cur.execute(
                "DELETE FROM player_test WHERE player_id=%s",
                (delete_id,)
            )

            conn.commit()

            st.success("Player Deleted Successfully")


    cur.close()
    conn.close()