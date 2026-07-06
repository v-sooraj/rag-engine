import pytest
from pydantic import ValidationError

from rag_engine.llm.generated_answer import GeneratedAnswer


def test_generated_answer_is_created_with_valid_content():
    answer = GeneratedAnswer(
        content="Vector databases store embeddings."
    )

    assert (
        answer.content
        == "Vector databases store embeddings."
    )


def test_generated_answer_rejects_empty_content():
    with pytest.raises(ValidationError):
        GeneratedAnswer(
            content=""
        )


def test_generated_answer_is_immutable():
    answer = GeneratedAnswer(
        content="Original answer"
    )

    with pytest.raises(ValidationError):
        answer.content = "Changed answer"