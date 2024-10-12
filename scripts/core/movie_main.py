import datetime
from typing import List, Dict, Any

from scripts.core.movie_analyzer import MovieAnalyzer
from scripts.core.movie_api import MovieAPI
from scripts.core.movie_manager import MovieManager
from scripts.helpers.logger import Logger

class MovieMain:
    def __init__(self, movies_api: MovieAPI, manager: MovieManager, analyzer: MovieAnalyzer = None, log_callback = None):
        self.movies_api = movies_api
        self.manager = manager
        self.analyzer = MovieAnalyzer() if analyzer is None else analyzer
        self.logger = Logger().get_logger()
        self.log_callback = log_callback
        self.lang = 'es-ES'

    def analyze_movies(self, year: int, page: int, overwrite_movies: bool, clear_cache: bool) -> List[Dict[str, Any]]:
        """Get movies from the API, analyze them and save the results."""
        
        self.log_start()
        
        movies = self.fetch_movies(year, page)
        tests_list = self.manager.get_tests()
        
        if clear_cache:
            self.analyzer.clear_cache()
            self.log("Cache cleared")

        analyzed_movies = []
        for movie in movies:
            analyzed_movie = self.process_movie(movie, overwrite_movies, tests_list)
            if analyzed_movie:
                analyzed_movies.append(analyzed_movie)

        self.log(f"{len(analyzed_movies)} movies analyzed and saved!")
        return analyzed_movies


    def analyze_single_movie(self, movie_id: str, overwrite_movies: bool) -> Dict[str, Any]:
        """Get a single movie from the API, analyze it and save the results."""
        
        movie = self.movies_api.fetch_movie_details(movie_id, lang=self.lang, raw=False)
        return self.process_movie(movie, overwrite_movies, self.manager.get_tests())


    def fetch_movies(self, year: int, page: int) -> List[Dict[str, Any]]:
        """Fetch movies from the API."""

        self.log("Fetching movies from API...")
        return self.movies_api.fetch_movies(year=year, page=page, lang=self.lang)


    def process_movie(self, movie: Dict[str, Any], overwrite_movies: bool, tests_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a movie by analyzing it and saving the results."""

        self.log(f"Analyzing: {movie['title']}({movie['year']}) - {movie['id']}")
        
        existing_movie = self.manager.get_movie(movie['id'])
        if not overwrite_movies and existing_movie:
            self.log(f'\tAlready exists in the database, so it was skipped')
            return None
        
        if overwrite_movies or not existing_movie:
            movie = self.manager.save_movie(movie)

        self.manager.set_tests_inactive(movie['id'])
        
        results_test = self.run_tests(movie, tests_list)
        if results_test is None:
            self.log(f"\tNo info in the model, so it was skipped")
            return None
        
        movie['result_test'] = results_test
        
        self.log(f"\tGenerating summary")
        self.manager.create_summary(self.analyzer, movie)
        
        return movie

    def run_tests(self, movie: Dict[str, Any], tests_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run the tests for a movie."""

        results_test = []
        for current_test in tests_list:
            try:
                self.log(f"\tRunning test: {current_test['name']}")
                result = self.manager.create_results(self.analyzer, movie, current_test)

                # Check if there is info
                if result['result'] is None:
                    # Delete movie because there is info in the model
                    self.manager.delete_movie(movie['id'])
                    return None

                self.manager.save_results(result)
                
                result['tests'] = current_test
                results_test.append(result)
            except Exception as e:
                self.log(f"\tError running test: {current_test['name']}. Error: {e}")
        return results_test

    def log_start(self):
        """Log the start of the script."""

        self.log('-'*50, False)
        self.log('-'*14 + ' Starting the script ' + '-'*15, False)
        self.log('-'*14 + f' {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ' + '-'*15, False)
        self.log('-'*50, False)

    def log(self, message: str, callback: bool = True):
        """Log a message."""

        self.logger.info(message)
        if self.log_callback and callback:
            self.log_callback(message)