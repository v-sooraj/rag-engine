from collections.abc import Callable
from hashlib import sha256
from uuid import UUID, uuid4

from rag_engine.database.connection import create_connection
from rag_engine.embedding.embedded_chunk import EmbeddedChunk
from rag_engine.loader.document import Document
from rag_engine.vector_store.vector_store import VectorStore


class PostgresVectorStore(VectorStore):

    EMBEDDING_DIMENSION = 384

    def __init__(
        self,
        connection_factory: Callable = create_connection,
    ):
        self.connection_factory = connection_factory

    def store(
        self,
        document: Document,
        chunks: list[EmbeddedChunk],
    ) -> UUID:
        self._validate(
            document=document,
            chunks=chunks,
        )

        content_hash = self._calculate_content_hash(
            document=document,
        )

        candidate_document_id = uuid4()

        with self.connection_factory() as connection:
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
                    ON CONFLICT (content_hash)
                    DO NOTHING
                    RETURNING id
                    """,
                    (
                        candidate_document_id,
                        document.metadata.filename,
                        document.metadata.title,
                        document.metadata.author,
                        document.metadata.language,
                        document.metadata.page_count,
                        content_hash,
                    ),
                )

                inserted_document = cursor.fetchone()

                if inserted_document is None:
                    cursor.execute(
                        """
                        SELECT id
                        FROM documents
                        WHERE content_hash = %s
                        """,
                        (content_hash,),
                    )

                    existing_document = cursor.fetchone()

                    if existing_document is None:
                        raise RuntimeError(
                            "Document conflict occurred but existing "
                            "document could not be found"
                        )

                    return existing_document[0]

                document_id = inserted_document[0]

                chunk_rows = [
                    (
                        uuid4(),
                        document_id,
                        embedded_chunk.chunk.metadata.chunk_index,
                        embedded_chunk.chunk.content,
                        self._to_vector_string(
                            embedded_chunk.embedding
                        ),
                    )
                    for embedded_chunk in chunks
                ]

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
                    chunk_rows,
                )

                return document_id

    def _validate(
            self,
            document: Document,
            chunks: list[EmbeddedChunk],
    ) -> None:
        if not chunks:
            raise ValueError("chunks must not be empty")

        chunk_indexes = set()

        for embedded_chunk in chunks:
            if (
                    embedded_chunk.chunk.metadata.document_metadata
                    != document.metadata
            ):
                raise ValueError(
                    "Chunk document metadata does not match document metadata"
                )

            actual_dimension = len(
                embedded_chunk.embedding
            )

            if actual_dimension != self.EMBEDDING_DIMENSION:
                raise ValueError(
                    f"Expected embedding dimension "
                    f"{self.EMBEDDING_DIMENSION}, "
                    f"got {actual_dimension}"
                )

            chunk_index = embedded_chunk.chunk.metadata.chunk_index

            if chunk_index in chunk_indexes:
                raise ValueError(
                    "Chunk indexes must be unique"
                )

            chunk_indexes.add(chunk_index)

    @staticmethod
    def _calculate_content_hash(
        document: Document,
    ) -> str:
        return sha256(
            document.content.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _to_vector_string(
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