import logging
import sys

from rag_engine.observability.json_formatter import (
    JsonFormatter,
)


def configure_logging(
    level: int = logging.INFO,
) -> None:
    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setFormatter(
        JsonFormatter()
    )

    root_logger = logging.getLogger()

    root_logger.handlers.clear()
    root_logger.addHandler(
        handler
    )
    root_logger.setLevel(
        level
    )