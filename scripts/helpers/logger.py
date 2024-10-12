import logging
from datetime import datetime
import os

class Logger:
    def __init__(self, log_file_prefix='app'):
        log_file = self._generate_log_file_name(log_file_prefix)
        self._create_log_dir(log_file)
        self._setup_logging(log_file)

    def _generate_log_file_name(self, prefix):
        date_str = datetime.now().strftime('%Y-%m-%d')
        return f"./logs/{prefix}_{date_str}.log"
    
    def _create_log_dir(self, log_file):
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def _setup_logging(self, log_file):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger(__name__)
        # self.logger.info("Logging is set up")
        
        httpx_logger = logging.getLogger("httpx")
        httpx_logger.setLevel(logging.WARNING)

    def get_logger(self):
        return self.logger