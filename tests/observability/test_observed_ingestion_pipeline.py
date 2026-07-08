from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)
from rag_engine.observability.context import (
    reset_request_id,
    set_request_id,
)
from rag_engine.observability.observed_ingestion_pipeline import (
    ObservedIngestionPipeline,
)


@pytest.fixture
def delegate() -> Mock:
    return Mock(
        spec=IngestionPipeline
    )


@pytest.fixture
def pipeline(
    delegate: Mock,
) -> ObservedIngestionPipeline:
    return ObservedIngestionPipeline(
        delegate=delegate
    )


@patch(
    "rag_engine.observability."
    "observed_ingestion_pipeline.logger"
)
def test_ingest_delegates_and_returns_document_id(
    logger: Mock,
    pipeline: ObservedIngestionPipeline,
    delegate: Mock,
):
    document_id = uuid4()

    delegate.ingest.return_value = (
        document_id
    )

    result = pipeline.ingest(
        "document.pdf"
    )

    assert result == document_id

    delegate.ingest.assert_called_once_with(
        "document.pdf"
    )


@patch(
    "rag_engine.observability."
    "observed_ingestion_pipeline.logger"
)
def test_ingest_logs_started_and_completed_events(
    logger: Mock,
    pipeline: ObservedIngestionPipeline,
    delegate: Mock,
):
    document_id = uuid4()

    delegate.ingest.return_value = (
        document_id
    )

    pipeline.ingest(
        "document.pdf"
    )

    assert (
        logger.info.call_args_list[0].args[0]
        == "ingestion.started"
    )

    assert (
        logger.info.call_args_list[1].args[0]
        == "ingestion.completed"
    )


@patch(
    "rag_engine.observability."
    "observed_ingestion_pipeline.logger"
)
def test_ingest_logs_document_filename_without_full_path(
    logger: Mock,
    pipeline: ObservedIngestionPipeline,
    delegate: Mock,
):
    delegate.ingest.return_value = uuid4()

    pipeline.ingest(
        "private/path/document.pdf"
    )

    started_extra = (
        logger.info
        .call_args_list[0]
        .kwargs["extra"]
    )

    assert (
            started_extra["document_filename"]
            == "document.pdf"
    )

    assert "path" not in started_extra


@patch(
    "rag_engine.observability."
    "observed_ingestion_pipeline.logger"
)
def test_ingest_includes_request_id_when_available(
    logger: Mock,
    pipeline: ObservedIngestionPipeline,
    delegate: Mock,
):
    delegate.ingest.return_value = uuid4()

    token = set_request_id(
        "request-123"
    )

    try:
        pipeline.ingest(
            "document.pdf"
        )

    finally:
        reset_request_id(
            token
        )

    started_extra = (
        logger.info
        .call_args_list[0]
        .kwargs["extra"]
    )

    assert (
        started_extra["request_id"]
        == "request-123"
    )


@patch(
    "rag_engine.observability."
    "observed_ingestion_pipeline.logger"
)
def test_ingest_omits_request_id_when_unavailable(
    logger: Mock,
    pipeline: ObservedIngestionPipeline,
    delegate: Mock,
):
    delegate.ingest.return_value = uuid4()

    pipeline.ingest(
        "document.pdf"
    )

    started_extra = (
        logger.info
        .call_args_list[0]
        .kwargs["extra"]
    )

    assert "request_id" not in started_extra


@patch(
    "rag_engine.observability."
    "observed_ingestion_pipeline.perf_counter",
    side_effect=[10.0, 10.125],
)
@patch(
    "rag_engine.observability."
    "observed_ingestion_pipeline.logger"
)
def test_ingest_logs_duration_in_milliseconds(
    logger: Mock,
    perf_counter: Mock,
    pipeline: ObservedIngestionPipeline,
    delegate: Mock,
):
    delegate.ingest.return_value = uuid4()

    pipeline.ingest(
        "document.pdf"
    )

    completed_extra = (
        logger.info
        .call_args_list[1]
        .kwargs["extra"]
    )

    assert (
        completed_extra["duration_ms"]
        == 125.0
    )


@patch(
    "rag_engine.observability."
    "observed_ingestion_pipeline.logger"
)
def test_ingest_logs_failure_and_propagates_same_exception(
    logger: Mock,
    pipeline: ObservedIngestionPipeline,
    delegate: Mock,
):
    error = RuntimeError(
        "ingestion failed"
    )

    delegate.ingest.side_effect = error

    with pytest.raises(
        RuntimeError
    ) as exception_info:
        pipeline.ingest(
            "document.pdf"
        )

    assert exception_info.value is error

    logger.exception.assert_called_once()

    assert (
        logger.exception.call_args.args[0]
        == "ingestion.failed"
    )

    failure_extra = (
        logger.exception
        .call_args
        .kwargs["extra"]
    )

    assert (
        failure_extra["exception_type"]
        == "RuntimeError"
    )