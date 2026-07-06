from abc import ABC, abstractmethod

from rag_engine.llm.generated_answer import GeneratedAnswer
from rag_engine.prompt_augmentation.augmented_prompt import AugmentedPrompt


class LLM(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: AugmentedPrompt,
    ) -> GeneratedAnswer:
        pass