from abc import ABC, abstractmethod

from rag_engine.chunker.chunk import Chunk
from rag_engine.embedding.embedded_chunk import EmbeddedChunk


class ChunkEmbedder(ABC):

    @abstractmethod
    def embed(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        pass