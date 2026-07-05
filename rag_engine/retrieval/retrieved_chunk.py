from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: UUID
    document_id: UUID
    content: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    distance: float = Field(ge=0)