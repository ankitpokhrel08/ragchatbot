from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Abstract base class for all LLM adapters.
    Every LLM (Gemini, Ollama, OpenAI) must implement these methods.
    Same interface = swap LLM via config only, no code change.
    """

    @abstractmethod
    def generate(self, question: str, context_chunks: list[dict]) -> dict:
        """
        Generate an answer from question + retrieved chunks.

        Args:
            question:       user's raw question string
            context_chunks: list of dicts from store.query_chunks()
                            each dict has keys: text, source, score

        Returns dict:
            {
                "answer":  "Refunds take 5 business days...",
                "sources": ["refund-policy.md", "faq.md"]
            }
        """
        pass

    def _build_prompt(self, question: str, context_chunks: list[dict]) -> str:
        """
        Build the RAG prompt template.
        Shared across all LLM adapters — lives in base class.
        """
        # Extract chunk texts and join
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
        """
        Extract unique source filenames from retrieved chunks.
        Deduplicates — same file can appear multiple times in top-K.
        """
        seen = set()
        sources = []
        for chunk in context_chunks:
            src = chunk["source"]
            if src not in seen:
                seen.add(src)
                sources.append(src)
        return sources