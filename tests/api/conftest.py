from collections.abc import Iterator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from rag_engine.api.app import create_app
from rag_engine.api.dependencies import (
    get_ingestion_pipeline,
    get_rag_pipeline,
)
from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)
from rag_engine.rag_pipeline.rag_pipeline import (
    RAGPipeline,
)


@pytest.fixture
def ingestion_pipeline() -> Mock:
    return Mock(
        spec=IngestionPipeline
    )


@pytest.fixture
def rag_pipeline() -> Mock:
    return Mock(
        spec=RAGPipeline
    )


@pytest.fixture
def client(
    ingestion_pipeline: Mock,
    rag_pipeline: Mock,
) -> Iterator[TestClient]:
    app = create_app()

    app.dependency_overrides[
        get_ingestion_pipeline
    ] = lambda: ingestion_pipeline

    app.dependency_overrides[
        get_rag_pipeline
    ] = lambda: rag_pipeline

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()