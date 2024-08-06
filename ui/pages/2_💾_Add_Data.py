import streamlit as st

from scripts.core.movie_main import MovieMain

st.title("💾 Scan, analyze and save movies")

with st.form("year_page_form"):
    year = st.number_input("Year", min_value=1900, max_value=2021, step=1, value=2021)
    page = st.number_input("Page", min_value=1, step=1, value=1)
    overwrite_movies = st.checkbox("Overwrite movies", value=False)
    clear_cache = st.checkbox("Clear cache", value=False)
    submit_button = st.form_submit_button("Analyze movies")

if submit_button:
    with st.status(f"Scanning and analyzing movies for year {year} and page {page}...", expanded=True) as status:
        
        movies_api = st.session_state.api 
        manager = st.session_state.manager
        config = st.session_state.config

        def progress_callback(message):
            st.write(message)

        analyzer_main = MovieMain(movies_api, manager, progress_callback)
        movies = analyzer_main.analyze_movies(year, page, overwrite_movies, clear_cache)
        
        status.update(label=f"{len(movies)} movies analyzed and saved!", state="complete", expanded=False)

