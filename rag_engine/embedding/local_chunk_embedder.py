from sentence_transformers import SentenceTransformer

from rag_engine.chunker.chunk import Chunk
from rag_engine.embedding.chunk_embedder import ChunkEmbedder
from rag_engine.embedding.embedded_chunk import EmbeddedChunk


class LocalChunkEmbedder(ChunkEmbedder):

    def __init__(
        self,
        model_name: str,
        batch_size: int = 32,
        model: SentenceTransformer | None = None,
    ):
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")

        self.model = model or SentenceTransformer(model_name)
        self.batch_size = batch_size

    def embed(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        if not chunks:
            return []

        embeddings = self.model.encode(
            [chunk.content for chunk in chunks],
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding response count does not match input chunk count"
            )

        return [
            EmbeddedChunk(
                chunk=chunk,
                embedding=embedding.tolist(),
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]