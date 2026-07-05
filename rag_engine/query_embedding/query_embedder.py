from abc import ABC, abstractmethod


class QueryEmbedder(ABC):

    @abstractmethod
    def embed(
        self,
        query: str,
    ) -> list[float]:
        pass