import datetime
import yaml
import time

from movie_analyzer import MovieAnalyzer
from movie_api import MovieAPI
from config import Config
from logger import Logger
from supabase_db import SupabaseDB

def save_initial_tests():
    """ Save the initial tests to the database. """
    logger.info('Starting to save initial tests...')

    with open('./config/tests.yaml', 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

        for item in data:
            existing_document = db_supabase.read('tests', {'id': item['id']})
            if not existing_document:
                db_supabase.create('tests', item)
                logger.info(f'Test "{item["name"]}" created successfully!')

def main():
    logger.info('Starting to analyze movies...')
    movies_api = MovieAPI(config.get('tmdb_api_token'))
    movies = movies_api.fetch_movies()
    
    tests_list = db_supabase.read('tests', order_by='id')

    analyzer = MovieAnalyzer()

    for movie in movies[:2]:
        logger.info(f"{movie['title']}, {movie['year']}")

        existing_movie = db_supabase.read('movies', {'id': movie['id']})
        if not config.get('overwrite_movies'):
            if existing_movie:
                logger.info(f'\tMovie "{movie["title"]}" already exists in the database, so it was skipped')
                continue
        
        movie['created_at'] = datetime.datetime.now().isoformat()

        if not existing_movie:
            db_supabase.create('movies', movie)
        
        
        for current_test in tests_list[:3]:
            logger.info(f"\tRunning test: {current_test['name']}")
            start_time = time.time()
            result = analyzer.run(movie['title'], movie['year'], current_test['name'])
            end_time = time.time()
            
            result['test_id'] = current_test['id']
            result['execution_time'] = end_time - start_time

            # Translate the result
            if 'reason_es' not in result:
                try:
                    result['reason_es'] = analyzer.translate(result['reason'], 'Spanish')
                except Exception as e:
                    logger.error(f'\tError translating the result to Spanish: {str(e)}')
                    result['reason_es'] = None
            
            result['movie_id'] = movie['id']
            db_supabase.create('result_test', result)





if __name__ == "__main__":
    
    config = Config('./config/config.yaml')

    db_supabase = SupabaseDB(config.get('supabase_url'), config.get('supabase_key'))

    logger = Logger().get_logger()

    logger.info('-'*50)
    logger.info('-'*14 + ' Starting the script ' + '-'*15)
    logger.info('-'*14 + f' {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ' + '-'*15)
    logger.info('-'*50)

    if config.get('initailize_tests'):
        save_initial_tests()

    main()