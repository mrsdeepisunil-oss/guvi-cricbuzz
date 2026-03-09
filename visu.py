import streamlit as st
import pandas as pd
import psycopg2
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Cricbuzz Dashboard Pro", layout="wide")

HEADERS = {
    "X-RapidAPI-Key": "2454e52ef7msha9ad8a68de89ea1p1b4c51jsn18b293bbd472",
    "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
}

# --- 2. HELPER FUNCTIONS ---

def get_db_connection():
    return psycopg2.connect(
        host='localhost', database='cricbuzz',
        user='postgres', password='deepika@88', port=5432
    )
# Streamlit decorator used to cache the output of a function
@st.cache_data(ttl=60)
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

if page == "Home Page":
    st.title("🏠 Cricket Analytics Hub")
    st.write("Welcome to your comprehensive cricket management system.")
    st.info("Select a page from the sidebar to begin.")

elif page == "Live Match Page":
    st.title("📡 Live Match Status")
    data = fetch_api("matches/v1/live")
    
    match_map = {}
    if data:
        for match_type in data.get('typeMatches', []):
            for series in match_type.get('seriesMatches', []):
                if 'seriesAdWrapper' in series:
                    for m in series['seriesAdWrapper'].get('matches', []):
                        m_info = m.get('matchInfo', {})
                        name = f"{m_info.get('team1', {}).get('teamName')} vs {m_info.get('team2', {}).get('teamName')}"
                        match_map[name] = m_info.get('matchId')

    if match_map:
        selected_match = st.selectbox("Select a Live Match", options=list(match_map.keys()))
        m_id = match_map[selected_match]  
        st.write(f"Showing details for: **{selected_match}**")
        
        # Fetch detailed info for selected match
        details = fetch_api(f"msc/v1/scorecard/{m_id}")
        if details:
            st.subheader(f"🏏 {selected_match}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Status", details.get('status', 'N/A'))
            col2.metric("Venue", details.get('venue', {}).get('name', 'N/A'))
            col3.metric("Toss", details.get('tossResults', {}).get('tossWinnerName', 'N/A'))
            
            st.write("---")
            st.markdown("### 📊 Basic Scorecard")
            # This is a simplified display of the nested JSON
            st.json(details.get('scorecard', "Scorecard data loading..."))
    else:
        st.warning("No live matches currently available.")

elif page == "Player Stats":  # test

    import requests
    import streamlit as st

    # RapidAPI configuration
    API_KEY = "2454e52ef7msha9ad8a68de89ea1p1b4c51jsn18b293bbd472"
    API_HOST = "cricbuzz-cricket.p.rapidapi.com"

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }

    # Function to call API
    def fetch_api(endpoint, params=None):
        try:
            url = f"https://{API_HOST}/{endpoint}"
            response = requests.get(url, headers=headers, params=params)
            return response.json()
        except Exception as e:
            st.error(f"API Error: {e}")
            return None


    # Streamlit UI
    st.title("🏏 Cricket Player Dashboard")

    player_name = st.text_input("Enter Player Name")

    if st.button("Search Player"):

        if player_name.strip() == "":
            st.warning("Please enter a player name")
            st.stop()

        # STEP 1: Search player
        search_data = fetch_api(
            "stats/v1/player/search",
            params={"q": player_name}
        )

        # Debug (optional)
        # st.json(search_data)

        if search_data and "player" in search_data and len(search_data["player"]) > 0:

            player_id = search_data["player"][0]["id"]

            st.success(f"Player Found (ID: {player_id})")

            # STEP 2: Get player profile
            info = fetch_api(f"stats/v1/player/{player_id}")

            if info:

                st.header(info.get("name", "N/A"))

                col1, col2 = st.columns([1,2])

                with col1:
                    if info.get("image"):
                        st.image(info.get("image"), width=200)

                with col2:
                    st.write("**Role:**", info.get("role","N/A"))
                    st.write("**Batting Style:**", info.get("bat","N/A"))
                    st.write("**Bowling Style:**", info.get("bowl","N/A"))
                    st.write("**International Team:**", info.get("intlTeam","N/A"))
                    st.write("**Birth Place:**", info.get("birthPlace","N/A"))
                    st.write("**Date of Birth:**", info.get("DoBFormat","N/A"))

                st.subheader("Teams Played")
                st.write(info.get("teams","N/A"))

                st.divider()

                # STEP 3: Career Stats
                career = fetch_api(f"stats/v1/player/{player_id}/career")

                if career and "values" in career:

                    st.subheader("🏏 Career Stats")

                    for format_data in career["values"]:
                        format_name = format_data.get("name")

                        st.markdown(f"### {format_name}")

                        for stat in format_data["values"]:
                            st.write(f"{stat['key']} : {stat['value']}")

        else:
            st.error("Player not found. Try another name.")

# elif page == "Player Stats":
#     st.title("🏆 Player Career Profile")
#     search_query = st.text_input("Search Player (e.g., Virat Kohli)", "Virat Kohli")
    
#     if search_query:
#         # Step 1: Search for Player to get ID
#         search_data = fetch_api("stats/v1/player/search", params={"name": search_query})
#         if search_data and search_data.get('player'):
#             p_id = search_data['player'][0]['id']
            
#             # Step 2: Get Personal Details & Career Stats
#             info = fetch_api(f"stats/v1/player/{p_id}")
#             career = fetch_api(f"stats/v1/player/{p_id}/career")
            
#             if info and career:
#                 st.header(f"👤 {info.get('name')}")
                
#                 # Layout for personal details
#                 c1, c2, c3 = st.columns(3)
#                 c1.write(f"**DOB:** {info.get('dateOfBirth')}")
#                 c2.write(f"**Height:** {info.get('height')}")
#                 c3.write(f"**Birth Place:** {info.get('birthPlace')}")
#                 st.write(f"**Teams Played for:** {info.get('teams')}")
                
#                 # Career Stats Tabs
#                 tab1, tab2 = st.tabs(["🏏 Batting Stats", "🥎 Bowling Stats"])
#                 with tab1:
#                     if 'values' in career:
#                         st.dataframe(pd.DataFrame(career['values']))
#                     else:
#                         st.write("Batting stats not available.")
#                 with tab2:
#                     st.write("Bowling career data is available in the career JSON object.")

elif page == "SQL Queries & Analytics":

    elif page == "SQL Queries & Analytics":

    st.title("📊 SQL Analytics")

    query_option = st.selectbox(
        "Select Analysis",
        [
            "Players Representing India",
            "Recent Matches (Last Few Days)"
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
        FROM public.recent_matches
        ORDER BY match_date DESC
        """
    }

    try:
        conn = get_db_connection()

        query = queries[query_option]

        df = pd.read_sql(query, conn)

        st.dataframe(df)

        conn.close()

    except Exception as e:
        st.error(f"Database Error: {e}")

elif page == "CRUD Operations":
    st.title("⚙️ Database CRUD")
    # with st.form("crud_form"):
    #     p_name = st.text_input("Player Name")
    #     action = st.selectbox("Action", ["Create", "Update", "Delete"])
    #     submitted = st.form_submit_button("Execute")
        
    #     if submitted:
    #         # Here you would add logic: cur.execute("INSERT INTO...")
    #         st.success(f"Action '{action}' simulated for {p_name}")

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