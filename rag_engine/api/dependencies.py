from rag_engine.composition.application import (
    create_rag_pipeline,
)
from rag_engine.rag_pipeline.rag_pipeline import RAGPipeline


def get_rag_pipeline() -> RAGPipeline:
    return create_rag_pipeline()