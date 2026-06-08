from abc import ABC, abstractmethod
from typing import Generator


class BaseLLM(ABC):
    """
    Abstract base class for all LLM adapters.
    Every LLM (Gemini, Ollama, OpenAI) must implement these methods.
    Same interface = swap LLM via config only, no code change.
    """

    @abstractmethod
    def generate(self, question: str, context_chunks: list[dict]) -> dict:
        """
        Generate a full answer from question + retrieved chunks.
        Returns complete answer at once.

        Returns dict:
            {
                "answer":  "Refunds take 5 business days...",
                "sources": ["refund-policy.md", "faq.md"]
            }
        """
        pass

    @abstractmethod
    def generate_stream(self, question: str, context_chunks: list[dict]) -> Generator:
        """
        Stream answer token by token.

        Yields:
            str tokens as they arrive from the LLM.

        Sources are NOT yielded — caller should get them via
        _extract_sources() before starting the stream.
        """
        pass

    def _build_prompt(self, question: str, context_chunks: list[dict]) -> str:
        context = "\n\n".join(
            f"[Source: {chunk['source']}]\n{chunk['text']}"
            for chunk in context_chunks
        )

        return f"""You are a helpful assistant. Answer the user's question using ONLY the context provided below.
If the answer is not found in the context, say exactly: "I don't have that information in my docs."
Do not make up information. Do not use any knowledge outside the context.

Context:
---------
{context}
---------

Question: {question}
Answer:"""

    def _extract_sources(self, context_chunks: list[dict]) -> list[str]:
        seen = set()
        sources = []
        for chunk in context_chunks:
            src = chunk["source"]
            if src not in seen:
                seen.add(src)
                sources.append(src)
        return sources