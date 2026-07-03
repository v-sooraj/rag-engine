import pytest

from rag_engine.chunker.document_chunker import DocumentChunker
from rag_engine.chunker.recursive_document_chunker import (
    RecursiveDocumentChunker,
)
from rag_engine.loader.document import Document, DocumentMetadata
from rag_engine.loader.document_loader import DocumentLoader
from rag_engine.loader.pdf_loader import PdfLoader

"""
Given: invalid recursive chunker configuration
When: the chunker is constructed
Then: configuration validation fails immediately
"""
@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [
        (0, 0),
        (-1, 0),
        (500, -1),
        (500, 500),
        (500, 600),
    ],
)
def test_invalid_chunker_configuration_raises_error(
    chunk_size: int,
    chunk_overlap: int,
):
    with pytest.raises(ValueError):
        RecursiveDocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

"""
Given: a document smaller than chunk_size
When: chunk() is called
Then: exactly one chunk is returned with index 0 and the original document metadata
"""
def test_small_document_returns_single_chunk():
    document = Document(
        content="This is test content",
        metadata=DocumentMetadata(
            filename="test.pdf",
            page_count=1,
        ),
    )

    doc_chunker: DocumentChunker = RecursiveDocumentChunker(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = doc_chunker.chunk(document)

    assert len(chunks) == 1
    assert chunks[0].content == document.content
    assert chunks[0].metadata.chunk_index == 0
    assert chunks[0].metadata.document_metadata is document.metadata

"""
Given: a document containing an oversized paragraph
When: recursive chunking is performed
Then: the oversized paragraph is split using a weaker separator
      and every resulting chunk stays within chunk_size
"""
def test_oversized_paragraph_uses_weaker_separator():
    document = Document(
        content=(
            "First paragraph.\n\n"
            "This is a longer paragraph containing several words "
            "that cannot fit within the configured chunk size.\n\n"
            "Final paragraph."
        ),
        metadata=DocumentMetadata(
            filename="test.pdf",
            page_count=1,
        ),
    )

    doc_chunker: DocumentChunker = RecursiveDocumentChunker(
        chunk_size=50,
        chunk_overlap=0,
    )

    chunks = doc_chunker.chunk(document)

    assert len(chunks) > 1
    assert all(len(chunk.content) <= 50 for chunk in chunks)
    assert [chunk.metadata.chunk_index for chunk in chunks] == list(
        range(len(chunks))
    )

"""
Given: a document containing multiple small paragraphs
When: recursive chunking is performed
Then: adjacent pieces are merged while staying within chunk_size
"""
def test_small_pieces_are_merged():
    document = Document(
        content=(
            "First paragraph.\n\n"
            "Second paragraph.\n\n"
            "Third paragraph."
        ),
        metadata=DocumentMetadata(
            filename="test.pdf",
            page_count=1,
        ),
    )

    doc_chunker: DocumentChunker = RecursiveDocumentChunker(
        chunk_size=50,
        chunk_overlap=0,
    )

    chunks = doc_chunker.chunk(document)

    assert len(chunks) == 2
    assert chunks[0].content == (
        "First paragraph.\n\n"
        "Second paragraph.\n\n"
    )
    assert chunks[1].content == "Third paragraph."

"""
Given: content that produces multiple chunks
When: chunking is performed with overlap
Then: the end of the previous chunk is repeated at the start of the next chunk
"""
def test_chunks_include_configured_overlap():
    document = Document(
        content=(
            "First paragraph.\n\n"
            "Second paragraph.\n\n"
            "Third paragraph."
        ),
        metadata=DocumentMetadata(
            filename="test.pdf",
            page_count=1,
        ),
    )

    doc_chunker: DocumentChunker = RecursiveDocumentChunker(
        chunk_size=50,
        chunk_overlap=10,
    )

    chunks = doc_chunker.chunk(document)

    assert len(chunks) == 2
    assert chunks[1].content.startswith(chunks[0].content[-10:])
    assert all(len(chunk.content) <= 50 for chunk in chunks)

"""
Given: a valid PDF document
When: the document is loaded and recursively chunked
Then: validated chunks are produced while preserving document metadata
"""
def test_pdf_loading_and_chunking_pipeline():
    loader: DocumentLoader = PdfLoader()
    chunker: DocumentChunker = RecursiveDocumentChunker(
        chunk_size=500,
        chunk_overlap=50,
    )

    document = loader.load("tests/resources/sample.pdf")
    chunks = chunker.chunk(document)

    assert len(chunks) > 1
    assert all(chunk.content.strip() for chunk in chunks)
    assert all(len(chunk.content) <= 500 for chunk in chunks)

    assert [chunk.metadata.chunk_index for chunk in chunks] == list(
        range(len(chunks))
    )

    assert all(
        chunk.metadata.document_metadata is document.metadata
        for chunk in chunks
    )