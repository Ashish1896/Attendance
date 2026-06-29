import streamlit as st
from supabase import create_client, Client

# Load credentials from Streamlit secrets (works both locally and on Streamlit Cloud)
SUPABASE_URL: str = st.secrets["SUPABASE_URL"]
SUPABASE_KEY: str = st.secrets["SUPABASE_SECRET_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
