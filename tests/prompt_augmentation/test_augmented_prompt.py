import pytest
from pydantic import ValidationError

from rag_engine.prompt_augmentation.augmented_prompt import AugmentedPrompt


def test_augmented_prompt_is_created_with_valid_values():
    prompt = AugmentedPrompt(
        system_instruction="Use only the provided context.",
        context="Vector databases store embeddings.",
        question="What do vector databases store?",
    )

    assert (
        prompt.system_instruction
        == "Use only the provided context."
    )
    assert (
        prompt.context
        == "Vector databases store embeddings."
    )
    assert (
        prompt.question
        == "What do vector databases store?"
    )


def test_augmented_prompt_allows_empty_context():
    prompt = AugmentedPrompt(
        system_instruction="Use only the provided context.",
        context="",
        question="What is RAG?",
    )

    assert prompt.context == ""


def test_augmented_prompt_rejects_empty_system_instruction():
    with pytest.raises(ValidationError):
        AugmentedPrompt(
            system_instruction="",
            context="Some context",
            question="Some question",
        )


def test_augmented_prompt_rejects_empty_question():
    with pytest.raises(ValidationError):
        AugmentedPrompt(
            system_instruction="Some instruction",
            context="Some context",
            question="",
        )


def test_augmented_prompt_is_immutable():
    prompt = AugmentedPrompt(
        system_instruction="Use only the provided context.",
        context="Some context",
        question="Some question",
    )

    with pytest.raises(ValidationError):
        prompt.context = "Changed context"