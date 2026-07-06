from abc import ABC, abstractmethod

from rag_engine.llm.generated_answer import GeneratedAnswer


class RAGPipeline(ABC):

    @abstractmethod
    def answer(
        self,
        query: str,
    ) -> GeneratedAnswer:
        pass