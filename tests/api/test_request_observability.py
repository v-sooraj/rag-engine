from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from rag_engine.llm.generated_answer import GeneratedAnswer


def test_response_contains_generated_request_id(
    client: TestClient,
    rag_pipeline: Mock,
):
    generated_answer = GeneratedAnswer(
        content="test answer"
    )

    rag_pipeline.answer.return_value = generated_answer

    response = client.post(
        "/answers",
        json={
            "query": "What is RAG?",
        },
    )

    assert response.status_code == 200

    request_id = response.headers.get(
        "X-Request-ID"
    )

    assert request_id is not None


def test_response_reuses_client_request_id(
    client: TestClient,
    rag_pipeline: Mock,
):
    generated_answer = GeneratedAnswer(
        content="test answer"
    )

    rag_pipeline.answer.return_value = generated_answer

    response = client.post(
        "/answers",
        headers={
            "X-Request-ID": "client-request-123",
        },
        json={
            "query": "What is RAG?",
        },
    )

    assert (
        response.headers["X-Request-ID"]
        == "client-request-123"
    )


def test_document_response_contains_request_id(
    client: TestClient,
    ingestion_pipeline: Mock,
):
    ingestion_pipeline.ingest.return_value = (
        uuid4()
    )

    response = client.post(
        "/documents",
        files={
            "file": (
                "document.pdf",
                b"%PDF-1.4 test content",
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 201

    assert (
        response.headers.get(
            "X-Request-ID"
        )
        is not None
    )