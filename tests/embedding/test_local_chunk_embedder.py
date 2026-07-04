from unittest.mock import Mock

import numpy as np
import pytest

from rag_engine.chunker.chunk import Chunk, ChunkMetadata
from rag_engine.embedding.local_chunk_embedder import LocalChunkEmbedder
from rag_engine.loader.document import DocumentMetadata


def create_chunks() -> list[Chunk]:
    document_metadata = DocumentMetadata(
        filename="test.pdf",
        page_count=1,
    )

    return [
        Chunk(
            content="First chunk",
            metadata=ChunkMetadata(
                chunk_index=0,
                document_metadata=document_metadata,
            ),
        ),
        Chunk(
            content="Second chunk",
            metadata=ChunkMetadata(
                chunk_index=1,
                document_metadata=document_metadata,
            ),
        ),
    ]


"""
Given: an empty list of chunks
When: embed() is called
Then: an empty list is returned without invoking the model
"""
def test_empty_chunk_list_returns_empty_list():
    mock_model = Mock()

    embedder = LocalChunkEmbedder(
        model_name="test-model",
        model=mock_model,
    )

    embedded_chunks = embedder.embed([])

    assert embedded_chunks == []
    mock_model.encode.assert_not_called()


"""
Given: multiple chunks
When: local embedding is performed
Then: each chunk is paired with its corresponding embedding
"""
def test_embed_returns_embedded_chunks():
    chunks = create_chunks()

    mock_model = Mock()

    mock_model.encode.return_value = np.array(
        [
            [0.1, 0.2],
            [0.3, 0.4],
        ]
    )

    embedder = LocalChunkEmbedder(
        model_name="test-model",
        batch_size=16,
        model=mock_model,
    )

    embedded_chunks = embedder.embed(chunks)

    assert len(embedded_chunks) == 2

    assert embedded_chunks[0].chunk is chunks[0]
    assert embedded_chunks[0].embedding == [0.1, 0.2]

    assert embedded_chunks[1].chunk is chunks[1]
    assert embedded_chunks[1].embedding == [0.3, 0.4]

    mock_model.encode.assert_called_once_with(
        ["First chunk", "Second chunk"],
        batch_size=16,
        show_progress_bar=False,
    )


"""
Given: fewer embeddings than input chunks
When: embed() is called
Then: the entire embedding operation fails
"""
def test_embed_raises_error_when_embedding_count_does_not_match():
    chunks = create_chunks()

    mock_model = Mock()

    mock_model.encode.return_value = np.array(
        [
            [0.1, 0.2],
        ]
    )

    embedder = LocalChunkEmbedder(
        model_name="test-model",
        model=mock_model,
    )

    with pytest.raises(
        ValueError,
        match="Embedding response count does not match input chunk count",
    ):
        embedder.embed(chunks)


"""
Given: an invalid batch size
When: the local embedder is constructed
Then: configuration validation fails immediately
"""
@pytest.mark.parametrize(
    "batch_size",
    [
        0,
        -1,
    ],
)
def test_invalid_batch_size_raises_error(batch_size: int):
    mock_model = Mock()

    with pytest.raises(
        ValueError,
        match="batch_size must be greater than 0",
    ):
        LocalChunkEmbedder(
            model_name="test-model",
            batch_size=batch_size,
            model=mock_model,
        )