import logging
from pathlib import Path
from time import perf_counter
from uuid import UUID

from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)
from rag_engine.observability.context import (
    get_request_id,
)


logger = logging.getLogger(
    __name__
)


class ObservedIngestionPipeline(
    IngestionPipeline
):

    def __init__(
        self,
        delegate: IngestionPipeline,
    ):
        self._delegate = delegate

    def ingest(
        self,
        path: str,
    ) -> UUID:
        request_id = get_request_id()

        started_at = perf_counter()

        logger.info(
            "ingestion.started",
            extra=self._build_extra(
                request_id=request_id,
                document_filename=Path(path).name,
            ),
        )

        try:
            document_id = (
                self._delegate.ingest(
                    path
                )
            )

        except Exception as error:
            duration_ms = self._duration_ms(
                started_at
            )

            logger.exception(
                "ingestion.failed",
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
            "ingestion.completed",
            extra=self._build_extra(
                request_id=request_id,
                document_id=str(document_id),
                duration_ms=duration_ms,
            ),
        )

        return document_id

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