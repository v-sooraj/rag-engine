
"""
Given: a valid PDF document
When: the PDF loader loads the document
Then: a populated Document model is returned
"""
from rag_engine.loader.document_loader import DocumentLoader
from rag_engine.loader.pdf_loader import PdfLoader


def test_load_returns_document_from_pdf():
    doc_loader: DocumentLoader = PdfLoader()

    document = doc_loader.load("tests/resources/sample.pdf")

    assert document.content.strip()
    assert document.metadata is not None
    assert document.metadata.filename == "sample.pdf"
    assert document.metadata.page_count > 1

