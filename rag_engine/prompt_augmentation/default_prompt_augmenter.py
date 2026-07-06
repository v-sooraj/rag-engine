from rag_engine.prompt_augmentation.augmented_prompt import AugmentedPrompt
from rag_engine.prompt_augmentation.prompt_augmenter import PromptAugmenter
from rag_engine.retrieval.retrieved_chunk import RetrievedChunk


class DefaultPromptAugmenter(PromptAugmenter):

    SYSTEM_INSTRUCTION = (
        "Answer the question using only the provided context. "
        "If the context does not contain enough information to answer "
        "the question, say that you do not have enough information."
    )

    def augment(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> AugmentedPrompt:
        self._validate(query)

        context = self._build_context(chunks)

        return AugmentedPrompt(
            system_instruction=self.SYSTEM_INSTRUCTION,
            context=context,
            question=query,
        )

    def _validate(
        self,
        query: str,
    ) -> None:
        if not query.strip():
            raise ValueError(
                "query must not be empty"
            )

    def _build_context(
        self,
        chunks: list[RetrievedChunk],
    ) -> str:
        context_blocks = [
            (
                f"[CONTEXT {index}]\n"
                f"{chunk.content}"
            )
            for index, chunk in enumerate(
                chunks,
                start=1,
            )
        ]

        return "\n\n".join(context_blocks)