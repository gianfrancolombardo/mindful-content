import datetime
import yaml
import time

from movie_analyzer import MovieAnalyzer
from firebase_db import FirebaseDB
from movie_api import MovieAPI
from config import Config
from logger import Logger

def save_initial_tests():
    """ Save the initial tests to the database. """
    logger.info('Starting to save initial tests...')

    with open('./config/tests.yaml', 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

        for item in data:
            existing_document = db.read_document_by_property('tests', 'name', item['name'])
            if not existing_document:
                db.create_document('tests', item, str(item['id']))
                logger.info(f'Test "{item["name"]}" created successfully!')

def main():
    logger.info('Starting to analyze movies...')
    movies_api = MovieAPI(config.get('tmdb_api_token'))
    movies = movies_api.fetch_movies()
    
    tests_list = db.read_all_documents('tests', 'id')

    analyzer = MovieAnalyzer()

    for movie in movies[:2]:
        logger.info(f"{movie['title']}, {movie['year']}")

        if not config.get('overwrite_movies'):
            existing_document = db.read_document_by_property('movies', 'title', movie['title'])
            if existing_document:
                logger.info(f'\tMovie "{movie["title"]}" already exists in the database, so it was skipped')
                continue

        movie['tests'] = []
        for current_test in tests_list:
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

            movie['tests'].append(result)
            
        movie['created_at'] = datetime.datetime.now()

        try:
            existing_document = db.read_document_by_property('movies', 'title', movie['title'])
            if not existing_document:
                db.create_document('movies', movie)
                logger.info(f'\tMovie "{movie["title"]}" created successfully!')
            else:
                db.update_document('movies', 'title', movie['title'], movie)
                logger.info(f'\tMovie "{movie["title"]}" already exists in the database, so it was updated')
        except Exception as e:
            logger.error(f'\tError creating or updating movie "{movie["title"]}": {str(e)}')


if __name__ == "__main__":
    
    config = Config('./config/config.yaml')

    db = FirebaseDB(config.get('firebase_config_path'))
    
    logger = Logger().get_logger()

    logger.info('-'*50)
    logger.info('-'*14 + ' Starting the script ' + '-'*15)
    logger.info('-'*14 + f' {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ' + '-'*15)
    logger.info('-'*50)

    if config.get('initailize_tests'):
        save_initial_tests()

    #main()