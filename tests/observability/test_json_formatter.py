import json
import logging

from rag_engine.observability.json_formatter import (
    JsonFormatter,
)


def create_record(
    message: str = "test.event",
) -> logging.LogRecord:
    return logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_formatter_outputs_valid_json():
    formatter = JsonFormatter()

    result = formatter.format(
        create_record()
    )

    parsed = json.loads(
        result
    )

    assert isinstance(
        parsed,
        dict,
    )


def test_formatter_includes_common_fields():
    formatter = JsonFormatter()

    parsed = json.loads(
        formatter.format(
            create_record()
        )
    )

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert parsed["event"] == "test.event"
    assert "timestamp" in parsed


def test_formatter_includes_custom_extra_fields():
    formatter = JsonFormatter()

    record = create_record()

    record.request_id = "request-123"
    record.duration_ms = 42.5

    parsed = json.loads(
        formatter.format(
            record
        )
    )

    assert (
        parsed["request_id"]
        == "request-123"
    )

    assert (
        parsed["duration_ms"]
        == 42.5
    )


def test_formatter_serializes_non_json_native_values():
    formatter = JsonFormatter()

    record = create_record()
    record.custom_value = object()

    parsed = json.loads(
        formatter.format(
            record
        )
    )

    assert isinstance(
        parsed["custom_value"],
        str,
    )