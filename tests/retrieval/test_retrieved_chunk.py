from uuid import uuid4

import pytest
from pydantic import ValidationError

from rag_engine.retrieval.retrieved_chunk import RetrievedChunk


def test_retrieved_chunk_is_created_with_valid_values():
    chunk_id = uuid4()
    document_id = uuid4()

    retrieved_chunk = RetrievedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        content="Vector databases store embeddings.",
        chunk_index=0,
        distance=0.12,
    )

    assert retrieved_chunk.chunk_id == chunk_id
    assert retrieved_chunk.document_id == document_id
    assert (
        retrieved_chunk.content
        == "Vector databases store embeddings."
    )
    assert retrieved_chunk.chunk_index == 0
    assert retrieved_chunk.distance == 0.12


def test_retrieved_chunk_rejects_empty_content():
    with pytest.raises(ValidationError):
        RetrievedChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="",
            chunk_index=0,
            distance=0.12,
        )


def test_retrieved_chunk_rejects_negative_chunk_index():
    with pytest.raises(ValidationError):
        RetrievedChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Valid content",
            chunk_index=-1,
            distance=0.12,
        )


def test_retrieved_chunk_rejects_negative_distance():
    with pytest.raises(ValidationError):
        RetrievedChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            content="Valid content",
            chunk_index=0,
            distance=-0.1,
        )


def test_retrieved_chunk_is_immutable():
    retrieved_chunk = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        content="Valid content",
        chunk_index=0,
        distance=0.12,
    )

    with pytest.raises(ValidationError):
        retrieved_chunk.distance = 0.5