"""Common logging package for authomize"""
import logging
import sys
from datetime import datetime
from typing import Any, Optional

from pythonjsonlogger import jsonlogger


def _log_wrapper(level: str) -> Any:
    def inner(func: Any) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if kwargs.get("extra") is None:
                kwargs["extra"] = {}

            kwargs["extra"]["time"] = datetime.utcnow().strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            kwargs["extra"]["level"] = level
            kwargs["extra"]["service_name"] = "authomize-sync"
            return func(*args, **kwargs)

        return wrapper

    return inner


def _exc_info() -> bool:
    if sys.exc_info()[0]:
        return True
    return False


class Logger:
    """Common JSON logger for authomize service."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("authomize")
        self.logger.propagate = False
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def set_level(self, level: str) -> None:
        """Set the log level

        Args:
            level str: Log level to set
        """
        level = logging.getLevelName(level.upper())
        self.logger.setLevel(level)

    @_log_wrapper("FATAL")
    def fatal(self, msg: str, extra: Optional[dict] = None) -> None:
        """Logs a message with level FATAL on the authomize logger."""
        self.logger.fatal(msg, exc_info=_exc_info(), extra=extra)
        sys.exit(1)

    @_log_wrapper("ERROR")
    def error(self, msg: str, extra: Optional[dict] = None) -> None:
        """Logs a message with level ERROR on the authomize logger."""
        self.logger.error(msg, exc_info=_exc_info(), extra=extra)

    @_log_wrapper("WARNING")
    def warning(self, msg: str, extra: Optional[dict] = None) -> None:
        """Logs a message with level WARNING on the authomize logger."""
        self.logger.warning(msg, exc_info=_exc_info(), extra=extra)

    @_log_wrapper("INFO")
    def info(self, msg: str, extra: Optional[dict] = None) -> None:
        """Logs a message with level INFO on the authomize logger."""
        self.logger.info(msg, extra=extra)

    @_log_wrapper("DEBUG")
    def debug(self, msg: str, extra: Optional[dict] = None) -> None:
        """Logs a message with level DEBUG on the authomize logger."""
        self.logger.debug(msg, extra=extra)


logger = Logger()
