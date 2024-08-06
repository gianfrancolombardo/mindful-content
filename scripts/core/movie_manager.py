

import datetime
from enum import Enum
import time
from typing import Dict

from core.movie_api import MovieAPI

from helpers.supabase_db import SupabaseDB

class Tables(Enum):
    MOVIES = 'movies'
    GENRES = 'genres'
    TESTS = 'tests'
    MOVIES_GENRES = 'movies_genres'
    RESULT_TEST = 'result_test'

    def __str__(self):
        return self.value


class MovieManager:

    def __init__(self, api: MovieAPI, db: SupabaseDB) -> None:
        """Initialize the MovieManager with the given API and database."""
        self.api = api
        self.db = db

    

    def get_tests(self) -> Dict[str, str]:
        """Read all tests from the database."""
        return self.db.read(Tables.TESTS, order_by='id')

    def get_movie(self, movie_id: str) -> Dict[str, str]:
        """Read a movie from the database by its ID."""
        result = self.db.read(Tables.MOVIES, {'id': movie_id})
        return result[0] if result else None
    
    def get_total(self, table: str) -> int:
        """Get the total number of a table in the database."""
        data = self.db.raw(table, "count(*)").execute()
        total_movies = data.data[0]["count"] if data else 0
        return total_movies

    def set_tests_inactive(self, movie_id: str) -> int:
        """Set all tests inactive for a movie."""
        return self.db.update(Tables.RESULT_TEST, {'movie_id': movie_id}, {'active': False})

    def save_movie(self, movie: Dict[str, str]) -> None:
        """Save the movie to the database."""

        # Fetching movie details
        movie_detail = self.api.fetch_movie_details(movie['id'])
        
        # Saving genres
        genres = movie_detail.get('genres', [])
        for genre in genres:
            self.save_genres(genre)

        # Saving movie
        movie['created_at'] = datetime.datetime.now().isoformat()
        movie['tmdb_score'] = movie.pop('vote_average')
        movie['imdb_id'] = movie_detail.get('imdb_id', None)
        self.db.create_or_update(Tables.MOVIES, movie)

        # Saving movie-genre relationship
        for genre in genres:
            self.db.create_or_update(Tables.MOVIES_GENRES, {'movie_id': movie['id'], 'genre_id': genre['id']})

        return movie

    def save_genres(self, genre: Dict[str, str]) -> None:
        """Save the genres of the movie to the database."""
        try:
            existing_obj = self.db.read(Tables.GENRES, {'id': genre['id']})
            if not existing_obj:
                self.db.create_or_update(Tables.GENRES, genre)
                
        except Exception as e:
            print(f"Error saving genre: {str(e)}")

    def create_results(self, analyzer, movie: Dict[str, str], test: Dict[str, str]) -> None:
        """Save the results of the tests to the database."""

        start_time = time.time()
        result = analyzer.run(movie['title'], movie['year'], test['name'], test['objective'])
        end_time = time.time()
        
        result['test_id'] = test['id']
        result['execution_time'] = end_time - start_time

        # Translate the result
        if 'reason_es' not in result:
            result['reason_es'] = self.translate_result(analyzer, result['reason'])
        
        result['movie_id'] = movie['id']
        result['active'] = True

        return result

    def save_results(self, result: Dict[str, str]) -> None:
        """Save the results of the tests to the database."""
        return self.db.create_or_update(Tables.RESULT_TEST, result)
    
    def translate_result(self, analyzer, reason: str) -> str:
        """Translate the result to Spanish."""
        try:
            reason_es = analyzer.translate(reason, 'Spanish')
            if 'translated' in reason_es:
                reason_es = reason_es['translated']
        except Exception as e:
            reason_es = None
        return reason_es
    
    def create_summary(self, analyzer, movie):
        """ Generate and translate summary movie. """

        movie_to_update = {}
        movie_to_update['summary'] = analyzer.summary(movie)
        if movie_to_update['summary']:
            try:
                
                translated = analyzer.translate(movie_to_update['summary'], 'Spanish')
                if 'translated' in translated:
                    movie_to_update['summary_es'] = translated['translated']
            except Exception as e:
                movie_to_update['summary_es'] = None

            movie_to_update['our_score'] = self.calculate_score(movie)

            self.db.update(Tables.MOVIES, {'id': movie['id']}, movie_to_update)

    def calculate_score(self, movie) -> int:
        """ Calculate percentage of passed test. """

        total_tests = len(movie['result_test'])
        if total_tests == 0:
            return 0.0 
        
        true_results = sum(1 for test in movie['result_test'] if test['result'] is True)
        score_percentage = (true_results / total_tests) * 100
        
        return int(score_percentage)