import argparse

from core.movie_api import MovieAPI
from core.movie_manager import MovieManager
from core.movie_main import MovieMain
from helpers.config import Config
from helpers.supabase_db import SupabaseDB

def initialize():
    config = Config('./config/config.yaml')
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
    args = parser.parse_args()

    _, _, manager, movies_api = initialize()

    def progress_callback(message):
        print(message)


    analyzer_main = MovieMain(movies_api, manager, progress_callback) 

    analyzer_main.analyze_movies(args.year, args.page, args.overwrite, args.clear_cache)



if __name__ == "__main__":
    main()