from unittest.mock import Mock
from uuid import uuid4

import pytest

from rag_engine.chunker.chunk import (
    Chunk,
    ChunkMetadata,
)
from rag_engine.chunker.document_chunker import (
    DocumentChunker,
)
from rag_engine.embedding.chunk_embedder import (
    ChunkEmbedder,
)
from rag_engine.embedding.embedded_chunk import (
    EmbeddedChunk,
)
from rag_engine.ingestion_pipeline.default_ingestion_pipeline import (
    DefaultIngestionPipeline,
)
from rag_engine.loader.document import (
    Document,
    DocumentMetadata,
)
from rag_engine.loader.document_loader import (
    DocumentLoader,
)
from rag_engine.vector_store.vector_store import (
    VectorStore,
)


PATH = "documents/vector-databases.pdf"


@pytest.fixture
def document() -> Document:
    return Document(
        content=(
            "Vector databases store and search "
            "high-dimensional embeddings."
        ),
        metadata=DocumentMetadata(
            filename="vector-databases.pdf",
            title="Vector Databases",
            author="Test Author",
            language="en",
            page_count=1,
        ),
    )


@pytest.fixture
def chunks(
    document: Document,
) -> list[Chunk]:
    return [
        Chunk(
            content=(
                "Vector databases store embeddings."
            ),
            metadata=ChunkMetadata(
                chunk_index=0,
                document_metadata=document.metadata,
            ),
        ),
        Chunk(
            content=(
                "They support similarity search."
            ),
            metadata=ChunkMetadata(
                chunk_index=1,
                document_metadata=document.metadata,
            ),
        ),
    ]


@pytest.fixture
def embedded_chunks(
    chunks: list[Chunk],
) -> list[EmbeddedChunk]:
    return [
        EmbeddedChunk(
            chunk=chunks[0],
            embedding=[0.1] * 384,
        ),
        EmbeddedChunk(
            chunk=chunks[1],
            embedding=[0.2] * 384,
        ),
    ]


@pytest.fixture
def document_loader() -> Mock:
    return Mock(
        spec=DocumentLoader
    )


@pytest.fixture
def document_chunker() -> Mock:
    return Mock(
        spec=DocumentChunker
    )


@pytest.fixture
def chunk_embedder() -> Mock:
    return Mock(
        spec=ChunkEmbedder
    )


@pytest.fixture
def vector_store() -> Mock:
    return Mock(
        spec=VectorStore
    )


@pytest.fixture
def pipeline(
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
) -> DefaultIngestionPipeline:
    return DefaultIngestionPipeline(
        document_loader=document_loader,
        document_chunker=document_chunker,
        chunk_embedder=chunk_embedder,
        vector_store=vector_store,
    )


def test_ingest_returns_stored_document_id(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
    document: Document,
    chunks: list[Chunk],
    embedded_chunks: list[EmbeddedChunk],
):
    document_id = uuid4()

    document_loader.load.return_value = document
    document_chunker.chunk.return_value = chunks
    chunk_embedder.embed.return_value = (
        embedded_chunks
    )
    vector_store.store.return_value = document_id

    result = pipeline.ingest(PATH)

    assert result == document_id


def test_ingest_passes_path_to_document_loader(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
    document: Document,
    chunks: list[Chunk],
    embedded_chunks: list[EmbeddedChunk],
):
    document_loader.load.return_value = document
    document_chunker.chunk.return_value = chunks
    chunk_embedder.embed.return_value = (
        embedded_chunks
    )
    vector_store.store.return_value = uuid4()

    pipeline.ingest(PATH)

    document_loader.load.assert_called_once_with(
        PATH
    )


def test_ingest_passes_document_to_chunker(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
    document: Document,
    chunks: list[Chunk],
    embedded_chunks: list[EmbeddedChunk],
):
    document_loader.load.return_value = document
    document_chunker.chunk.return_value = chunks
    chunk_embedder.embed.return_value = (
        embedded_chunks
    )
    vector_store.store.return_value = uuid4()

    pipeline.ingest(PATH)

    document_chunker.chunk.assert_called_once_with(
        document
    )


def test_ingest_passes_chunks_to_chunk_embedder(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
    document: Document,
    chunks: list[Chunk],
    embedded_chunks: list[EmbeddedChunk],
):
    document_loader.load.return_value = document
    document_chunker.chunk.return_value = chunks
    chunk_embedder.embed.return_value = (
        embedded_chunks
    )
    vector_store.store.return_value = uuid4()

    pipeline.ingest(PATH)

    chunk_embedder.embed.assert_called_once_with(
        chunks
    )


def test_ingest_passes_document_and_embedded_chunks_to_vector_store(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
    document: Document,
    chunks: list[Chunk],
    embedded_chunks: list[EmbeddedChunk],
):
    document_loader.load.return_value = document
    document_chunker.chunk.return_value = chunks
    chunk_embedder.embed.return_value = (
        embedded_chunks
    )
    vector_store.store.return_value = uuid4()

    pipeline.ingest(PATH)

    vector_store.store.assert_called_once_with(
        document,
        embedded_chunks,
    )


@pytest.mark.parametrize(
    "invalid_path",
    [
        "",
        " ",
        "   ",
        "\t",
        "\n",
    ],
)
def test_ingest_rejects_empty_or_blank_path(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
    invalid_path: str,
):
    with pytest.raises(
        ValueError,
        match="path must not be empty or blank",
    ):
        pipeline.ingest(
            invalid_path
        )

    document_loader.load.assert_not_called()
    document_chunker.chunk.assert_not_called()
    chunk_embedder.embed.assert_not_called()
    vector_store.store.assert_not_called()


def test_ingest_propagates_document_loader_failure_unchanged(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
):
    error = RuntimeError(
        "document loading failed"
    )

    document_loader.load.side_effect = error

    with pytest.raises(RuntimeError) as exception_info:
        pipeline.ingest(PATH)

    assert exception_info.value is error

    document_chunker.chunk.assert_not_called()
    chunk_embedder.embed.assert_not_called()
    vector_store.store.assert_not_called()


def test_ingest_propagates_document_chunker_failure_unchanged(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
    document: Document,
):
    error = RuntimeError(
        "document chunking failed"
    )

    document_loader.load.return_value = document
    document_chunker.chunk.side_effect = error

    with pytest.raises(RuntimeError) as exception_info:
        pipeline.ingest(PATH)

    assert exception_info.value is error

    chunk_embedder.embed.assert_not_called()
    vector_store.store.assert_not_called()


def test_ingest_propagates_chunk_embedder_failure_unchanged(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
    document: Document,
    chunks: list[Chunk],
):
    error = RuntimeError(
        "chunk embedding failed"
    )

    document_loader.load.return_value = document
    document_chunker.chunk.return_value = chunks
    chunk_embedder.embed.side_effect = error

    with pytest.raises(RuntimeError) as exception_info:
        pipeline.ingest(PATH)

    assert exception_info.value is error

    vector_store.store.assert_not_called()


def test_ingest_propagates_vector_store_failure_unchanged(
    pipeline: DefaultIngestionPipeline,
    document_loader: Mock,
    document_chunker: Mock,
    chunk_embedder: Mock,
    vector_store: Mock,
    document: Document,
    chunks: list[Chunk],
    embedded_chunks: list[EmbeddedChunk],
):
    error = RuntimeError(
        "vector storage failed"
    )

    document_loader.load.return_value = document
    document_chunker.chunk.return_value = chunks
    chunk_embedder.embed.return_value = (
        embedded_chunks
    )
    vector_store.store.side_effect = error

    with pytest.raises(RuntimeError) as exception_info:
        pipeline.ingest(PATH)

    assert exception_info.value is error