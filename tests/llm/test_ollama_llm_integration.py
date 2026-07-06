from rag_engine.config.settings import settings
from rag_engine.llm.ollama_llm import OllamaLLM
from rag_engine.prompt_augmentation.augmented_prompt import AugmentedPrompt


"""
Given: a running Ollama server with the configured model available
When: a structured augmented prompt is sent to Ollama
Then: a non-empty generated answer is returned
"""
def test_real_ollama_generation():
    llm = OllamaLLM(
        base_url=settings.ollama.base_url,
        model_name=settings.ollama.model_name,
        timeout_seconds=settings.ollama.timeout_seconds,
    )

    prompt = AugmentedPrompt(
        system_instruction=(
            "Answer the question using only the provided context. "
            "If the context does not contain enough information to "
            "answer the question, say that you do not have enough "
            "information."
        ),
        context=(
            "[CONTEXT 1]\n"
            "Vector databases store numerical embeddings and support "
            "similarity search."
        ),
        question=(
            "What do vector databases store?"
        ),
    )

    answer = llm.generate(prompt)

    assert answer.content
    assert answer.content.strip()