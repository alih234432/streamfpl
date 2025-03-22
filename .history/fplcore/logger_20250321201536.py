import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/fpl_chatbot_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

# Create logger
logger = logging.getLogger('fpl_chatbot')

def log_info(message):
    """Log an informational message"""
    logger.info(message)

def log_error(message):
    """Log an error message"""
    logger.error(message)

def log_warning(message):
    """Log a warning message"""
    logger.warning(message)

def log_debug(message):
    """Log a debug message"""
    logger.debug(message)

def log_exception(e):
    """Log an exception with traceback"""
    logger.exception(f"Exception occurred: {str(e)}")

def get_logger():
    """Get the logger instance"""
    return logger