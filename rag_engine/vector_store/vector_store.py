from abc import ABC, abstractmethod
from uuid import UUID

from rag_engine.embedding.embedded_chunk import EmbeddedChunk
from rag_engine.loader.document import Document


class VectorStore(ABC):

    @abstractmethod
    def store(self, document: Document, embedded_chunks: list[EmbeddedChunk]) -> UUID:
        pass