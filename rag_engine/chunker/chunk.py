from pydantic import BaseModel, ConfigDict, Field

from rag_engine.loader.document import DocumentMetadata


class ChunkMetadata(BaseModel):

    model_config = ConfigDict(frozen=True)

    chunk_index: int = Field(ge=0)
    document_metadata: DocumentMetadata

class Chunk(BaseModel):

    model_config = ConfigDict(frozen=True)

    content: str = Field(min_length=1)
    metadata: ChunkMetadata
