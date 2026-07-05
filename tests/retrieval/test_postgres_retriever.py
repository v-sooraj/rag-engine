from unittest.mock import Mock
from uuid import uuid4

import pytest

from rag_engine.retrieval.postgres_retriever import (
    PostgresRetriever,
)


def create_mock_connection():
    connection = Mock()
    cursor = Mock()

    connection.__enter__ = Mock(
        return_value=connection,
    )
    connection.__exit__ = Mock(
        return_value=False,
    )

    cursor.__enter__ = Mock(
        return_value=cursor,
    )
    cursor.__exit__ = Mock(
        return_value=False,
    )

    connection.cursor.return_value = cursor

    return connection, cursor


def test_retrieve_rejects_invalid_embedding_dimension_before_opening_connection():
    connection_factory = Mock()

    retriever = PostgresRetriever(
        connection_factory=connection_factory,
    )

    with pytest.raises(
        ValueError,
        match="Expected query embedding dimension 384, got 3",
    ):
        retriever.retrieve(
            query_embedding=[
                0.1,
                0.2,
                0.3,
            ],
            top_k=3,
        )

    connection_factory.assert_not_called()


def test_retrieve_rejects_zero_top_k_before_opening_connection():
    connection_factory = Mock()

    retriever = PostgresRetriever(
        connection_factory=connection_factory,
    )

    with pytest.raises(
        ValueError,
        match="top_k must be greater than 0",
    ):
        retriever.retrieve(
            query_embedding=[0.1] * 384,
            top_k=0,
        )

    connection_factory.assert_not_called()


def test_retrieve_rejects_negative_top_k_before_opening_connection():
    connection_factory = Mock()

    retriever = PostgresRetriever(
        connection_factory=connection_factory,
    )

    with pytest.raises(
        ValueError,
        match="top_k must be greater than 0",
    ):
        retriever.retrieve(
            query_embedding=[0.1] * 384,
            top_k=-1,
        )

    connection_factory.assert_not_called()


def test_retrieve_returns_ranked_chunks():
    first_chunk_id = uuid4()
    first_document_id = uuid4()

    second_chunk_id = uuid4()
    second_document_id = uuid4()

    connection, cursor = create_mock_connection()

    cursor.fetchall.return_value = [
        (
            first_chunk_id,
            first_document_id,
            "Most relevant chunk",
            0,
            0.08,
        ),
        (
            second_chunk_id,
            second_document_id,
            "Second most relevant chunk",
            1,
            0.21,
        ),
    ]

    connection_factory = Mock(
        return_value=connection,
    )

    retriever = PostgresRetriever(
        connection_factory=connection_factory,
    )

    results = retriever.retrieve(
        query_embedding=[0.1] * 384,
        top_k=2,
    )

    assert len(results) == 2

    assert results[0].chunk_id == first_chunk_id
    assert (
        results[0].document_id
        == first_document_id
    )
    assert (
        results[0].content
        == "Most relevant chunk"
    )
    assert results[0].chunk_index == 0
    assert results[0].distance == 0.08

    assert results[1].chunk_id == second_chunk_id
    assert (
        results[1].document_id
        == second_document_id
    )
    assert (
        results[1].content
        == "Second most relevant chunk"
    )
    assert results[1].chunk_index == 1
    assert results[1].distance == 0.21

    connection_factory.assert_called_once()
    connection.cursor.assert_called_once()
    cursor.execute.assert_called_once()

    query_params = cursor.execute.call_args.args[1]

    assert query_params[0] == query_params[1]
    assert query_params[2] == 2


def test_retrieve_returns_empty_list_when_no_chunks_match():
    connection, cursor = create_mock_connection()

    cursor.fetchall.return_value = []

    connection_factory = Mock(
        return_value=connection,
    )

    retriever = PostgresRetriever(
        connection_factory=connection_factory,
    )

    results = retriever.retrieve(
        query_embedding=[0.1] * 384,
        top_k=3,
    )

    assert results == []