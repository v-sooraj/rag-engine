from uuid import UUID, uuid4

from sentence_transformers import SentenceTransformer

from rag_engine.chunker.chunk import Chunk, ChunkMetadata
from rag_engine.database.connection import create_connection
from rag_engine.embedding.local_chunk_embedder import LocalChunkEmbedder
from rag_engine.loader.document import Document, DocumentMetadata
from rag_engine.query_embedding.local_query_embedder import (
    LocalQueryEmbedder,
)
from rag_engine.retrieval.postgres_retriever import PostgresRetriever
from rag_engine.vector_store.postgres_vector_store import PostgresVectorStore


MODEL_NAME = "all-MiniLM-L6-v2"


def create_test_document() -> Document:
    return Document(
        content=(
            "Vector databases store numerical embeddings and support "
            "similarity search. "
            f"Semantic retrieval integration test {uuid4()}."
        ),
        metadata=DocumentMetadata(
            filename="semantic-retrieval-test.pdf",
            title="Semantic Retrieval Test",
            author="Test Author",
            language="en",
            page_count=1,
        ),
    )


def create_test_chunks(
    document: Document,
) -> list[Chunk]:
    return [
        Chunk(
            content=(
                "Vector databases store embeddings and retrieve "
                "similar items using vector similarity search."
            ),
            metadata=ChunkMetadata(
                chunk_index=0,
                document_metadata=document.metadata,
            ),
        ),
        Chunk(
            content=(
                "Biryani is a rice dish prepared with spices, "
                "vegetables, or meat."
            ),
            metadata=ChunkMetadata(
                chunk_index=1,
                document_metadata=document.metadata,
            ),
        ),
        Chunk(
            content=(
                "Cricket is played between two teams using "
                "a bat and a ball."
            ),
            metadata=ChunkMetadata(
                chunk_index=2,
                document_metadata=document.metadata,
            ),
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


"""
Given: semantically different text chunks stored with real local embeddings
When: a real user query is embedded and used for pgvector retrieval
Then: the semantically relevant chunk is ranked first
"""
def test_real_semantic_retrieval_pipeline():
    document = create_test_document()
    chunks = create_test_chunks(document)

    model = SentenceTransformer(
        MODEL_NAME
    )

    chunk_embedder = LocalChunkEmbedder(
        model_name=MODEL_NAME,
        batch_size=32,
        model=model,
    )

    query_embedder = LocalQueryEmbedder(
        model_name=MODEL_NAME,
        model=model,
    )

    vector_store = PostgresVectorStore()
    retriever = PostgresRetriever()

    embedded_chunks = chunk_embedder.embed(
        chunks
    )

    document_id = vector_store.store(
        document=document,
        chunks=embedded_chunks,
    )

    try:
        query_embedding = query_embedder.embed(
            "How can I find similar information using embeddings?"
        )

        results = retriever.retrieve(
            query_embedding=query_embedding,
            top_k=3,
        )

        document_results = [
            result
            for result in results
            if result.document_id == document_id
        ]

        assert document_results

        assert (
            document_results[0].content
            == (
                "Vector databases store embeddings and retrieve "
                "similar items using vector similarity search."
            )
        )

        assert all(
            document_results[index].distance
            <= document_results[index + 1].distance
            for index in range(
                len(document_results) - 1
            )
        )

    finally:
        delete_test_document(
            document_id
        )