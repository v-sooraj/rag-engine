from rag_engine.llm.generated_answer import GeneratedAnswer
from rag_engine.llm.llm import LLM
from rag_engine.prompt_augmentation.prompt_augmenter import PromptAugmenter
from rag_engine.query_embedding.query_embedder import QueryEmbedder
from rag_engine.rag_pipeline.rag_pipeline import RAGPipeline
from rag_engine.retrieval.retriever import Retriever


class DefaultRAGPipeline(RAGPipeline):

    def __init__(
        self,
        query_embedder: QueryEmbedder,
        retriever: Retriever,
        prompt_augmenter: PromptAugmenter,
        llm: LLM,
        top_k: int,
    ) -> None:
        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero"
            )

        self._query_embedder = query_embedder
        self._retriever = retriever
        self._prompt_augmenter = prompt_augmenter
        self._llm = llm
        self._top_k = top_k

    def answer(
        self,
        query: str,
    ) -> GeneratedAnswer:
        if not query.strip():
            raise ValueError(
                "query must not be empty or blank"
            )

        query_embedding = (
            self._query_embedder.embed(query)
        )

        retrieved_chunks = self._retriever.retrieve(
            query_embedding=query_embedding,
            top_k=self._top_k,
        )

        augmented_prompt = (
            self._prompt_augmenter.augment(
                query=query,
                chunks=retrieved_chunks,
            )
        )

        return self._llm.generate(
            augmented_prompt
        )