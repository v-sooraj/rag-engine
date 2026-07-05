from rag_engine.query_embedding.local_query_embedder import (
    LocalQueryEmbedder,
)


def test_real_local_query_embedding_generation():
    embedder = LocalQueryEmbedder(
        model_name="all-MiniLM-L6-v2",
    )

    embedding = embedder.embed(
        "How do vector databases work?"
    )

    assert len(embedding) == 384

    assert all(
        isinstance(value, float)
        for value in embedding
    )