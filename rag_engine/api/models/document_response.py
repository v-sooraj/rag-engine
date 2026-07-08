from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    document_id: UUID