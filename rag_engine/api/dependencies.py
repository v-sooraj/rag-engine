from rag_engine.composition.application import (
    create_ingestion_pipeline,
    create_rag_pipeline,
)
from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)
from rag_engine.rag_pipeline.rag_pipeline import (
    RAGPipeline,
)


def get_ingestion_pipeline() -> IngestionPipeline:
    return create_ingestion_pipeline()


def get_rag_pipeline() -> RAGPipeline:
    return create_rag_pipeline()