import streamlit as st
import pandas as pd

from Home import init

from scripts.core.movie_manager import Tables

st.title("🚀 Dashboard")

if 'db' not in st.session_state:
    init()
db = st.session_state.db.client

# Getting data
data_movies = db.table(Tables.MOVIES).select('*', count='exact').execute()
data_result_tests = db.table(Tables.RESULT_TEST).select('*, tests(name)', count='exact').execute()
data_genres = db.table(Tables.GENRES).select('*', count='exact').execute()

movies_df = pd.DataFrame(data_movies.data)
result_tests_df = pd.DataFrame(data_result_tests.data)

# Processing data
result_tests_df = pd.concat([result_tests_df, result_tests_df['tests'].apply(pd.Series)], axis=1)
result_tests_df = result_tests_df.rename(columns={'name': 'test_name'})


# General metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Movies", value=data_movies.count)
with col2:
    st.metric(label="Total Tests", value=data_result_tests.count)
with col3:
    st.metric(label="Total Genres", value=data_genres.count)

# Movies by year
movies_by_year = movies_df.groupby('year').size().reset_index(name='count')

st.subheader("Movies by Year")
st.bar_chart(movies_by_year.set_index('year'))



# Results metrics
result_counts = result_tests_df['result'].value_counts(dropna=False)

st.subheader("Tests Results")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Passed", value=result_counts.get(True, 0))
with col2:
    st.metric(label="Failed", value=result_counts.get(False, 0))
with col3:
    st.metric(label="Incomplete", value=result_counts.get(None, 0))


# Results by test
result_tests_df['result'] = result_tests_df['result'].astype(str)
results_by_tests = result_tests_df.groupby(['test_name', 'result']).size().unstack(fill_value=0)
results_by_tests = results_by_tests.rename(columns={
    'True': 'Passed',
    'False': 'Failed',
    'None': 'Incomplete'
})
results_by_tests = results_by_tests[['Passed', 'Failed', 'Incomplete']]

st.subheader("Results by Test")
st.bar_chart(results_by_tests)
