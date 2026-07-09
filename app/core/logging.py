import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def configure_logging() -> None:
    """
    Configure structured JSON logging for the application.
    """

    handler = logging.StreamHandler(sys.stdout)

    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)