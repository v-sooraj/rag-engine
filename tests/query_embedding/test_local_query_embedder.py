from unittest.mock import Mock

import numpy as np
import pytest

from rag_engine.query_embedding.local_query_embedder import (
    LocalQueryEmbedder,
)


def test_embed_returns_query_embedding():
    model = Mock()

    model.encode.return_value = np.array(
        [0.1, 0.2, 0.3]
    )

    embedder = LocalQueryEmbedder(
        model_name="test-model",
        model=model,
    )

    embedding = embedder.embed(
        "How do vector databases work?"
    )

    assert embedding == [
        0.1,
        0.2,
        0.3,
    ]

    model.encode.assert_called_once_with(
        "How do vector databases work?"
    )


def test_embed_rejects_empty_query_before_calling_model():
    model = Mock()

    embedder = LocalQueryEmbedder(
        model_name="test-model",
        model=model,
    )

    with pytest.raises(
        ValueError,
        match="query must not be empty",
    ):
        embedder.embed("")

    model.encode.assert_not_called()


def test_embed_rejects_blank_query_before_calling_model():
    model = Mock()

    embedder = LocalQueryEmbedder(
        model_name="test-model",
        model=model,
    )

    with pytest.raises(
        ValueError,
        match="query must not be empty",
    ):
        embedder.embed("   ")

    model.encode.assert_not_called()