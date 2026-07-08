from uuid import UUID

from rag_engine.chunker.recursive_document_chunker import (
    RecursiveDocumentChunker,
)
from rag_engine.database.connection import (
    create_connection,
)
from rag_engine.embedding.local_chunk_embedder import (
    LocalChunkEmbedder,
)
from rag_engine.ingestion_pipeline.default_ingestion_pipeline import (
    DefaultIngestionPipeline,
)
from rag_engine.loader.pdf_loader import (
    PdfLoader,
)
from rag_engine.vector_store.postgres_vector_store import (
    PostgresVectorStore,
)


PDF_PATH = "tests/resources/sample.pdf"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


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


def test_real_ingestion_pipeline():
    pipeline = DefaultIngestionPipeline(
        document_loader=PdfLoader(),
        document_chunker=RecursiveDocumentChunker(
            chunk_size=500,
            chunk_overlap=50,
        ),
        chunk_embedder=LocalChunkEmbedder(
            model_name=EMBEDDING_MODEL_NAME,
            batch_size=2,
        ),
        vector_store=PostgresVectorStore(),
    )

    document_id = pipeline.ingest(
        PDF_PATH
    )

    try:
        assert isinstance(
            document_id,
            UUID,
        )

        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        filename,
                        page_count
                    FROM documents
                    WHERE id = %s
                    """,
                    (document_id,),
                )

                stored_document = cursor.fetchone()

                assert stored_document is not None
                assert stored_document[0] == "sample.pdf"
                assert stored_document[1] > 1

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

                assert len(stored_chunks) > 1

                assert [
                    chunk[0]
                    for chunk in stored_chunks
                ] == list(
                    range(len(stored_chunks))
                )

                assert all(
                    chunk[1].strip()
                    for chunk in stored_chunks
                )

                assert all(
                    chunk[2] == 384
                    for chunk in stored_chunks
                )

    finally:
        delete_test_document(
            document_id
        )