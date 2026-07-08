from functools import lru_cache

from sentence_transformers import SentenceTransformer

from rag_engine.chunker.recursive_document_chunker import (
    RecursiveDocumentChunker,
)
from rag_engine.config.settings import settings
from rag_engine.embedding.local_chunk_embedder import (
    LocalChunkEmbedder,
)
from rag_engine.ingestion_pipeline.default_ingestion_pipeline import (
    DefaultIngestionPipeline,
)
from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)
from rag_engine.llm.ollama_llm import OllamaLLM
from rag_engine.loader.pdf_loader import PdfLoader
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
from rag_engine.vector_store.postgres_vector_store import (
    PostgresVectorStore,
)


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 32

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

DEFAULT_TOP_K = 3


@lru_cache(maxsize=1)
def create_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )


@lru_cache(maxsize=1)
def create_ingestion_pipeline() -> IngestionPipeline:
    embedding_model = create_embedding_model()

    chunk_embedder = LocalChunkEmbedder(
        model_name=EMBEDDING_MODEL_NAME,
        batch_size=EMBEDDING_BATCH_SIZE,
        model=embedding_model,
    )

    return DefaultIngestionPipeline(
        document_loader=PdfLoader(),
        document_chunker=RecursiveDocumentChunker(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        ),
        chunk_embedder=chunk_embedder,
        vector_store=PostgresVectorStore(),
    )


@lru_cache(maxsize=1)
def create_rag_pipeline() -> RAGPipeline:
    embedding_model = create_embedding_model()

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