from abc import ABC, abstractmethod

from rag_engine.prompt_augmentation.augmented_prompt import AugmentedPrompt
from rag_engine.retrieval.retrieved_chunk import RetrievedChunk


class PromptAugmenter(ABC):

    @abstractmethod
    def augment(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> AugmentedPrompt:
        pass