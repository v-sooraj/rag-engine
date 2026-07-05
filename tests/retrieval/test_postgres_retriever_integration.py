from uuid import uuid4

from rag_engine.database.connection import create_connection
from rag_engine.retrieval.postgres_retriever import (
    PostgresRetriever,
)


def to_vector_string(
    embedding: list[float],
) -> str:
    return (
        "["
        + ",".join(
            str(value)
            for value in embedding
        )
        + "]"
    )


def create_test_document_and_chunks():
    document_id = uuid4()

    first_chunk_id = uuid4()
    second_chunk_id = uuid4()
    third_chunk_id = uuid4()

    query_direction = [1.0] + [0.0] * 383

    close_direction = (
        [0.9, 0.1]
        + [0.0] * 382
    )

    far_direction = (
        [0.0, 1.0]
        + [0.0] * 382
    )

    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (
                    id,
                    filename,
                    title,
                    author,
                    language,
                    page_count,
                    content_hash
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    document_id,
                    "retrieval-test.pdf",
                    "Retrieval Test",
                    "Test Author",
                    "en",
                    1,
                    str(uuid4()),
                ),
            )

            cursor.executemany(
                """
                INSERT INTO chunks (
                    id,
                    document_id,
                    chunk_index,
                    content,
                    embedding
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::vector
                )
                """,
                [
                    (
                        first_chunk_id,
                        document_id,
                        0,
                        "Exact vector match",
                        to_vector_string(
                            query_direction
                        ),
                    ),
                    (
                        second_chunk_id,
                        document_id,
                        1,
                        "Close vector match",
                        to_vector_string(
                            close_direction
                        ),
                    ),
                    (
                        third_chunk_id,
                        document_id,
                        2,
                        "Far vector match",
                        to_vector_string(
                            far_direction
                        ),
                    ),
                ],
            )

    return (
        document_id,
        query_direction,
    )


def delete_test_document(
    document_id,
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


def test_real_postgres_retrieves_top_k_chunks_by_cosine_distance():
    (
        document_id,
        query_embedding,
    ) = create_test_document_and_chunks()

    retriever = PostgresRetriever()

    try:
        results = retriever.retrieve(
            query_embedding=query_embedding,
            top_k=2,
        )

        assert len(results) == 2

        assert (
            results[0].content
            == "Exact vector match"
        )

        assert (
            results[1].content
            == "Close vector match"
        )

        assert (
            results[0].distance
            <= results[1].distance
        )

        assert all(
            result.document_id == document_id
            for result in results
        )

    finally:
        delete_test_document(document_id)