from unittest.mock import Mock

import httpx
import pytest

from rag_engine.llm.llm_generation_error import LLMGenerationError
from rag_engine.llm.ollama_llm import OllamaLLM
from rag_engine.prompt_augmentation.augmented_prompt import AugmentedPrompt


BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen3:4b"
TIMEOUT_SECONDS = 120.0


def create_prompt() -> AugmentedPrompt:
    return AugmentedPrompt(
        system_instruction=(
            "Answer using only the provided context."
        ),
        context=(
            "[CONTEXT 1]\n"
            "Vector databases store embeddings."
        ),
        question=(
            "What do vector databases store?"
        ),
    )


def create_llm(
    client: Mock,
) -> OllamaLLM:
    return OllamaLLM(
        base_url=BASE_URL,
        model_name=MODEL_NAME,
        timeout_seconds=TIMEOUT_SECONDS,
        client=client,
    )


def create_success_response(
    content: str = (
        "Vector databases store embeddings."
    ),
) -> Mock:
    response = Mock(spec=httpx.Response)

    response.raise_for_status.return_value = None

    response.json.return_value = {
        "message": {
            "role": "assistant",
            "content": content,
        }
    }

    return response


def test_generate_returns_generated_answer():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response()
    )

    llm = create_llm(client)

    answer = llm.generate(
        create_prompt()
    )

    assert (
        answer.content
        == "Vector databases store embeddings."
    )


def test_generate_maps_system_instruction_to_system_message():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response()
    )

    llm = create_llm(client)
    prompt = create_prompt()

    llm.generate(prompt)

    payload = client.post.call_args.kwargs["json"]

    assert payload["messages"][0] == {
        "role": "system",
        "content": prompt.system_instruction,
    }


def test_generate_maps_context_and_question_to_user_message():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response()
    )

    llm = create_llm(client)
    prompt = create_prompt()

    llm.generate(prompt)

    payload = client.post.call_args.kwargs["json"]

    assert payload["messages"][1] == {
        "role": "user",
        "content": (
            "Context:\n"
            "[CONTEXT 1]\n"
            "Vector databases store embeddings.\n\n"
            "Question:\n"
            "What do vector databases store?"
        ),
    }


def test_generate_uses_configured_model():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response()
    )

    llm = create_llm(client)

    llm.generate(
        create_prompt()
    )

    payload = client.post.call_args.kwargs["json"]

    assert payload["model"] == MODEL_NAME


def test_generate_disables_streaming():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response()
    )

    llm = create_llm(client)

    llm.generate(
        create_prompt()
    )

    payload = client.post.call_args.kwargs["json"]

    assert payload["stream"] is False


def test_generate_calls_ollama_chat_endpoint():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response()
    )

    llm = create_llm(client)

    llm.generate(
        create_prompt()
    )

    client.post.assert_called_once()

    assert (
        client.post.call_args.args[0]
        == "http://localhost:11434/api/chat"
    )


def test_generate_uses_configured_timeout():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response()
    )

    llm = create_llm(client)

    llm.generate(
        create_prompt()
    )

    assert (
        client.post.call_args.kwargs["timeout"]
        == TIMEOUT_SECONDS
    )


def test_generate_removes_trailing_slash_from_base_url():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response()
    )

    llm = OllamaLLM(
        base_url="http://localhost:11434/",
        model_name=MODEL_NAME,
        timeout_seconds=TIMEOUT_SECONDS,
        client=client,
    )

    llm.generate(
        create_prompt()
    )

    assert (
        client.post.call_args.args[0]
        == "http://localhost:11434/api/chat"
    )


def test_generate_translates_connection_failure():
    client = Mock(spec=httpx.Client)

    client.post.side_effect = httpx.ConnectError(
        "connection failed"
    )

    llm = create_llm(client)

    with pytest.raises(
        LLMGenerationError,
        match="failed to generate answer",
    ) as exception_info:
        llm.generate(
            create_prompt()
        )

    assert isinstance(
        exception_info.value.__cause__,
        httpx.ConnectError,
    )


def test_generate_translates_timeout():
    client = Mock(spec=httpx.Client)

    client.post.side_effect = httpx.ReadTimeout(
        "request timed out"
    )

    llm = create_llm(client)

    with pytest.raises(
        LLMGenerationError,
        match="failed to generate answer",
    ) as exception_info:
        llm.generate(
            create_prompt()
        )

    assert isinstance(
        exception_info.value.__cause__,
        httpx.ReadTimeout,
    )


def test_generate_translates_http_error():
    client = Mock(spec=httpx.Client)

    response = Mock(spec=httpx.Response)

    response.raise_for_status.side_effect = (
        httpx.HTTPStatusError(
            "server error",
            request=Mock(
                spec=httpx.Request
            ),
            response=response,
        )
    )

    client.post.return_value = response

    llm = create_llm(client)

    with pytest.raises(
        LLMGenerationError,
        match="failed to generate answer",
    ):
        llm.generate(
            create_prompt()
        )


def test_generate_rejects_missing_message():
    client = Mock(spec=httpx.Client)

    response = Mock(spec=httpx.Response)

    response.raise_for_status.return_value = None

    response.json.return_value = {}

    client.post.return_value = response

    llm = create_llm(client)

    with pytest.raises(
        LLMGenerationError,
        match="failed to generate answer",
    ):
        llm.generate(
            create_prompt()
        )


def test_generate_rejects_missing_content():
    client = Mock(spec=httpx.Client)

    response = Mock(spec=httpx.Response)

    response.raise_for_status.return_value = None

    response.json.return_value = {
        "message": {}
    }

    client.post.return_value = response

    llm = create_llm(client)

    with pytest.raises(
        LLMGenerationError,
        match="failed to generate answer",
    ):
        llm.generate(
            create_prompt()
        )


def test_generate_rejects_non_string_content():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response(
            content=123
        )
    )

    llm = create_llm(client)

    with pytest.raises(
        LLMGenerationError,
        match="failed to generate answer",
    ):
        llm.generate(
            create_prompt()
        )


def test_generate_rejects_empty_content():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response(
            content=""
        )
    )

    llm = create_llm(client)

    with pytest.raises(
        LLMGenerationError,
        match="failed to generate answer",
    ):
        llm.generate(
            create_prompt()
        )


def test_generate_rejects_blank_content():
    client = Mock(spec=httpx.Client)

    client.post.return_value = (
        create_success_response(
            content="   "
        )
    )

    llm = create_llm(client)

    with pytest.raises(
        LLMGenerationError,
        match="failed to generate answer",
    ):
        llm.generate(
            create_prompt()
        )