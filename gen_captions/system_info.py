# gen_captions/system_info.py

import platform
import os
from .logger_config import logger


def print_system_info():
    """Print system information and environment variable settings."""
    logger.info("\r\n" * 2)
    logger.info("System Information:")
    logger.info(f"Platform: {platform.system()}")
    logger.info(f"Platform Version: {platform.version()}")
    logger.info(f"Platform Release: {platform.release()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info(f"Python Version: {platform.python_version()}")

    logger.info("Environment Variable Settings:")
    for key, value in os.environ.items():
        if key.startswith("GETCAP_"):
            logger.info(f"{key}: {value}")
    logger.info("\r\n" * 2)
