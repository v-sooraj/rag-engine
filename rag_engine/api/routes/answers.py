from typing import Annotated

from fastapi import APIRouter, Depends

from rag_engine.api.dependencies import (
    get_rag_pipeline,
)
from rag_engine.api.models.answer_request import (
    AnswerRequest,
)
from rag_engine.api.models.answer_response import (
    AnswerResponse,
)
from rag_engine.rag_pipeline.rag_pipeline import (
    RAGPipeline,
)


router = APIRouter(
    prefix="/answers",
    tags=["answers"],
)


@router.post(
    "",
    response_model=AnswerResponse,
)
def answer_question(
    request: AnswerRequest,
    pipeline: Annotated[
        RAGPipeline,
        Depends(get_rag_pipeline),
    ],
) -> AnswerResponse:
    generated_answer = pipeline.answer(
        request.query
    )

    return AnswerResponse(
        answer=generated_answer.content
    )