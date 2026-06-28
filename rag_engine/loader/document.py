from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    title: str | None = None
    language: str | None = None
    author: str | None = None
    page_count: int = Field(ge=1)
    filename: str = Field(min_length=1)

class Document(BaseModel):
    content: str = Field(min_length=1)
    metadata: DocumentMetadata
