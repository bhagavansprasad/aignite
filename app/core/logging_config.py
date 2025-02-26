# app/core/logging_config.py

import logging
import logging.config
import os

# Define log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# Default log level
DEFAULT_LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
LOGGING_LEVEL = LOG_LEVELS.get(DEFAULT_LOG_LEVEL, logging.DEBUG)  # Fallback to INFO

# Define log directory
LOG_DIR = "logs" # same folder

# Create logs directory if it doesn't exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Define logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            # 'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            'format': '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': LOGGING_LEVEL,
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'level': LOGGING_LEVEL,
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,  # Rotate through 10 files
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': LOGGING_LEVEL,
            'propagate': True,
        },
        'app': {  # App-specific logger
            'handlers': ['console', 'file'],
            'level': LOGGING_LEVEL,
            'propagate': False,  # Prevent double logging
        },
    },
}

def configure_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
