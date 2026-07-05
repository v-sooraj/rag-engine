from abc import ABC, abstractmethod

from rag_engine.retrieval.retrieved_chunk import RetrievedChunk


class Retriever(ABC):

    @abstractmethod
    def retrieve(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        pass