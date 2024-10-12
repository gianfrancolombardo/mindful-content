import pandas as pd
import streamlit as st

from Home import init

from scripts.core.movie_manager import Tables

if 'db' not in st.session_state:
    init()
db = st.session_state.db.client
base_url_image = 'https://image.tmdb.org/t/p/w500/'

manager = st.session_state.manager

def search_movie(query):
    try:
        result = db.table(Tables.MOVIES).select('*, genres(*), result_test(*, tests(name, objective))').match({'id': query}).eq('result_test.active', True).single().execute()
        return result.data
    except Exception as e:
        print("Error searching movie", e)
        return None

st.title("🎬 Movie Details")

query = st.text_input("Search movie by ID", value=38700)
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    search_button = st.button("🔍 Search", use_container_width=True)
with col3:
    delete_button = st.button("🗑️ Delete Movie and all tests", type="primary", use_container_width=True)


if search_button:
    movie = search_movie(query)

    if movie:

        st.header(f"[{movie['title']} ({movie['year']})](https://www.themoviedb.org/movie/{movie['id']}?language=es)")
        

        # Details ----------------------------------------------------------- *
        col1, col2 = st.columns(2)
        with col1:
            st.image(base_url_image + movie['poster_path'], 
                    caption=movie['title'], 
                    use_column_width=True)
        
        with col2:
            st.subheader("Details")
            st.write(f"Release date: **{movie['release_date']}**")
            st.write(f"TMDb: **{movie['tmdb_score']}**")
            st.write(f"Our score: **{movie['our_score']}**")
            st.write(f"Genres: **{', '.join([genre['name'] for genre in movie['genres']])}**")
            created_at = pd.to_datetime(movie['created_at'])
            formatted_created_at = created_at.strftime("%Y-%m-%d")
            st.write(f"Created at: **{formatted_created_at}**")
        
            st.subheader("Backdrop")
            st.image(base_url_image + movie['backdrop_path'], use_column_width=True)


        # Summary ----------------------------------------------------------- *
        st.subheader("Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"{movie['summary']}")
        with col2:
            st.write(f"{movie['summary_es']}")
        st.divider()

        st.subheader("Tests")


        # Test metrics -------------------------------------------------------- *
        tests_data = sorted(movie['result_test'], key=lambda x: x['test_id'])
        result_tests_df = pd.DataFrame(tests_data)
        if result_tests_df.empty:
            st.info("No tests found.")
        else:
            result_counts = result_tests_df['result'].value_counts(dropna=False)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Passed", value=result_counts.get(True, 0))
            with col2:
                st.metric(label="Failed", value=result_counts.get(False, 0))
            with col3:
                st.metric(label="Incomplete", value=result_counts.get(None, 0))
            st.divider()
            

            for test in tests_data:
                with st.container():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**{test['tests']['name']}**")
                    with col2:
                        result_emoji = ":large_green_circle:" if test['result'] else ":red_circle:" if test['result'] is not None else ":white_circle:"
                        st.markdown(f"### {result_emoji}")
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        st.write(f"**{test['reason']}**")
                    with col4:
                        st.write(f"**{test['reason_es']}**")
                    
                    st.write(f"Execution time: **{int(test['execution_time'])} seconds**")
                    st.divider()

    else:
        st.error("Movie not found")


if delete_button:
    st.toast("Deleting movie...", icon="⏳")
    result = manager.delete_movie(query)
    if result == True:
        st.toast(f"Deleted movie", icon="✅")
        st.rerun()
    else:
        st.toast(f"Error deleting movie: {result}", icon="⚠️")