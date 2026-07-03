from abc import ABC, abstractmethod

from rag_engine.chunker.chunk import Chunk
from rag_engine.loader.document import Document


class DocumentChunker(ABC):

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        pass