import json
import logging

from rag_engine.observability.logging_config import (
    configure_logging,
)


def test_configure_logging_writes_json_to_stdout(
    capsys,
):
    configure_logging()

    logger = logging.getLogger(
        "test.logging"
    )

    logger.info(
        "test.event",
        extra={
            "request_id": "request-123",
        },
    )

    captured = capsys.readouterr()

    parsed = json.loads(
        captured.out.strip()
    )

    assert parsed["event"] == "test.event"

    assert (
        parsed["request_id"]
        == "request-123"
    )


def test_configure_logging_replaces_existing_handlers():
    root_logger = logging.getLogger()

    root_logger.addHandler(
        logging.NullHandler()
    )

    configure_logging()

    assert len(
        root_logger.handlers
    ) == 1