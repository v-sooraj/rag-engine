from typing import Any

import httpx

from rag_engine.llm.generated_answer import GeneratedAnswer
from rag_engine.llm.llm import LLM
from rag_engine.llm.llm_generation_error import LLMGenerationError
from rag_engine.prompt_augmentation.augmented_prompt import AugmentedPrompt


class OllamaLLM(LLM):

    def __init__(
        self,
        base_url: str,
        model_name: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._client = client

    def generate(
        self,
        prompt: AugmentedPrompt,
    ) -> GeneratedAnswer:
        payload = self._build_payload(prompt)

        try:
            response = self._post(payload)

            response.raise_for_status()

            response_body = response.json()

            content = self._extract_content(
                response_body
            )

            return GeneratedAnswer(
                content=content
            )

        except (
            httpx.HTTPError,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            raise LLMGenerationError(
                "failed to generate answer"
            ) from error

    def _build_payload(
        self,
        prompt: AugmentedPrompt,
    ) -> dict[str, Any]:
        return {
            "model": self._model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        prompt.system_instruction
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_user_message(
                        prompt
                    ),
                },
            ],
            "stream": False,
        }

    def _build_user_message(
        self,
        prompt: AugmentedPrompt,
    ) -> str:
        return (
            f"Context:\n"
            f"{prompt.context}\n\n"
            f"Question:\n"
            f"{prompt.question}"
        )

    def _post(
        self,
        payload: dict[str, Any],
    ) -> httpx.Response:
        if self._client is not None:
            return self._client.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=self._timeout_seconds,
            )

        with httpx.Client() as client:
            return client.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=self._timeout_seconds,
            )

    def _extract_content(
        self,
        response_body: dict[str, Any],
    ) -> str:
        content = response_body["message"]["content"]

        if not isinstance(content, str):
            raise TypeError(
                "generated content must be a string"
            )

        if not content.strip():
            raise ValueError(
                "generated content must not be empty"
            )

        return content