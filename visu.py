import streamlit as st  
import pandas as pd
import psycopg2

# 1. Establish the connection
conn = psycopg2.connect(
    host='localhost',
    database='cricbuzz',
    user='postgres',
    password='deepika@88',
    port=5432
)

# 2. Create a cursor object (this executes your SQL)
cur = conn.cursor()
st.title("Cricbuzz Live states")

st.sidebar.header("header")
st.subheader("sub")
st.text("give some text here")
st.markdown("Here is another one: :crescent_moon:")
st.write("The moon is bright tonight :moon:")
st.header("Night Mode 🌕")
st.markdown(
    """
# h1 tag
## h2tag
### h3 tag

### Tonight's Sky
The moon is bright tonight :full_moon:
:sunglasses:


"""
)