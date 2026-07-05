CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    title TEXT,
    author TEXT,
    language TEXT,
    page_count INTEGER NOT NULL CHECK (page_count > 0),
    content_hash TEXT NOT NULL UNIQUE
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    content TEXT NOT NULL CHECK (length(content) > 0),
    embedding VECTOR(384) NOT NULL,

    CONSTRAINT fk_chunks_document
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_chunks_document_chunk_index
        UNIQUE (document_id, chunk_index)
);