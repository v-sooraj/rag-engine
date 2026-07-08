import os
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import UploadFile

from rag_engine.api.adapters.document_upload_adapter import (
    DocumentUploadAdapter,
)
from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)


PDF_CONTENT = b"%PDF-1.4 test content"


@pytest.fixture
def ingestion_pipeline() -> Mock:
    return Mock(
        spec=IngestionPipeline
    )


@pytest.fixture
def upload_file() -> UploadFile:
    return UploadFile(
        filename="document.pdf",
        file=BytesIO(PDF_CONTENT),
    )


@pytest.fixture
def adapter(
    ingestion_pipeline: Mock,
) -> DocumentUploadAdapter:
    return DocumentUploadAdapter(
        ingestion_pipeline=ingestion_pipeline
    )


def test_ingest_returns_document_id(
    adapter: DocumentUploadAdapter,
    ingestion_pipeline: Mock,
    upload_file: UploadFile,
):
    document_id = uuid4()

    ingestion_pipeline.ingest.return_value = (
        document_id
    )

    result = adapter.ingest(
        upload_file
    )

    assert result == document_id


def test_ingest_passes_temporary_pdf_path_to_pipeline(
    adapter: DocumentUploadAdapter,
    ingestion_pipeline: Mock,
    upload_file: UploadFile,
):
    ingestion_pipeline.ingest.return_value = uuid4()

    adapter.ingest(
        upload_file
    )

    path = (
        ingestion_pipeline
        .ingest
        .call_args
        .args[0]
    )

    assert path.endswith(".pdf")


def test_ingest_copies_uploaded_content_to_temporary_file(
    adapter: DocumentUploadAdapter,
    ingestion_pipeline: Mock,
    upload_file: UploadFile,
):
    captured_content = None

    def capture_content(
        path: str,
    ):
        nonlocal captured_content

        with open(
            path,
            "rb",
        ) as temporary_file:
            captured_content = (
                temporary_file.read()
            )

        return uuid4()

    ingestion_pipeline.ingest.side_effect = (
        capture_content
    )

    adapter.ingest(
        upload_file
    )

    assert captured_content == PDF_CONTENT


def test_ingest_deletes_temporary_file_after_success(
    adapter: DocumentUploadAdapter,
    ingestion_pipeline: Mock,
    upload_file: UploadFile,
):
    captured_path = None

    def capture_path(
        path: str,
    ):
        nonlocal captured_path
        captured_path = path
        return uuid4()

    ingestion_pipeline.ingest.side_effect = (
        capture_path
    )

    adapter.ingest(
        upload_file
    )

    assert captured_path is not None
    assert not os.path.exists(
        captured_path
    )


def test_ingest_deletes_temporary_file_when_pipeline_fails(
    adapter: DocumentUploadAdapter,
    ingestion_pipeline: Mock,
    upload_file: UploadFile,
):
    captured_path = None

    def fail(
        path: str,
    ):
        nonlocal captured_path
        captured_path = path

        raise RuntimeError(
            "ingestion failed"
        )

    ingestion_pipeline.ingest.side_effect = fail

    with pytest.raises(
        RuntimeError,
        match="ingestion failed",
    ):
        adapter.ingest(
            upload_file
        )

    assert captured_path is not None
    assert not os.path.exists(
        captured_path
    )


def test_ingest_propagates_pipeline_failure_unchanged(
    adapter: DocumentUploadAdapter,
    ingestion_pipeline: Mock,
    upload_file: UploadFile,
):
    error = RuntimeError(
        "ingestion failed"
    )

    ingestion_pipeline.ingest.side_effect = error

    with pytest.raises(
        RuntimeError
    ) as exception_info:
        adapter.ingest(
            upload_file
        )

    assert exception_info.value is error

def test_ingest_preserves_original_filename_in_temporary_path(
    adapter: DocumentUploadAdapter,
    ingestion_pipeline: Mock,
    upload_file: UploadFile,
):
    ingestion_pipeline.ingest.return_value = uuid4()

    adapter.ingest(
        upload_file
    )

    path = (
        ingestion_pipeline
        .ingest
        .call_args
        .args[0]
    )

    assert Path(path).name == "document.pdf"