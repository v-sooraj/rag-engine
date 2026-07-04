from pydantic import BaseModel, Field, ConfigDict

from rag_engine.chunker.chunk import Chunk


class EmbeddedChunk(BaseModel):

    model_config = ConfigDict(frozen=True)

    chunk: Chunk
    embedding: list[float] = Field(min_length=1)