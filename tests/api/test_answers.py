from unittest.mock import Mock

from fastapi.testclient import TestClient

from rag_engine.llm.generated_answer import (
    GeneratedAnswer,
)


QUERY = "What do vector databases store?"

ANSWER = (
    "Vector databases store embeddings."
)


def test_answer_returns_generated_answer(
    client: TestClient,
    rag_pipeline: Mock,
):
    rag_pipeline.answer.return_value = (
        GeneratedAnswer(
            content=ANSWER
        )
    )

    response = client.post(
        "/answers",
        json={
            "query": QUERY,
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "answer": ANSWER,
    }


def test_answer_passes_query_to_rag_pipeline(
    client: TestClient,
    rag_pipeline: Mock,
):
    rag_pipeline.answer.return_value = (
        GeneratedAnswer(
            content=ANSWER
        )
    )

    client.post(
        "/answers",
        json={
            "query": QUERY,
        },
    )

    rag_pipeline.answer.assert_called_once_with(
        QUERY
    )


def test_answer_rejects_missing_query(
    client: TestClient,
    rag_pipeline: Mock,
):
    response = client.post(
        "/answers",
        json={},
    )

    assert response.status_code == 422

    rag_pipeline.answer.assert_not_called()


def test_answer_rejects_empty_query(
    client: TestClient,
    rag_pipeline: Mock,
):
    response = client.post(
        "/answers",
        json={
            "query": "",
        },
    )

    assert response.status_code == 422

    rag_pipeline.answer.assert_not_called()


def test_answer_rejects_blank_query(
    client: TestClient,
    rag_pipeline: Mock,
):
    response = client.post(
        "/answers",
        json={
            "query": "   ",
        },
    )

    assert response.status_code == 422

    rag_pipeline.answer.assert_not_called()


def test_answer_rejects_null_query(
    client: TestClient,
    rag_pipeline: Mock,
):
    response = client.post(
        "/answers",
        json={
            "query": None,
        },
    )

    assert response.status_code == 422

    rag_pipeline.answer.assert_not_called()


def test_answer_rejects_non_string_query(
    client: TestClient,
    rag_pipeline: Mock,
):
    response = client.post(
        "/answers",
        json={
            "query": 123,
        },
    )

    assert response.status_code == 422

    rag_pipeline.answer.assert_not_called()


def test_answer_returns_internal_server_error_when_pipeline_fails(
    client: TestClient,
    rag_pipeline: Mock,
):
    rag_pipeline.answer.side_effect = (
        RuntimeError(
            "pipeline failed"
        )
    )

    response = client.post(
        "/answers",
        json={
            "query": QUERY,
        },
    )

    assert response.status_code == 500