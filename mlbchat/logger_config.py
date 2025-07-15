# logger_config.py
import logging
import sys

def setup_logging():
    # Configure the root logger or a specific named logger
    logger = logging.getLogger('mlbchat')  # Use a consistent name
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers if setup_logging is called multiple times
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Error handler
    error_handler = logging.FileHandler('mlbchat_errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Info handler with filter
    info_handler = logging.FileHandler('mlbchat_info.log')
    info_handler.setLevel(logging.DEBUG)
    info_handler.setFormatter(formatter)
    
    class InfoFilter(logging.Filter):
        def filter(self, record):
            return record.levelno < logging.ERROR
    
    info_handler.addFilter(InfoFilter())
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(error_handler)
    logger.addHandler(info_handler)
    logger.addHandler(console_handler)
    
def get_logger(name=None):
    if name is None:
        name = 'mlbchat'
    return logging.getLogger(name)
