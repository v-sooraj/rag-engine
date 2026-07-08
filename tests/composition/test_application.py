from unittest.mock import Mock, patch

import pytest

from rag_engine.composition.application import (
    create_embedding_model,
    create_ingestion_pipeline,
    create_rag_pipeline,
)
from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)
from rag_engine.rag_pipeline.rag_pipeline import (
    RAGPipeline,
)


@pytest.fixture(autouse=True)
def clear_composition_caches():
    create_ingestion_pipeline.cache_clear()
    create_rag_pipeline.cache_clear()
    create_embedding_model.cache_clear()

    yield

    create_ingestion_pipeline.cache_clear()
    create_rag_pipeline.cache_clear()
    create_embedding_model.cache_clear()


@patch(
    "rag_engine.composition.application.SentenceTransformer"
)
def test_create_embedding_model_reuses_same_instance(
    sentence_transformer: Mock,
):
    model = Mock()
    sentence_transformer.return_value = model

    first = create_embedding_model()
    second = create_embedding_model()

    assert first is model
    assert second is model

    sentence_transformer.assert_called_once()


@patch(
    "rag_engine.composition.application.PostgresVectorStore"
)
@patch(
    "rag_engine.composition.application.LocalChunkEmbedder"
)
@patch(
    "rag_engine.composition.application.RecursiveDocumentChunker"
)
@patch(
    "rag_engine.composition.application.PdfLoader"
)
@patch(
    "rag_engine.composition.application.create_embedding_model"
)
def test_create_ingestion_pipeline_returns_ingestion_pipeline(
    create_model: Mock,
    pdf_loader: Mock,
    recursive_document_chunker: Mock,
    local_chunk_embedder: Mock,
    postgres_vector_store: Mock,
):
    create_model.return_value = Mock()

    pipeline = create_ingestion_pipeline()

    assert isinstance(
        pipeline,
        IngestionPipeline,
    )


@patch(
    "rag_engine.composition.application.PostgresVectorStore"
)
@patch(
    "rag_engine.composition.application.LocalChunkEmbedder"
)
@patch(
    "rag_engine.composition.application.RecursiveDocumentChunker"
)
@patch(
    "rag_engine.composition.application.PdfLoader"
)
@patch(
    "rag_engine.composition.application.create_embedding_model"
)
def test_create_ingestion_pipeline_reuses_same_instance(
    create_model: Mock,
    pdf_loader: Mock,
    recursive_document_chunker: Mock,
    local_chunk_embedder: Mock,
    postgres_vector_store: Mock,
):
    create_model.return_value = Mock()

    first = create_ingestion_pipeline()
    second = create_ingestion_pipeline()

    assert first is second


@patch(
    "rag_engine.composition.application.PostgresVectorStore"
)
@patch(
    "rag_engine.composition.application.LocalChunkEmbedder"
)
@patch(
    "rag_engine.composition.application.RecursiveDocumentChunker"
)
@patch(
    "rag_engine.composition.application.PdfLoader"
)
@patch(
    "rag_engine.composition.application.create_embedding_model"
)
def test_create_ingestion_pipeline_uses_shared_embedding_model(
    create_model: Mock,
    pdf_loader: Mock,
    recursive_document_chunker: Mock,
    local_chunk_embedder: Mock,
    postgres_vector_store: Mock,
):
    model = Mock()
    create_model.return_value = model

    create_ingestion_pipeline()

    local_chunk_embedder.assert_called_once()

    assert (
        local_chunk_embedder.call_args.kwargs["model"]
        is model
    )


@patch(
    "rag_engine.composition.application.OllamaLLM"
)
@patch(
    "rag_engine.composition.application.DefaultPromptAugmenter"
)
@patch(
    "rag_engine.composition.application.PostgresRetriever"
)
@patch(
    "rag_engine.composition.application.LocalQueryEmbedder"
)
@patch(
    "rag_engine.composition.application.create_embedding_model"
)
def test_create_rag_pipeline_returns_rag_pipeline(
    create_model: Mock,
    local_query_embedder: Mock,
    postgres_retriever: Mock,
    default_prompt_augmenter: Mock,
    ollama_llm: Mock,
):
    create_model.return_value = Mock()

    pipeline = create_rag_pipeline()

    assert isinstance(
        pipeline,
        RAGPipeline,
    )


@patch(
    "rag_engine.composition.application.OllamaLLM"
)
@patch(
    "rag_engine.composition.application.DefaultPromptAugmenter"
)
@patch(
    "rag_engine.composition.application.PostgresRetriever"
)
@patch(
    "rag_engine.composition.application.LocalQueryEmbedder"
)
@patch(
    "rag_engine.composition.application.create_embedding_model"
)
def test_create_rag_pipeline_reuses_same_instance(
    create_model: Mock,
    local_query_embedder: Mock,
    postgres_retriever: Mock,
    default_prompt_augmenter: Mock,
    ollama_llm: Mock,
):
    create_model.return_value = Mock()

    first = create_rag_pipeline()
    second = create_rag_pipeline()

    assert first is second


@patch(
    "rag_engine.composition.application.OllamaLLM"
)
@patch(
    "rag_engine.composition.application.DefaultPromptAugmenter"
)
@patch(
    "rag_engine.composition.application.PostgresRetriever"
)
@patch(
    "rag_engine.composition.application.LocalQueryEmbedder"
)
@patch(
    "rag_engine.composition.application.create_embedding_model"
)
def test_create_rag_pipeline_uses_shared_embedding_model(
    create_model: Mock,
    local_query_embedder: Mock,
    postgres_retriever: Mock,
    default_prompt_augmenter: Mock,
    ollama_llm: Mock,
):
    model = Mock()
    create_model.return_value = model

    create_rag_pipeline()

    local_query_embedder.assert_called_once()

    assert (
        local_query_embedder.call_args.kwargs["model"]
        is model
    )


@patch(
    "rag_engine.composition.application.OllamaLLM"
)
@patch(
    "rag_engine.composition.application.DefaultPromptAugmenter"
)
@patch(
    "rag_engine.composition.application.PostgresRetriever"
)
@patch(
    "rag_engine.composition.application.LocalQueryEmbedder"
)
@patch(
    "rag_engine.composition.application.PostgresVectorStore"
)
@patch(
    "rag_engine.composition.application.LocalChunkEmbedder"
)
@patch(
    "rag_engine.composition.application.RecursiveDocumentChunker"
)
@patch(
    "rag_engine.composition.application.PdfLoader"
)
@patch(
    "rag_engine.composition.application.create_embedding_model"
)
def test_both_pipelines_receive_same_embedding_model(
    create_model: Mock,
    pdf_loader: Mock,
    recursive_document_chunker: Mock,
    local_chunk_embedder: Mock,
    postgres_vector_store: Mock,
    local_query_embedder: Mock,
    postgres_retriever: Mock,
    default_prompt_augmenter: Mock,
    ollama_llm: Mock,
):
    model = Mock()
    create_model.return_value = model

    create_ingestion_pipeline()
    create_rag_pipeline()

    chunk_model = (
        local_chunk_embedder.call_args.kwargs["model"]
    )

    query_model = (
        local_query_embedder.call_args.kwargs["model"]
    )

    assert chunk_model is model
    assert query_model is model
    assert chunk_model is query_model