from unittest.mock import Mock

import pytest

from rag_engine.llm.generated_answer import GeneratedAnswer
from rag_engine.llm.llm import LLM
from rag_engine.prompt_augmentation.augmented_prompt import AugmentedPrompt
from rag_engine.prompt_augmentation.prompt_augmenter import PromptAugmenter
from rag_engine.query_embedding.query_embedder import QueryEmbedder
from rag_engine.rag_pipeline.default_rag_pipeline import (
    DefaultRAGPipeline,
)
from rag_engine.retrieval.retrieved_chunk import RetrievedChunk
from rag_engine.retrieval.retriever import Retriever


TOP_K = 3

QUERY = "What do vector databases store?"

QUERY_EMBEDDING = [
    0.1,
    0.2,
    0.3,
]

AUGMENTED_PROMPT = AugmentedPrompt(
    system_instruction=(
        "Answer using only the provided context."
    ),
    context=(
        "[CONTEXT 1]\n"
        "Vector databases store embeddings."
    ),
    question=QUERY,
)

GENERATED_ANSWER = GeneratedAnswer(
    content="Vector databases store embeddings."
)


def create_dependencies():
    query_embedder = Mock(
        spec=QueryEmbedder
    )
    retriever = Mock(
        spec=Retriever
    )
    prompt_augmenter = Mock(
        spec=PromptAugmenter
    )
    llm = Mock(
        spec=LLM
    )

    return (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )


def create_pipeline(
    query_embedder,
    retriever,
    prompt_augmenter,
    llm,
    top_k: int = TOP_K,
) -> DefaultRAGPipeline:
    return DefaultRAGPipeline(
        query_embedder=query_embedder,
        retriever=retriever,
        prompt_augmenter=prompt_augmenter,
        llm=llm,
        top_k=top_k,
    )


def configure_successful_pipeline(
    query_embedder,
    retriever,
    prompt_augmenter,
    llm,
):
    retrieved_chunks = [
        Mock(spec=RetrievedChunk)
    ]

    query_embedder.embed.return_value = (
        QUERY_EMBEDDING
    )

    retriever.retrieve.return_value = (
        retrieved_chunks
    )

    prompt_augmenter.augment.return_value = (
        AUGMENTED_PROMPT
    )

    llm.generate.return_value = (
        GENERATED_ANSWER
    )

    return retrieved_chunks


def test_answer_returns_generated_answer():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    configure_successful_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    answer = pipeline.answer(QUERY)

    assert answer is GENERATED_ANSWER


def test_answer_embeds_query():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    configure_successful_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    pipeline.answer(QUERY)

    query_embedder.embed.assert_called_once_with(
        QUERY
    )


def test_answer_retrieves_chunks_using_query_embedding_and_top_k():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    configure_successful_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    pipeline.answer(QUERY)

    retriever.retrieve.assert_called_once_with(
        query_embedding=QUERY_EMBEDDING,
        top_k=TOP_K,
    )


def test_answer_augments_original_query_and_retrieved_chunks():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    retrieved_chunks = (
        configure_successful_pipeline(
            query_embedder,
            retriever,
            prompt_augmenter,
            llm,
        )
    )

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    pipeline.answer(QUERY)

    prompt_augmenter.augment.assert_called_once_with(
        query=QUERY,
        chunks=retrieved_chunks,
    )


def test_answer_generates_from_augmented_prompt():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    configure_successful_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    pipeline.answer(QUERY)

    llm.generate.assert_called_once_with(
        AUGMENTED_PROMPT
    )


def test_answer_rejects_empty_query_before_calling_dependencies():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    with pytest.raises(
        ValueError,
        match="query must not be empty or blank",
    ):
        pipeline.answer("")

    query_embedder.embed.assert_not_called()
    retriever.retrieve.assert_not_called()
    prompt_augmenter.augment.assert_not_called()
    llm.generate.assert_not_called()


def test_answer_rejects_blank_query_before_calling_dependencies():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    with pytest.raises(
        ValueError,
        match="query must not be empty or blank",
    ):
        pipeline.answer("   ")

    query_embedder.embed.assert_not_called()
    retriever.retrieve.assert_not_called()
    prompt_augmenter.augment.assert_not_called()
    llm.generate.assert_not_called()


def test_constructor_rejects_zero_top_k():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        create_pipeline(
            query_embedder,
            retriever,
            prompt_augmenter,
            llm,
            top_k=0,
        )


def test_constructor_rejects_negative_top_k():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        create_pipeline(
            query_embedder,
            retriever,
            prompt_augmenter,
            llm,
            top_k=-1,
        )


def test_answer_continues_when_no_chunks_are_retrieved():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    query_embedder.embed.return_value = (
        QUERY_EMBEDDING
    )

    retriever.retrieve.return_value = []

    empty_context_prompt = AugmentedPrompt(
        system_instruction=(
            "Answer using only the provided context."
        ),
        context="",
        question=QUERY,
    )

    prompt_augmenter.augment.return_value = (
        empty_context_prompt
    )

    llm.generate.return_value = (
        GENERATED_ANSWER
    )

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    answer = pipeline.answer(QUERY)

    prompt_augmenter.augment.assert_called_once_with(
        query=QUERY,
        chunks=[],
    )

    llm.generate.assert_called_once_with(
        empty_context_prompt
    )

    assert answer is GENERATED_ANSWER


def test_answer_propagates_query_embedder_failure():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    error = RuntimeError(
        "query embedding failed"
    )

    query_embedder.embed.side_effect = error

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    with pytest.raises(
        RuntimeError,
        match="query embedding failed",
    ) as exception_info:
        pipeline.answer(QUERY)

    assert exception_info.value is error

    retriever.retrieve.assert_not_called()
    prompt_augmenter.augment.assert_not_called()
    llm.generate.assert_not_called()


def test_answer_propagates_retriever_failure():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    query_embedder.embed.return_value = (
        QUERY_EMBEDDING
    )

    error = RuntimeError(
        "retrieval failed"
    )

    retriever.retrieve.side_effect = error

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    with pytest.raises(
        RuntimeError,
        match="retrieval failed",
    ) as exception_info:
        pipeline.answer(QUERY)

    assert exception_info.value is error

    prompt_augmenter.augment.assert_not_called()
    llm.generate.assert_not_called()


def test_answer_propagates_prompt_augmenter_failure():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    query_embedder.embed.return_value = (
        QUERY_EMBEDDING
    )

    retriever.retrieve.return_value = []

    error = RuntimeError(
        "prompt augmentation failed"
    )

    prompt_augmenter.augment.side_effect = error

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    with pytest.raises(
        RuntimeError,
        match="prompt augmentation failed",
    ) as exception_info:
        pipeline.answer(QUERY)

    assert exception_info.value is error

    llm.generate.assert_not_called()


def test_answer_propagates_llm_failure():
    (
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    ) = create_dependencies()

    configure_successful_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    error = RuntimeError(
        "generation failed"
    )

    llm.generate.side_effect = error

    pipeline = create_pipeline(
        query_embedder,
        retriever,
        prompt_augmenter,
        llm,
    )

    with pytest.raises(
        RuntimeError,
        match="generation failed",
    ) as exception_info:
        pipeline.answer(QUERY)

    assert exception_info.value is error