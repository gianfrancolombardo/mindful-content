import streamlit as st

from Home import init

from scripts.core.movie_analyzer import MovieAnalyzer
from scripts.core.movie_manager import Tables

if 'db' not in st.session_state:
    init()
db = st.session_state.db.client
manager = st.session_state.manager 
analyzer = MovieAnalyzer()
total_tests = 0

st.title("🔄 Update Data")


with st.form("update_test_form"):
    st.write("Update the tests' result of movies that have result Incomplete")
    update_tests_btn = st.form_submit_button("Update Incomplete tests")

if update_tests_btn:
    with st.status(f"Updating tests' results...", expanded=True) as status:
        
        # Get all movies and tests with result None
        st.write("Fetching movies from DB...")
        data_movies = db.table(Tables.MOVIES).select('*, result_test(*, tests(id, name))').is_('result_test.result', 'null').eq('result_test.active', True).execute()

        for movie in data_movies.data:
            st.write(f"Analyzing: {movie['title']}({movie['year']}) - {movie['id']}")
            
            for test in movie['result_test']:
                if test['result'] is None:
                    st.write(f"__ Running test: {test['tests']['name']}")

                    result = manager.create_results(analyzer, movie, test['tests'])
                    print(result)
                    result['id'] = test['id']
                    manager.save_results(result)

                    total_tests += 1

    status.update(label=f"Re-analyzed {total_tests} for {len(data_movies.data)} movies!", state="complete", expanded=True)





with st.form("update_translation_form"):
    st.write("Update the translation of the tests' result")
    update_transtation_btn = st.form_submit_button("Update transtations")

if update_transtation_btn:
    with st.status(f"Updating reason test to Spanish...", expanded=True) as status:
        
        # Get all movies and tests with result None
        st.write("Fetching results from DB...")
        data_results = db.table(Tables.RESULT_TEST).select('*').is_('reason_es', 'null').eq('active', True).execute()
        st.write(f"{len(data_results.data)} results will be updated.")


        for result in data_results.data:
            st.write(f"Updating movie {result['movie_id']}, result {result['id']}")
            
            result['reason_es'] = manager.translate_result(analyzer, result['reason'])
            manager.save_results(result)

    status.update(label=f"Updated translation of {len(data_results.data)} result!", state="complete", expanded=True)






with st.form("update_summary_form"):
    st.write("Update summary of movies")
    update_summary_btn = st.form_submit_button("Update summary")

if update_summary_btn:
    with st.status(f"Updating summary of movies...", expanded=True) as status:
        
        # Get all movies with summary None
        st.write("Fetching movies from DB...")
        #data_movies = db.table(Tables.MOVIES).select('*').is_('summary', 'null').execute()
        data_movies = db.table(Tables.MOVIES).select('*').execute()
        st.write(f"{len(data_movies.data)} movies will be updated.")
        
        for movie in data_movies.data:
            st.write(f"Updating movie {movie['id']}")

            result_test = db.table(Tables.RESULT_TEST).select('*, tests(name, objective)').eq('movie_id', movie['id']).execute()
            movie_isolate = {
                "id": movie['id'],
                "title": movie['title'],
                "year": movie['year'],
                "result_test": result_test.data
            }
            
            manager.create_summary(analyzer, movie_isolate)
            
    status.update(label=f"Updated summry of {len(data_movies.data)} movies!", state="complete", expanded=True)