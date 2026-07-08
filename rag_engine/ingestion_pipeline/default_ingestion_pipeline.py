from uuid import UUID

from rag_engine.chunker.document_chunker import (
    DocumentChunker,
)
from rag_engine.embedding.chunk_embedder import (
    ChunkEmbedder,
)
from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)
from rag_engine.loader.document_loader import (
    DocumentLoader,
)
from rag_engine.vector_store.vector_store import (
    VectorStore,
)


class DefaultIngestionPipeline(IngestionPipeline):

    def __init__(
        self,
        document_loader: DocumentLoader,
        document_chunker: DocumentChunker,
        chunk_embedder: ChunkEmbedder,
        vector_store: VectorStore,
    ):
        self._document_loader = document_loader
        self._document_chunker = document_chunker
        self._chunk_embedder = chunk_embedder
        self._vector_store = vector_store

    def ingest(
        self,
        path: str,
    ) -> UUID:
        if not path.strip():
            raise ValueError(
                "path must not be empty or blank"
            )

        document = self._document_loader.load(
            path
        )

        chunks = self._document_chunker.chunk(
            document
        )

        embedded_chunks = self._chunk_embedder.embed(
            chunks
        )

        return self._vector_store.store(
            document,
            embedded_chunks,
        )