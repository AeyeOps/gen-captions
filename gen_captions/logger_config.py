import logging
import os
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler

from concurrent_log_handler import ConcurrentRotatingFileHandler
from concurrent_log_handler.queue import setup_logging_queues
from rich.logging import RichHandler


class DateTimeLogFilter(logging.Filter):
    def filter(self, record):
        record.date_time = datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]
        return True


class ThreadLogFilter(logging.Filter):
    def filter(self, record):
        record.thread = threading.get_ident()
        return True


class CustomLogFormatter(logging.Formatter):
    def format(self, record):
        return (
            f"[{record.date_time}][0x{record.process:04x}][0x{record.thread:04x}]"
            + f"[{record.levelname:>8}][{record.module}::{record.funcName}] {record.msg}"
        )


class CustomLogger:
    def __init__(
        self,
        name=__name__,
        console=None,
        concurrent=True,
        level=logging.DEBUG,
    ):
        self._console = console
        self._log = logging.getLogger(name=name)
        self._log.setLevel(level)
        self._basefile = name + ".log"
        self._file = os.path.join(os.getcwd(), self._basefile)
        self.add_log_handler(self._file, concurrent)

    def create_file_handler(self, file, concurrent=True):
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
        for handler in self._log.handlers:
            self._log.removeHandler(handler)

    def add_log_handler(self, file, concurrent=True):
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
        setup_logging_queues()

    # getter property for the self.log
    @property
    def logger(self):
        return self._log


# import logging
# from logging.handlers import RotatingFileHandler
# from .config import Config

# # Configure logging
# logging.basicConfig(
#     format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
#     level=Config.LOG_LEVEL,
# )
# logger = logging.getLogger(__name__)
# logger.setLevel(Config.LOG_LEVEL)

# formatter = logging.Formatter("%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s")

# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)

# file_handler = RotatingFileHandler("gen_captions.log", mode="a", maxBytes=10485760, backupCount=5)
# file_handler.setFormatter(formatter)

# logger.addHandler(console_handler)
# logger.addHandler(file_handler)
