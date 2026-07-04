from rag_engine.chunker.document_chunker import DocumentChunker
from rag_engine.chunker.recursive_document_chunker import (
    RecursiveDocumentChunker,
)
from rag_engine.embedding.chunk_embedder import ChunkEmbedder
from rag_engine.embedding.local_chunk_embedder import LocalChunkEmbedder
from rag_engine.loader.document_loader import DocumentLoader
from rag_engine.loader.pdf_loader import PdfLoader


"""
Given: a valid PDF document
When: the document is loaded, chunked, and embedded
Then: immutable embedded chunks with real vectors are produced
"""
def test_pdf_loading_chunking_and_embedding_pipeline():
    loader: DocumentLoader = PdfLoader()

    chunker: DocumentChunker = RecursiveDocumentChunker(
        chunk_size=500,
        chunk_overlap=50,
    )

    embedder: ChunkEmbedder = LocalChunkEmbedder(
        model_name="all-MiniLM-L6-v2",
        batch_size=32,
    )

    document = loader.load("tests/resources/sample.pdf")
    chunks = chunker.chunk(document)
    embedded_chunks = embedder.embed(chunks)

    assert len(embedded_chunks) == len(chunks)
    assert len(embedded_chunks) > 0

    assert all(
        embedded_chunk.chunk is chunk
        for embedded_chunk, chunk in zip(
            embedded_chunks,
            chunks,
        )
    )

    assert all(
        len(embedded_chunk.embedding) == 384
        for embedded_chunk in embedded_chunks
    )

    assert all(
        isinstance(value, float)
        for embedded_chunk in embedded_chunks
        for value in embedded_chunk.embedding
    )