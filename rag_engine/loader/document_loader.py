from abc import ABC, abstractmethod

from rag_engine.loader.document import Document


class DocumentLoader(ABC):

    @abstractmethod
    def load(self, path: str) -> Document:
        pass
