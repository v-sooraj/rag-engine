from uuid import uuid4

import pytest

from rag_engine.prompt_augmentation.default_prompt_augmenter import (
    DefaultPromptAugmenter,
)
from rag_engine.retrieval.retrieved_chunk import RetrievedChunk


def create_retrieved_chunk(
    content: str,
    chunk_index: int,
    distance: float,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        content=content,
        chunk_index=chunk_index,
        distance=distance,
    )


def test_augment_returns_structured_augmented_prompt():
    augmenter = DefaultPromptAugmenter()

    chunks = [
        create_retrieved_chunk(
            content="Vector databases store embeddings.",
            chunk_index=0,
            distance=0.12,
        ),
    ]

    prompt = augmenter.augment(
        query="What do vector databases store?",
        chunks=chunks,
    )

    assert (
        prompt.system_instruction
        == DefaultPromptAugmenter.SYSTEM_INSTRUCTION
    )
    assert (
        prompt.context
        == (
            "[CONTEXT 1]\n"
            "Vector databases store embeddings."
        )
    )
    assert (
        prompt.question
        == "What do vector databases store?"
    )


def test_augment_preserves_retrieval_order():
    augmenter = DefaultPromptAugmenter()

    chunks = [
        create_retrieved_chunk(
            content="Most relevant result",
            chunk_index=10,
            distance=0.10,
        ),
        create_retrieved_chunk(
            content="Second most relevant result",
            chunk_index=2,
            distance=0.20,
        ),
        create_retrieved_chunk(
            content="Third most relevant result",
            chunk_index=0,
            distance=0.30,
        ),
    ]

    prompt = augmenter.augment(
        query="Test query",
        chunks=chunks,
    )

    assert prompt.context == (
        "[CONTEXT 1]\n"
        "Most relevant result\n\n"
        "[CONTEXT 2]\n"
        "Second most relevant result\n\n"
        "[CONTEXT 3]\n"
        "Third most relevant result"
    )


def test_augment_preserves_chunk_boundaries():
    augmenter = DefaultPromptAugmenter()

    chunks = [
        create_retrieved_chunk(
            content="First chunk",
            chunk_index=0,
            distance=0.10,
        ),
        create_retrieved_chunk(
            content="Second chunk",
            chunk_index=1,
            distance=0.20,
        ),
    ]

    prompt = augmenter.augment(
        query="Test query",
        chunks=chunks,
    )

    assert "[CONTEXT 1]\nFirst chunk" in prompt.context
    assert "[CONTEXT 2]\nSecond chunk" in prompt.context


def test_augment_does_not_include_retrieval_metadata_in_context():
    augmenter = DefaultPromptAugmenter()

    chunk = create_retrieved_chunk(
        content="Relevant evidence",
        chunk_index=7,
        distance=0.123456,
    )

    prompt = augmenter.augment(
        query="Test query",
        chunks=[chunk],
    )

    assert prompt.context == (
        "[CONTEXT 1]\n"
        "Relevant evidence"
    )

    assert str(chunk.chunk_id) not in prompt.context
    assert str(chunk.document_id) not in prompt.context
    assert str(chunk.chunk_index) not in prompt.context
    assert str(chunk.distance) not in prompt.context


def test_augment_allows_empty_retrieved_chunks():
    augmenter = DefaultPromptAugmenter()

    prompt = augmenter.augment(
        query="What is RAG?",
        chunks=[],
    )

    assert (
        prompt.system_instruction
        == DefaultPromptAugmenter.SYSTEM_INSTRUCTION
    )
    assert prompt.context == ""
    assert prompt.question == "What is RAG?"


def test_augment_rejects_empty_query():
    augmenter = DefaultPromptAugmenter()

    with pytest.raises(
        ValueError,
        match="query must not be empty",
    ):
        augmenter.augment(
            query="",
            chunks=[],
        )


def test_augment_rejects_blank_query():
    augmenter = DefaultPromptAugmenter()

    with pytest.raises(
        ValueError,
        match="query must not be empty",
    ):
        augmenter.augment(
            query="   ",
            chunks=[],
        )


def test_augment_preserves_original_query():
    augmenter = DefaultPromptAugmenter()

    query = "  What is retrieval augmented generation?  "

    prompt = augmenter.augment(
        query=query,
        chunks=[],
    )

    assert prompt.question == query