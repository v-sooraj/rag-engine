from uuid import UUID

from rag_engine.chunker.document_chunker import DocumentChunker
from rag_engine.chunker.recursive_document_chunker import (
    RecursiveDocumentChunker,
)
from rag_engine.database.connection import create_connection
from rag_engine.embedding.chunk_embedder import ChunkEmbedder
from rag_engine.embedding.local_chunk_embedder import LocalChunkEmbedder
from rag_engine.loader.document_loader import DocumentLoader
from rag_engine.loader.pdf_loader import PdfLoader
from rag_engine.vector_store.postgres_vector_store import PostgresVectorStore
from rag_engine.vector_store.vector_store import VectorStore


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


"""
Given: a valid PDF document
When: the complete ingestion pipeline is executed
Then: the document and all generated embedded chunks are persisted
"""
def test_pdf_loading_chunking_embedding_and_storage_pipeline():
    loader: DocumentLoader = PdfLoader()

    chunker: DocumentChunker = RecursiveDocumentChunker(
        chunk_size=500,
        chunk_overlap=50,
    )

    embedder: ChunkEmbedder = LocalChunkEmbedder(
        model_name="all-MiniLM-L6-v2",
        batch_size=32,
    )

    vector_store: VectorStore = PostgresVectorStore()

    document = loader.load(
        "tests/resources/sample.pdf"
    )

    chunks = chunker.chunk(document)

    embedded_chunks = embedder.embed(chunks)

    document_id = vector_store.store(
        document=document,
        chunks=embedded_chunks,
    )

    try:
        assert isinstance(document_id, UUID)

        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM documents
                    WHERE id = %s
                    """,
                    (document_id,),
                )

                assert cursor.fetchone()[0] == 1

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM chunks
                    WHERE document_id = %s
                    """,
                    (document_id,),
                )

                stored_chunk_count = cursor.fetchone()[0]

                assert stored_chunk_count == len(
                    embedded_chunks
                )

                cursor.execute(
                    """
                    SELECT
                        chunk_index,
                        vector_dims(embedding)
                    FROM chunks
                    WHERE document_id = %s
                    ORDER BY chunk_index
                    """,
                    (document_id,),
                )

                stored_chunks = cursor.fetchall()

                assert [
                    row[0]
                    for row in stored_chunks
                ] == [
                    embedded_chunk.chunk.metadata.chunk_index
                    for embedded_chunk in embedded_chunks
                ]

                assert all(
                    vector_dimension == 384
                    for _, vector_dimension in stored_chunks
                )

    finally:
        delete_test_document(document_id)