import os
from quickrag.parser import parse_file
from quickrag.chunker import chunk_text
from quickrag.embedder import embed_chunks, embed_query
from quickrag.store import (
    hash_file,
    is_file_indexed,
    add_chunks,
    query_chunks,
    collection_stats
)


class RAG:
    """
    Main quickrag interface.

    Usage with Gemini:
        rag = RAG(docs="./docs", llm="gemini")
        rag.index()
        result = rag.ask("how long does a refund take?")

    Usage with Ollama:
        rag = RAG(docs="./docs", llm="ollama")
        rag.index()
        result = rag.ask("how long does a refund take?")
    """

    def __init__(
        self,
        docs: str = "./docs",
        db_path: str = "./chroma_db",
        llm: str = "gemini",
        n_results: int = 3,
        **llm_kwargs
    ):
        self.docs = docs
        self.db_path = db_path
        self.n_results = n_results
        self.llm = self._load_llm(llm, **llm_kwargs)

    def _load_llm(self, llm: str, **kwargs):
        """
        Load LLM adapter by name.
        Lazy import — only imports what's needed.
        """
        if llm == "gemini":
            from quickrag.llm.gemini import GeminiLLM
            return GeminiLLM(**kwargs)

        elif llm == "ollama":
            from quickrag.llm.ollama import OllamaLLM
            return OllamaLLM(**kwargs)

        else:
            raise ValueError(
                f"Unknown LLM: '{llm}'. "
                f"Supported: 'gemini', 'ollama'"
            )

    def index(self) -> None:
        """Index all .md and .txt files. Skips unchanged files."""
        print(f"Indexing {self.docs}...")

        for filename in os.listdir(self.docs):
            if not filename.endswith((".md", ".txt")):
                continue

            filepath = os.path.join(self.docs, filename)
            file_hash = hash_file(filepath)

            if is_file_indexed(filepath, file_hash, self.db_path):
                print(f"Skipping {filename} — unchanged")
                continue

            print(f"Indexing {filename}...")
            text = parse_file(filepath)
            chunks = chunk_text(text)
            embeddings = embed_chunks(chunks)
            add_chunks(filepath, chunks, embeddings, file_hash, self.db_path)

        print("Indexing complete.")

    def ask(self, question: str) -> dict:
        """
        Ask a question. Returns answer + sources.

        Returns:
            {
                "answer":  "Refunds take 5 business days...",
                "sources": ["refund-policy.md"]
            }
        """
        query_vector = embed_query(question)
        chunks = query_chunks(query_vector, self.n_results, self.db_path)
        return self.llm.generate(question, chunks)
    
    def serve(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
        """Start FastAPI server."""
        import uvicorn
        uvicorn.run(
            "quickrag.server:app",
            host=host,
            port=port,
            reload=reload
        )