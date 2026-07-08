from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from rag_engine.api.adapters.document_upload_adapter import (
    DocumentUploadAdapter,
)
from rag_engine.api.dependencies import (
    get_ingestion_pipeline,
)
from rag_engine.api.models.document_response import (
    DocumentResponse,
)
from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=201,
)
def ingest_document(
    file: Annotated[
        UploadFile,
        File(),
    ],
    pipeline: Annotated[
        IngestionPipeline,
        Depends(get_ingestion_pipeline),
    ],
) -> DocumentResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=415,
            detail="Only PDF files are supported",
        )

    adapter = DocumentUploadAdapter(
        ingestion_pipeline=pipeline
    )

    document_id = adapter.ingest(
        file
    )

    return DocumentResponse(
        document_id=document_id
    )