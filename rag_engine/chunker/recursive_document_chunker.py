from rag_engine.chunker.chunk import Chunk, ChunkMetadata
from rag_engine.chunker.document_chunker import DocumentChunker
from rag_engine.loader.document import Document


class RecursiveDocumentChunker(DocumentChunker):

    chunk_size: int
    chunk_overlap: int

    separators = ["\n\n", "\n", " ", ""]

    def __init__(self, chunk_size: int, chunk_overlap: int):

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: Document) -> list[Chunk]:

        pieces = self._split(document.content)
        chunk_contents = self._merge(pieces)

        return [
            Chunk(
                content=content,
                metadata=ChunkMetadata(
                    chunk_index=index,
                    document_metadata=document.metadata,
                ),
            )
            for index, content in enumerate(chunk_contents)
        ]

    def _split(self, text: str, separator_index: int = 0) -> list[str]:

        if len(text) <= self.chunk_size:
            return [text]

        separator = self.separators[separator_index]

        if separator == "":
            return [
                text[start:start + self.chunk_size]
                for start in range(0, len(text), self.chunk_size)
            ]

        if separator not in text:
            return self._split(text, separator_index + 1)

        raw_splits = text.split(separator)
        pieces = []

        for index, split in enumerate(raw_splits):
            if index < len(raw_splits) - 1:
                piece = split + separator
            else:
                piece = split

            if not piece:
                continue

            if len(piece) <= self.chunk_size:
                pieces.append(piece)
            else:
                pieces.extend(
                    self._split(piece, separator_index + 1)
                )

        return pieces

    def _merge(self, pieces: list[str]) -> list[str]:
        if not pieces:
            return []

        chunks = []
        current_chunk = ""

        for piece in pieces:

            if len(current_chunk) + len(piece) <= self.chunk_size:
                current_chunk += piece
                continue

            if current_chunk:
                chunks.append(current_chunk)

            available_overlap = self.chunk_size - len(piece)

            overlap_size = min(
                self.chunk_overlap,
                max(available_overlap, 0)
            )

            overlap = (
                current_chunk[-overlap_size:]
                if overlap_size > 0
                else ""
            )

            current_chunk = overlap + piece

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
