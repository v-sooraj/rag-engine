from fastapi import FastAPI

from rag_engine.api.middleware.request_observability import (
    RequestObservabilityMiddleware,
)
from rag_engine.api.routes.answers import (
    router as answers_router,
)
from rag_engine.api.routes.documents import (
    router as documents_router,
)
from rag_engine.observability.logging_config import (
    configure_logging,
)


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="RAG Engine API",
        version="1.0.0",
    )

    app.add_middleware(
        RequestObservabilityMiddleware
    )

    app.include_router(
        answers_router
    )

    app.include_router(
        documents_router
    )

    return app


app = create_app()