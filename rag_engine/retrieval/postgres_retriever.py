from collections.abc import Callable

from rag_engine.database.connection import create_connection
from rag_engine.retrieval.retrieved_chunk import RetrievedChunk
from rag_engine.retrieval.retriever import Retriever


class PostgresRetriever(Retriever):

    EMBEDDING_DIMENSION = 384

    def __init__(
        self,
        connection_factory: Callable = create_connection,
    ):
        self.connection_factory = connection_factory

    def retrieve(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        self._validate(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        query_vector = self._to_vector_string(
            query_embedding
        )

        with self.connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        document_id,
                        content,
                        chunk_index,
                        embedding <=> %s::vector AS distance
                    FROM chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (
                        query_vector,
                        query_vector,
                        top_k,
                    ),
                )

                rows = cursor.fetchall()

        return [
            RetrievedChunk(
                chunk_id=row[0],
                document_id=row[1],
                content=row[2],
                chunk_index=row[3],
                distance=row[4],
            )
            for row in rows
        ]

    def _validate(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> None:
        actual_dimension = len(
            query_embedding
        )

        if actual_dimension != self.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected query embedding dimension "
                f"{self.EMBEDDING_DIMENSION}, "
                f"got {actual_dimension}"
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0"
            )

    def _to_vector_string(
        self,
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