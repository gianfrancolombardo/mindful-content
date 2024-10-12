import argparse

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'core')))

from scripts.core.movie_analyzer import MovieAnalyzer
from scripts.core.movie_api import MovieAPI
from scripts.core.movie_manager import MovieManager
from scripts.core.movie_main import MovieMain
from scripts.helpers.config import Config
from scripts.helpers.supabase_db import SupabaseDB

def initialize():
    config = Config('./scripts/config/config.yaml')
    db = SupabaseDB(config.get('supabase_url'), config.get('supabase_key'))
    movies_api = MovieAPI(config.get('tmdb_api_token'))
    manager = MovieManager(movies_api, db)
    return config, db, manager, movies_api

def main():
    parser = argparse.ArgumentParser(description="Scan, analyze and save movies")
    parser.add_argument("--year", type=int, default=2021, help="Year of movies to analyze")
    parser.add_argument("--page", type=int, default=1, help="Page number for API request")
    parser.add_argument("--overwrite", default=False, action="store_true", help="Overwrite existing movies")
    parser.add_argument("--clear-cache", default=False, action="store_true", help="Clear cache before analysis")
    parser.add_argument("--remote-llm", default=True, action="store_true", help="Use remote LLM")

    parser.add_argument("--movie-id", type=int, help="Movie ID to analyze")
    args = parser.parse_args()

    config, _, manager, movies_api = initialize()

    def progress_callback(message):
        print(message)

    if args.remote_llm:
        analyzer = MovieAnalyzer(
            api_key=config.get('openai_key'),
            base_url="https://api.openai.com/v1/",
            model="gpt-4o-mini"
        )
    else:
        analyzer = MovieAnalyzer()

    analyzer_main = MovieMain(movies_api, manager, analyzer, progress_callback) 

    if args.movie_id:
        analyzer_main.analyze_single_movie(args.movie_id, args.overwrite)
    else:
        analyzer_main.analyze_movies(args.year, args.page, args.overwrite, args.clear_cache)



if __name__ == "__main__":
    main()