import streamlit as st

from scripts.core.movie_main import MovieMain

st.title("💾 Scan, analyze and save movies")


# Add bulk movies ----------------------------------------------------------*
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


# Add single movie --------------------------------------------------------*
with st.form("movie_id_form"):
    movie_id = st.text_input("Movie ID", placeholder="Enter the movie ID")
    overwrite_movies = st.checkbox("Overwrite data", value=False)
    submit_movie_button = st.form_submit_button("Analyze movie by ID")

if submit_movie_button:
    if movie_id:
        with st.status(f"Analyzing movie with ID {movie_id}...", expanded=True) as status:
            
            movies_api = st.session_state.api
            manager = st.session_state.manager

            def progress_callback(message):
                st.write(message)

            analyzer_main = MovieMain(movies_api, manager, progress_callback)
            movie = analyzer_main.analyze_single_movie(movie_id, overwrite_movies)

            if movie:
                status.update(label=f"Movie with ID {movie_id} analyzed and saved!", state="complete", expanded=False)
            else:
                status.update(label=f"Not found info in the model!", state="error", expanded=False)
    else:
        st.warning("Please enter a valid Movie ID")