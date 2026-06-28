from pathlib import Path

import fitz

from rag_engine.loader.document import Document, DocumentMetadata
from rag_engine.loader.document_loader import DocumentLoader


class PdfLoader(DocumentLoader):

    def load(self, path: str) -> Document:
        with fitz.open(path) as pdf:
            content = self._extract_content(pdf)
            metadata = self._extract_metadata(pdf, Path(path).name)
        return Document(
            content=content,
            metadata=metadata,
        )

    def _extract_content(self, pdf: fitz.Document) -> str:
        pages = []

        for page in pdf:
            text = page.get_text("text")

            if text.strip():
                pages.append(text)

        return "\n".join(pages)

    def _extract_metadata(
        self,
        pdf: fitz.Document,
        filename: str
    ) -> DocumentMetadata:

        return DocumentMetadata(
            filename=filename,
            page_count=pdf.page_count,
            title=pdf.metadata.get("title") or None,
            author=pdf.metadata.get("author") or None,
            language=pdf.metadata.get("language") or None,
        )

