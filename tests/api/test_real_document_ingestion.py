from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from rag_engine.api.app import create_app
from rag_engine.database.connection import (
    create_connection,
)


PDF_PATH = Path(
    "tests/resources/sample.pdf"
)


def delete_test_document(
    document_id: UUID,
) -> None:
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )


def test_real_document_ingestion_through_http():
    app = create_app()

    document_id: UUID | None = None

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as client:
        with PDF_PATH.open("rb") as pdf_file:
            response = client.post(
                "/documents",
                files={
                    "file": (
                        PDF_PATH.name,
                        pdf_file,
                        "application/pdf",
                    ),
                },
            )

        assert response.status_code == 201

        response_body = response.json()

        document_id = UUID(
            response_body["document_id"]
        )

        try:
            with create_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            filename,
                            page_count
                        FROM documents
                        WHERE id = %s
                        """,
                        (document_id,),
                    )

                    stored_document = (
                        cursor.fetchone()
                    )

                    assert (
                        stored_document
                        is not None
                    )

                    assert (
                        stored_document[0]
                        == "sample.pdf"
                    )

                    assert (
                        stored_document[1]
                        > 1
                    )

                    cursor.execute(
                        """
                        SELECT
                            chunk_index,
                            content,
                            vector_dims(embedding)
                        FROM chunks
                        WHERE document_id = %s
                        ORDER BY chunk_index
                        """,
                        (document_id,),
                    )

                    stored_chunks = (
                        cursor.fetchall()
                    )

                    assert len(
                        stored_chunks
                    ) > 1

                    assert [
                        chunk[0]
                        for chunk in stored_chunks
                    ] == list(
                        range(
                            len(stored_chunks)
                        )
                    )

                    assert all(
                        chunk[1].strip()
                        for chunk in stored_chunks
                    )

                    assert all(
                        chunk[2] == 384
                        for chunk in stored_chunks
                    )

        finally:
            delete_test_document(
                document_id
            )