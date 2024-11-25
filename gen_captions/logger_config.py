# gen_captions/logger_config.py

import logging
from .constants import LOG_LEVEL

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
    level=LOG_LEVEL,
)
logger = logging.getLogger(__name__)
