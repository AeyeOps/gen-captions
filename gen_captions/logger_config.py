"""Module for logger configuration used in gen_captions."""

import logging
import os
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler

from concurrent_log_handler import ConcurrentRotatingFileHandler

try:
    from concurrent_log_handler.queue import setup_logging_queues
except ModuleNotFoundError:  # pragma: no cover - optional API
    setup_logging_queues = None
from rich.logging import RichHandler


class DateTimeLogFilter(logging.Filter):
    """Attach an ISO-like UTC timestamp to each log record."""

    # pylint: disable=too-few-public-methods

    def filter(self, record):
        """Populate the record with a millisecond-precision timestamp."""
        record.date_time = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]
        return True


class ThreadLogFilter(logging.Filter):
    """Annotate log records with the current thread identifier."""

    # pylint: disable=too-few-public-methods

    def filter(self, record):
        """Store the worker thread id on the record."""
        record.thread = threading.get_ident()
        return True


class CustomLogFormatter(logging.Formatter):
    """Render log records in a single-line structured format."""

    def format(self, record):
        """Format the log record with timestamp, process, thread, and scope."""
        message = record.getMessage()
        return (
            f"[{record.date_time}][0x{record.process:04x}]"
            f"[0x{record.thread:04x}][{record.levelname:>8}]"
            f"[{record.module}::{record.funcName}] {message}"
        )


class CustomLogger:
    """Configure a Rich-aware logger with rotating file support."""

    def __init__(
        self,
        name=__name__,
        console=None,
        concurrent=True,
        level=logging.DEBUG,
    ):
        """Initialise the wrapped logger and attach a default handler."""
        self._console = console
        self._log = logging.getLogger(name=name)
        self._log.setLevel(level)
        self._basefile = name + ".log"
        self._file = os.path.join(os.getcwd(), self._basefile)
        self.add_log_handler(self._file, concurrent)

    @staticmethod
    def create_file_handler(file, concurrent=True):
        """Construct a rotating handler with the shared formatter."""
        if concurrent:
            handler = ConcurrentRotatingFileHandler(
                filename=file,
                mode="a",
                maxBytes=1024 * 1024 * 10,
                backupCount=10,
                encoding="utf-8",
                use_gzip=True,
            )

        else:
            handler = RotatingFileHandler(
                filename=file,
                mode="a",
                maxBytes=1024 * 1024 * 10,
                backupCount=10,
                encoding="utf-8",
            )

        handler.setFormatter(CustomLogFormatter())
        handler.addFilter(DateTimeLogFilter())
        handler.addFilter(ThreadLogFilter())
        return handler

    def clear_log_handlers(self):
        """Remove every handler currently attached to the logger."""
        for handler in self._log.handlers:
            self._log.removeHandler(handler)

    def add_log_handler(self, file, concurrent=True):
        """Attach a new handler and enable queue-backed logging."""
        # for now let's stick to a single log handler
        self.clear_log_handlers()

        if file:
            handler = self.create_file_handler(file, concurrent)
            self._file = os.fspath(file)
            self._basefile = os.path.abspath(self._file)
        else:
            # handler = logging.StreamHandler()
            handler = RichHandler()

        handler.setFormatter(CustomLogFormatter())
        handler.addFilter(DateTimeLogFilter())
        handler.addFilter(ThreadLogFilter())
        self._log.addHandler(handler)

        # To use the background logging queue, works well in
        # multi-threaded and multi-process concurrent environments.
        # Important for all writers to a given log file to use the same
        # class and the same settings at the same time
        if setup_logging_queues:
            setup_logging_queues()

    # getter property for the self.log
    @property
    def logger(self):
        """Return the configured logger instance."""
        return self._log
