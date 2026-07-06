from functools import lru_cache

from sentence_transformers import SentenceTransformer

from rag_engine.config.settings import settings
from rag_engine.llm.ollama_llm import OllamaLLM
from rag_engine.prompt_augmentation.default_prompt_augmenter import (
    DefaultPromptAugmenter,
)
from rag_engine.query_embedding.local_query_embedder import (
    LocalQueryEmbedder,
)
from rag_engine.rag_pipeline.default_rag_pipeline import (
    DefaultRAGPipeline,
)
from rag_engine.rag_pipeline.rag_pipeline import RAGPipeline
from rag_engine.retrieval.postgres_retriever import (
    PostgresRetriever,
)


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 3


@lru_cache(maxsize=1)
def create_rag_pipeline() -> RAGPipeline:
    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )

    query_embedder = LocalQueryEmbedder(
        model_name=EMBEDDING_MODEL_NAME,
        model=embedding_model,
    )

    retriever = PostgresRetriever()

    prompt_augmenter = DefaultPromptAugmenter()

    llm = OllamaLLM(
        base_url=settings.ollama.base_url,
        model_name=settings.ollama.model_name,
        timeout_seconds=(
            settings.ollama.timeout_seconds
        ),
    )

    return DefaultRAGPipeline(
        query_embedder=query_embedder,
        retriever=retriever,
        prompt_augmenter=prompt_augmenter,
        llm=llm,
        top_k=DEFAULT_TOP_K,
    )