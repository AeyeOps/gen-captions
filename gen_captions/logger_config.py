# gen_captions/logger_config.py

import logging
from logging.handlers import RotatingFileHandler
from .constants import LOG_LEVEL

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
    level=LOG_LEVEL,
)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

formatter = logging.Formatter("%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

file_handler = RotatingFileHandler("gen_captions.log", mode="a", maxBytes=10485760, backupCount=5)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
