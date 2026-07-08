import shutil
import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from rag_engine.ingestion_pipeline.ingestion_pipeline import (
    IngestionPipeline,
)


class DocumentUploadAdapter:

    def __init__(
        self,
        ingestion_pipeline: IngestionPipeline,
    ):
        self._ingestion_pipeline = ingestion_pipeline

    def ingest(
        self,
        file: UploadFile,
    ) -> UUID:
        with tempfile.TemporaryDirectory() as directory:
            temporary_path = (
                Path(directory)
                / Path(file.filename).name
            )

            with temporary_path.open("wb") as temporary_file:
                shutil.copyfileobj(
                    file.file,
                    temporary_file,
                )

            return self._ingestion_pipeline.ingest(
                str(temporary_path)
            )