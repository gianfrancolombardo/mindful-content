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
results_by_tests = results_by_tests.reindex(columns=['Passed', 'Failed', 'Incomplete'], fill_value=0)
results_by_tests = results_by_tests[['Passed', 'Failed', 'Incomplete']]

st.subheader("Results by Test")
st.bar_chart(results_by_tests)


# List last movies with count of tests
st.subheader("Movies")
tests_count = result_tests_df.groupby('movie_id').size().reset_index(name='test_count')
movies_with_test_counts = pd.merge(movies_df[['id', 'title', 'created_at']], tests_count, left_on='id', right_on='movie_id', how='left')
movies_with_test_counts['test_count'] = movies_with_test_counts['test_count'].fillna(0).astype(int)
movies_with_test_counts['id'] = movies_with_test_counts['id'].astype(str)
movies_with_test_counts = movies_with_test_counts.sort_values(by='created_at', ascending=False)
movies_with_test_counts = movies_with_test_counts.rename(columns={
    'id': 'Movie ID',
    'title': 'Title',
    'test_count': 'Tests'
})

st.dataframe(movies_with_test_counts[['Movie ID', 'Title', 'Tests']], use_container_width=True)

# def make_clickable(val):
#     return f'<a href="/?movie_id={val}">{val}</a>'

# tests_count = result_tests_df.groupby('movie_id').size().reset_index(name='test_count')
# movies_with_test_counts = pd.merge(movies_df[['id', 'title', 'created_at']], tests_count, left_on='id', right_on='movie_id', how='left')
# movies_with_test_counts['test_count'] = movies_with_test_counts['test_count'].fillna(0).astype(int)
# movies_with_test_counts['id'] = movies_with_test_counts['id'].astype(str)
# movies_with_test_counts = movies_with_test_counts.sort_values(by='created_at', ascending=False)
# movies_with_test_counts = movies_with_test_counts.drop(columns=['created_at', 'movie_id'])
# movies_with_test_counts = movies_with_test_counts.rename(columns={
#     'id': 'Movie ID',
#     'title': 'Title',
#     'test_count': 'Tests'
# })
# movies_with_test_counts['Movie ID'] = movies_with_test_counts['Movie ID'].apply(make_clickable)

# st.markdown(
#     movies_with_test_counts.to_html(escape=False, index=False), 
#     unsafe_allow_html=True
# )
