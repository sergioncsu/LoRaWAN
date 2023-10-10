
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logger():
    if not logging.getLogger().hasHandlers():
        # Create a logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Create a file handler
        log_directory = 'logs'
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        log_file = os.path.join(log_directory, f'{datetime.now().strftime("%Y-%m-%d")}.log')
        file_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1)
        file_handler.suffix = '%Y-%m-%d.log'
        file_handler.setLevel(logging.INFO)

        # Create a stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)

        # Create a formatter that adds timestamps
        formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s', datefmt='%H:%M:%S')
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        # Add both handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

# Call the setup_logger function to configure the logger
setup_logger()
