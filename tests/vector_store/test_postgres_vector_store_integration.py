from hashlib import sha256
from uuid import UUID, uuid4

import pytest

from rag_engine.chunker.chunk import Chunk, ChunkMetadata
from rag_engine.database.connection import create_connection
from rag_engine.embedding.embedded_chunk import EmbeddedChunk
from rag_engine.loader.document import Document, DocumentMetadata
from rag_engine.vector_store.postgres_vector_store import PostgresVectorStore


def create_test_document() -> Document:
    unique_content = (
        f"Unique integration test document content {uuid4()}."
    )

    return Document(
        content=unique_content,
        metadata=DocumentMetadata(
            filename="integration-test.pdf",
            title="Integration Test Document",
            author="Test Author",
            language="en",
            page_count=1,
        ),
    )


def create_test_chunks(
    document: Document,
) -> list[EmbeddedChunk]:
    return [
        EmbeddedChunk(
            chunk=Chunk(
                content="First integration test chunk.",
                metadata=ChunkMetadata(
                    chunk_index=0,
                    document_metadata=document.metadata,
                ),
            ),
            embedding=[0.1] * 384,
        ),
        EmbeddedChunk(
            chunk=Chunk(
                content="Second integration test chunk.",
                metadata=ChunkMetadata(
                    chunk_index=1,
                    document_metadata=document.metadata,
                ),
            ),
            embedding=[0.2] * 384,
        ),
    ]


def delete_test_document(
    document_id: UUID,
) -> None:
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )


def count_documents_by_content(
    content: str,
) -> int:
    content_hash = sha256(
        content.encode("utf-8")
    ).hexdigest()

    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM documents
                WHERE content_hash = %s
                """,
                (content_hash,),
            )

            return cursor.fetchone()[0]


class FailingChunkInsertCursor:

    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        self.cursor.__enter__()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return self.cursor.__exit__(
            exc_type,
            exc_value,
            traceback,
        )

    def execute(
        self,
        query,
        params=None,
    ):
        return self.cursor.execute(
            query,
            params,
        )

    def fetchone(self):
        return self.cursor.fetchone()

    def executemany(
        self,
        query,
        params_seq,
    ):
        raise RuntimeError(
            "Simulated chunk insertion failure"
        )


class FailingChunkInsertConnection:

    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return self.connection.__exit__(
            exc_type,
            exc_value,
            traceback,
        )

    def cursor(self):
        return FailingChunkInsertCursor(
            self.connection.cursor()
        )


def create_failing_connection():
    return FailingChunkInsertConnection(
        create_connection()
    )


"""
Given: a new document with valid embedded chunks
When: the document is stored using the real PostgreSQL vector store
Then: the document and all chunks are persisted successfully
"""
def test_real_postgres_vector_storage():
    document = create_test_document()
    chunks = create_test_chunks(document)

    vector_store = PostgresVectorStore()

    document_id = vector_store.store(
        document=document,
        chunks=chunks,
    )

    try:
        assert isinstance(document_id, UUID)

        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        filename,
                        title,
                        author,
                        language,
                        page_count
                    FROM documents
                    WHERE id = %s
                    """,
                    (document_id,),
                )

                stored_document = cursor.fetchone()

                assert stored_document == (
                    "integration-test.pdf",
                    "Integration Test Document",
                    "Test Author",
                    "en",
                    1,
                )

                cursor.execute(
                    """
                    SELECT
                        chunk_index,
                        content,
                        vector_dims(embedding)
                    FROM chunks
                    WHERE document_id = %s
                    ORDER BY chunk_index
                    """,
                    (document_id,),
                )

                stored_chunks = cursor.fetchall()

                assert stored_chunks == [
                    (
                        0,
                        "First integration test chunk.",
                        384,
                    ),
                    (
                        1,
                        "Second integration test chunk.",
                        384,
                    ),
                ]

    finally:
        delete_test_document(document_id)


"""
Given: a document that has already been stored
When: the same document is stored again
Then: the existing document UUID is returned without duplicating rows
"""
def test_real_postgres_vector_storage_is_idempotent():
    document = create_test_document()
    chunks = create_test_chunks(document)

    vector_store = PostgresVectorStore()

    first_document_id = vector_store.store(
        document=document,
        chunks=chunks,
    )

    try:
        second_document_id = vector_store.store(
            document=document,
            chunks=chunks,
        )

        assert second_document_id == first_document_id

        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM documents
                    WHERE id = %s
                    """,
                    (first_document_id,),
                )

                assert cursor.fetchone()[0] == 1

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM chunks
                    WHERE document_id = %s
                    """,
                    (first_document_id,),
                )

                assert cursor.fetchone()[0] == 2

    finally:
        delete_test_document(first_document_id)


"""
Given: a new document whose chunk insertion fails
When: store() runs inside a real PostgreSQL transaction
Then: the already inserted document is rolled back
"""
def test_real_postgres_rolls_back_document_when_chunk_insertion_fails():
    document = create_test_document()
    chunks = create_test_chunks(document)

    vector_store = PostgresVectorStore(
        connection_factory=create_failing_connection,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated chunk insertion failure",
    ):
        vector_store.store(
            document=document,
            chunks=chunks,
        )

    document_count = count_documents_by_content(
        document.content
    )

    assert document_count == 0