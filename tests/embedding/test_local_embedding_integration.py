from rag_engine.chunker.chunk import Chunk, ChunkMetadata
from rag_engine.embedding.local_chunk_embedder import LocalChunkEmbedder
from rag_engine.loader.document import DocumentMetadata


def test_real_local_embedding_generation():
    document_metadata = DocumentMetadata(
        filename="test.pdf",
        page_count=1,
    )

    chunks = [
        Chunk(
            content="Vector databases store embeddings for similarity search.",
            metadata=ChunkMetadata(
                chunk_index=0,
                document_metadata=document_metadata,
            ),
        ),
        Chunk(
            content="PostgreSQL can support vector search using pgvector.",
            metadata=ChunkMetadata(
                chunk_index=1,
                document_metadata=document_metadata,
            ),
        ),
    ]

    embedder = LocalChunkEmbedder(
        model_name="all-MiniLM-L6-v2",
        batch_size=2,
    )

    embedded_chunks = embedder.embed(chunks)

    assert len(embedded_chunks) == 2

    assert embedded_chunks[0].chunk is chunks[0]
    assert embedded_chunks[1].chunk is chunks[1]

    assert len(embedded_chunks[0].embedding) > 0
    assert len(embedded_chunks[1].embedding) > 0

    assert len(embedded_chunks[0].embedding) == len(
        embedded_chunks[1].embedding
    )

    assert all(
        isinstance(value, float)
        for embedded_chunk in embedded_chunks
        for value in embedded_chunk.embedding
    )