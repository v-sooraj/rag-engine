from unittest.mock import Mock, patch

import pytest

from rag_engine.observability.context import (
    reset_request_id,
    set_request_id,
)
from rag_engine.observability.observed_rag_pipeline import (
    ObservedRAGPipeline,
)
from rag_engine.rag_pipeline.rag_pipeline import (
    RAGPipeline,
)


@pytest.fixture
def delegate() -> Mock:
    return Mock(
        spec=RAGPipeline
    )


@pytest.fixture
def pipeline(
    delegate: Mock,
) -> ObservedRAGPipeline:
    return ObservedRAGPipeline(
        delegate=delegate
    )


@patch(
    "rag_engine.observability."
    "observed_rag_pipeline.logger"
)
def test_answer_delegates_and_returns_same_result(
    logger: Mock,
    pipeline: ObservedRAGPipeline,
    delegate: Mock,
):
    result = Mock()

    delegate.answer.return_value = result

    actual = pipeline.answer(
        "What is RAG?"
    )

    assert actual is result

    delegate.answer.assert_called_once_with(
        "What is RAG?"
    )


@patch(
    "rag_engine.observability."
    "observed_rag_pipeline.logger"
)
def test_answer_logs_started_and_completed_events(
    logger: Mock,
    pipeline: ObservedRAGPipeline,
    delegate: Mock,
):
    delegate.answer.return_value = Mock()

    pipeline.answer(
        "What is RAG?"
    )

    assert (
        logger.info.call_args_list[0].args[0]
        == "rag.started"
    )

    assert (
        logger.info.call_args_list[1].args[0]
        == "rag.completed"
    )


@patch(
    "rag_engine.observability."
    "observed_rag_pipeline.logger"
)
def test_answer_does_not_log_query_or_result(
    logger: Mock,
    pipeline: ObservedRAGPipeline,
    delegate: Mock,
):
    delegate.answer.return_value = Mock()

    pipeline.answer(
        "private user question"
    )

    for call in logger.info.call_args_list:
        extra = call.kwargs["extra"]

        assert "query" not in extra
        assert "answer" not in extra
        assert "result" not in extra


@patch(
    "rag_engine.observability."
    "observed_rag_pipeline.logger"
)
def test_answer_includes_request_id_when_available(
    logger: Mock,
    pipeline: ObservedRAGPipeline,
    delegate: Mock,
):
    delegate.answer.return_value = Mock()

    token = set_request_id(
        "request-123"
    )

    try:
        pipeline.answer(
            "What is RAG?"
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
    "observed_rag_pipeline.perf_counter",
    side_effect=[10.0, 10.250],
)
@patch(
    "rag_engine.observability."
    "observed_rag_pipeline.logger"
)
def test_answer_logs_duration_in_milliseconds(
    logger: Mock,
    perf_counter: Mock,
    pipeline: ObservedRAGPipeline,
    delegate: Mock,
):
    delegate.answer.return_value = Mock()

    pipeline.answer(
        "What is RAG?"
    )

    completed_extra = (
        logger.info
        .call_args_list[1]
        .kwargs["extra"]
    )

    assert (
        completed_extra["duration_ms"]
        == 250.0
    )


@patch(
    "rag_engine.observability."
    "observed_rag_pipeline.logger"
)
def test_answer_logs_failure_and_propagates_same_exception(
    logger: Mock,
    pipeline: ObservedRAGPipeline,
    delegate: Mock,
):
    error = RuntimeError(
        "generation failed"
    )

    delegate.answer.side_effect = error

    with pytest.raises(
        RuntimeError
    ) as exception_info:
        pipeline.answer(
            "What is RAG?"
        )

    assert exception_info.value is error

    logger.exception.assert_called_once()

    assert (
        logger.exception.call_args.args[0]
        == "rag.failed"
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