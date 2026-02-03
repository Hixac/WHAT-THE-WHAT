import os
import logging
from logging.handlers import RotatingFileHandler

import structlog

from src.core.config import settings


LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")


file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10485760, backupCount=5)

logging.getLogger("").addHandler(file_handler)
logging.getLogger("").setLevel(settings.LOG_LEVEL)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper("%d-%m-%Y %H:%M:%S"),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.ExceptionPrettyPrinter(),
        structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True
)


logger = structlog.get_logger()
