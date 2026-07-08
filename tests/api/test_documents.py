from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient


PDF_CONTENT = b"%PDF-1.4 test content"


def test_document_upload_returns_created_document(
    client: TestClient,
    ingestion_pipeline: Mock,
):
    document_id = uuid4()

    ingestion_pipeline.ingest.return_value = (
        document_id
    )

    response = client.post(
        "/documents",
        files={
            "file": (
                "document.pdf",
                PDF_CONTENT,
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 201

    assert response.json() == {
        "document_id": str(document_id),
    }


def test_document_upload_calls_ingestion_pipeline(
    client: TestClient,
    ingestion_pipeline: Mock,
):
    ingestion_pipeline.ingest.return_value = uuid4()

    response = client.post(
        "/documents",
        files={
            "file": (
                "document.pdf",
                PDF_CONTENT,
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 201

    ingestion_pipeline.ingest.assert_called_once()


def test_document_upload_passes_temporary_pdf_path_to_pipeline(
    client: TestClient,
    ingestion_pipeline: Mock,
):
    ingestion_pipeline.ingest.return_value = uuid4()

    client.post(
        "/documents",
        files={
            "file": (
                "document.pdf",
                PDF_CONTENT,
                "application/pdf",
            ),
        },
    )

    path = (
        ingestion_pipeline
        .ingest
        .call_args
        .args[0]
    )

    assert path.endswith(".pdf")


def test_document_upload_rejects_missing_file(
    client: TestClient,
    ingestion_pipeline: Mock,
):
    response = client.post(
        "/documents"
    )

    assert response.status_code == 422

    ingestion_pipeline.ingest.assert_not_called()


def test_document_upload_rejects_non_pdf_content_type(
    client: TestClient,
    ingestion_pipeline: Mock,
):
    response = client.post(
        "/documents",
        files={
            "file": (
                "document.txt",
                b"text content",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 415

    assert response.json() == {
        "detail": "Only PDF files are supported",
    }

    ingestion_pipeline.ingest.assert_not_called()


def test_document_upload_returns_internal_server_error_when_pipeline_fails(
    client: TestClient,
    ingestion_pipeline: Mock,
):
    ingestion_pipeline.ingest.side_effect = (
        RuntimeError(
            "ingestion failed"
        )
    )

    response = client.post(
        "/documents",
        files={
            "file": (
                "document.pdf",
                PDF_CONTENT,
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 500