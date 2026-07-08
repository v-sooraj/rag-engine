from abc import ABC, abstractmethod
from uuid import UUID


class IngestionPipeline(ABC):

    @abstractmethod
    def ingest(
        self,
        path: str,
    ) -> UUID:
        pass