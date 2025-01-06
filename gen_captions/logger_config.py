"""A module to configure the logger for the gen_captions package.

This module contains a class that configures the logger for the
gen_captions.
"""
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from .config import Config


class CustomLogger:
    """A class to configure the logger for the gen_captions package."""

    def __init__(
        self,
        config: Config,
        name=__name__,
        console: Optional[Console] = None,
    ):
        """Initialize the logger configuration."""
        self._console = console
        self._config = config
        self._logger = logging.getLogger(name)
        self._logger.setLevel(config.LOG_LEVEL)

        formatter = logging.Formatter(
            "%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s"
        )

        file_handler = RotatingFileHandler(
            "gen_captions.log",
            mode="a",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        if self._console:
            console_handler = RichHandler(console=self._console)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

    def get_logger(self):
        """Return the configured logger."""
        return self._logger
