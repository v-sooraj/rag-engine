import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)

from rag_engine.observability.context import (
    reset_request_id,
    set_request_id,
)


logger = logging.getLogger(
    __name__
)


REQUEST_ID_HEADER = "X-Request-ID"


class RequestObservabilityMiddleware(
    BaseHTTPMiddleware
):

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = (
            request.headers.get(
                REQUEST_ID_HEADER
            )
            or str(uuid4())
        )

        token = set_request_id(
            request_id
        )

        started_at = perf_counter()

        common_fields = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }

        logger.info(
            "http.request.started",
            extra=common_fields,
        )

        try:
            response = await call_next(
                request
            )

        except Exception as error:
            duration_ms = self._duration_ms(
                started_at
            )

            logger.exception(
                "http.request.failed",
                extra={
                    **common_fields,
                    "duration_ms": duration_ms,
                    "exception_type": (
                        type(error).__name__
                    ),
                },
            )

            raise

        else:
            duration_ms = self._duration_ms(
                started_at
            )

            response.headers[
                REQUEST_ID_HEADER
            ] = request_id

            logger.info(
                "http.request.completed",
                extra={
                    **common_fields,
                    "status_code": (
                        response.status_code
                    ),
                    "duration_ms": duration_ms,
                },
            )

            return response

        finally:
            reset_request_id(
                token
            )

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