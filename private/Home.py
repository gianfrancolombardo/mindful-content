import streamlit as st


import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from scripts.core.movie_api import MovieAPI
from scripts.core.movie_manager import MovieManager, Tables

from scripts.helpers.config import Config
from scripts.helpers.supabase_db import SupabaseDB
import pandas as pd

def main():
    st.set_page_config(page_title="Mindful Content Backoffice", page_icon=":clapper:")

    st.title("🎬 Mindful Content Backoffice")
    st.write("Symbolic narrative analyzer with AI to detect bias")


def init():
    if 'config' not in st.session_state:
        st.session_state.config = Config('../scripts/config/config.yaml')
    if 'db' not in st.session_state:
        st.session_state.db = SupabaseDB(
            st.session_state.config.get('supabase_url'), 
            st.session_state.config.get('supabase_key'))
    if 'api' not in st.session_state:
        st.session_state.api = MovieAPI(
            st.session_state.config.get('tmdb_api_token'))
    if 'manager' not in st.session_state:
        st.session_state.manager = MovieManager(
            st.session_state.api, 
            st.session_state.db)

if __name__ == "__main__":
    init()
    main()