# gen_captions/logger_config.py

import logging
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from .config import LOG_LEVEL

# Create a logger for the gen_captions package
logger = logging.getLogger("gen_captions")
logger.setLevel(LOG_LEVEL)

# Common formatter for file logging
formatter = logging.Formatter(
    "%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s"
)

# Create a RichHandler for console output
rich_handler = RichHandler(show_path=False)
rich_handler.setLevel(LOG_LEVEL)
# By default, RichHandler uses its own stylized format, but we can still attach a formatter if needed:
# rich_handler.setFormatter(formatter)

# Create a rotating file handler to preserve logs
file_handler = RotatingFileHandler(
    "gen_captions.log", mode="a", maxBytes=10_485_760, backupCount=5
)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)

# Replace any existing handlers
logger.handlers = []
logger.addHandler(rich_handler)
logger.addHandler(file_handler)

# import logging
# from logging.handlers import RotatingFileHandler
# from .constants import LOG_LEVEL

# # Configure logging
# logging.basicConfig(
#     format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
#     level=LOG_LEVEL,
# )
# logger = logging.getLogger(__name__)
# logger.setLevel(LOG_LEVEL)

# formatter = logging.Formatter("%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s")

# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)

# file_handler = RotatingFileHandler("gen_captions.log", mode="a", maxBytes=10485760, backupCount=5)
# file_handler.setFormatter(formatter)

# #logger.addHandler(console_handler)
# logger.addHandler(file_handler)
