import logging
from time import perf_counter

from rag_engine.observability.context import (
    get_request_id,
)
from rag_engine.rag_pipeline.rag_pipeline import (
    RAGPipeline,
)
from rag_engine.llm.generated_answer import (
    GeneratedAnswer,
)


logger = logging.getLogger(
    __name__
)


class ObservedRAGPipeline(
    RAGPipeline
):

    def __init__(
        self,
        delegate: RAGPipeline,
    ):
        self._delegate = delegate

    def answer(
        self,
        query: str,
    ) -> GeneratedAnswer:
        request_id = get_request_id()

        started_at = perf_counter()

        logger.info(
            "rag.started",
            extra=self._build_extra(
                request_id=request_id,
            ),
        )

        try:
            result = self._delegate.answer(
                query
            )

        except Exception as error:
            duration_ms = self._duration_ms(
                started_at
            )

            logger.exception(
                "rag.failed",
                extra=self._build_extra(
                    request_id=request_id,
                    duration_ms=duration_ms,
                    exception_type=(
                        type(error).__name__
                    ),
                ),
            )

            raise

        duration_ms = self._duration_ms(
            started_at
        )

        logger.info(
            "rag.completed",
            extra=self._build_extra(
                request_id=request_id,
                duration_ms=duration_ms,
            ),
        )

        return result

    @staticmethod
    def _duration_ms(
        started_at: float,
    ) -> float:
        return round(
            (
                perf_counter()
                - started_at
            )
            * 1000,
            2,
        )

    @staticmethod
    def _build_extra(
        **fields: object,
    ) -> dict[str, object]:
        return {
            key: value
            for key, value in fields.items()
            if value is not None
        }