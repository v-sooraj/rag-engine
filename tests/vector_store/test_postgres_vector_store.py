from unittest.mock import Mock
from uuid import uuid4

import pytest

from rag_engine.chunker.chunk import Chunk, ChunkMetadata
from rag_engine.embedding.embedded_chunk import EmbeddedChunk
from rag_engine.loader.document import Document, DocumentMetadata
from rag_engine.vector_store.postgres_vector_store import PostgresVectorStore


def create_document() -> Document:
    return Document(
        content="This is the original document content.",
        metadata=DocumentMetadata(
            filename="test.pdf",
            title="Test Document",
            author="Test Author",
            language="en",
            page_count=1,
        ),
    )


def create_embedded_chunk(
    document_metadata: DocumentMetadata,
    chunk_index: int = 0,
    embedding_dimension: int = 384,
) -> EmbeddedChunk:
    return EmbeddedChunk(
        chunk=Chunk(
            content=f"This is chunk {chunk_index} content.",
            metadata=ChunkMetadata(
                chunk_index=chunk_index,
                document_metadata=document_metadata,
            ),
        ),
        embedding=[0.1] * embedding_dimension,
    )


def create_mock_connection():
    connection = Mock()
    cursor = Mock()

    connection.__enter__ = Mock(
        return_value=connection,
    )
    connection.__exit__ = Mock(
        return_value=False,
    )

    cursor.__enter__ = Mock(
        return_value=cursor,
    )
    cursor.__exit__ = Mock(
        return_value=False,
    )

    connection.cursor.return_value = cursor

    return connection, cursor


"""
Given: an empty list of embedded chunks
When: store() is called
Then: validation fails before opening a database connection
"""
def test_store_rejects_empty_chunks_before_opening_connection():
    document = create_document()
    connection_factory = Mock()

    vector_store = PostgresVectorStore(
        connection_factory=connection_factory,
    )

    with pytest.raises(
        ValueError,
        match="chunks must not be empty",
    ):
        vector_store.store(
            document=document,
            chunks=[],
        )

    connection_factory.assert_not_called()


"""
Given: an embedded chunk belonging to different document metadata
When: store() is called
Then: validation fails before opening a database connection
"""
def test_store_rejects_chunk_metadata_mismatch_before_opening_connection():
    document = create_document()

    different_document_metadata = DocumentMetadata(
        filename="another.pdf",
        title="Another Document",
        author="Another Author",
        language="en",
        page_count=2,
    )

    embedded_chunk = create_embedded_chunk(
        document_metadata=different_document_metadata,
    )

    connection_factory = Mock()

    vector_store = PostgresVectorStore(
        connection_factory=connection_factory,
    )

    with pytest.raises(
        ValueError,
        match="Chunk document metadata does not match document metadata",
    ):
        vector_store.store(
            document=document,
            chunks=[embedded_chunk],
        )

    connection_factory.assert_not_called()


"""
Given: an embedded chunk whose vector dimension does not match the storage schema
When: store() is called
Then: validation fails before opening a database connection
"""
def test_store_rejects_invalid_embedding_dimension_before_opening_connection():
    document = create_document()

    embedded_chunk = create_embedded_chunk(
        document_metadata=document.metadata,
        embedding_dimension=768,
    )

    connection_factory = Mock()

    vector_store = PostgresVectorStore(
        connection_factory=connection_factory,
    )

    with pytest.raises(
        ValueError,
        match="Expected embedding dimension 384, got 768",
    ):
        vector_store.store(
            document=document,
            chunks=[embedded_chunk],
        )

    connection_factory.assert_not_called()


"""
Given: a new document with valid embedded chunks
When: store() is called
Then: the document and all chunks are persisted and the document UUID is returned
"""
def test_store_persists_new_document_and_all_chunks():
    document = create_document()

    chunks = [
        create_embedded_chunk(
            document_metadata=document.metadata,
            chunk_index=0,
        ),
        create_embedded_chunk(
            document_metadata=document.metadata,
            chunk_index=1,
        ),
    ]

    document_id = uuid4()

    connection, cursor = create_mock_connection()

    cursor.fetchone.return_value = (document_id,)

    connection_factory = Mock(
        return_value=connection,
    )

    vector_store = PostgresVectorStore(
        connection_factory=connection_factory,
    )

    stored_document_id = vector_store.store(
        document=document,
        chunks=chunks,
    )

    assert stored_document_id == document_id

    connection_factory.assert_called_once()
    connection.cursor.assert_called_once()

    assert cursor.execute.call_count == 1
    assert cursor.executemany.call_count == 1

    inserted_chunks = cursor.executemany.call_args.args[1]

    assert len(inserted_chunks) == 2

    assert inserted_chunks[0][1] == document_id
    assert inserted_chunks[0][2] == 0
    assert inserted_chunks[0][3] == "This is chunk 0 content."

    assert inserted_chunks[1][1] == document_id
    assert inserted_chunks[1][2] == 1
    assert inserted_chunks[1][3] == "This is chunk 1 content."


"""
Given: a document whose content has already been stored
When: store() is called again
Then: the existing document UUID is returned without inserting chunks again
"""
def test_store_returns_existing_document_id_for_duplicate_content():
    document = create_document()

    chunks = [
        create_embedded_chunk(
            document_metadata=document.metadata,
            chunk_index=0,
        ),
    ]

    existing_document_id = uuid4()

    connection, cursor = create_mock_connection()

    cursor.fetchone.side_effect = [
        None,
        (existing_document_id,),
    ]

    connection_factory = Mock(
        return_value=connection,
    )

    vector_store = PostgresVectorStore(
        connection_factory=connection_factory,
    )

    stored_document_id = vector_store.store(
        document=document,
        chunks=chunks,
    )

    assert stored_document_id == existing_document_id

    connection_factory.assert_called_once()
    connection.cursor.assert_called_once()

    assert cursor.execute.call_count == 2
    cursor.executemany.assert_not_called()


"""
Given: a new document whose chunk insertion fails
When: store() is called
Then: the persistence error propagates from the storage operation
"""
def test_store_propagates_chunk_insertion_failure():
    document = create_document()

    chunks = [
        create_embedded_chunk(
            document_metadata=document.metadata,
            chunk_index=0,
        ),
    ]

    document_id = uuid4()

    connection, cursor = create_mock_connection()

    cursor.fetchone.return_value = (document_id,)
    cursor.executemany.side_effect = RuntimeError(
        "Chunk insertion failed"
    )

    connection_factory = Mock(
        return_value=connection,
    )

    vector_store = PostgresVectorStore(
        connection_factory=connection_factory,
    )

    with pytest.raises(
        RuntimeError,
        match="Chunk insertion failed",
    ):
        vector_store.store(
            document=document,
            chunks=chunks,
        )

    connection_factory.assert_called_once()
    cursor.executemany.assert_called_once()

"""
Given: multiple embedded chunks with the same chunk index
When: store() is called
Then: validation fails before opening a database connection
"""
def test_store_rejects_duplicate_chunk_indexes_before_opening_connection():
    document = create_document()

    chunks = [
        create_embedded_chunk(
            document_metadata=document.metadata,
            chunk_index=0,
        ),
        create_embedded_chunk(
            document_metadata=document.metadata,
            chunk_index=0,
        ),
    ]

    connection_factory = Mock()

    vector_store = PostgresVectorStore(
        connection_factory=connection_factory,
    )

    with pytest.raises(
        ValueError,
        match="Chunk indexes must be unique",
    ):
        vector_store.store(
            document=document,
            chunks=chunks,
        )

    connection_factory.assert_not_called()