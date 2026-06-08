import os
from ragchatbot.parser import parse_file
from ragchatbot.chunker import chunk_text
from ragchatbot.embedder import embed_chunks, embed_query
from ragchatbot.store import (
    hash_file,
    is_file_indexed,
    add_chunks,
    query_chunks,
    collection_stats,
    delete_file_chunks,
    get_indexed_files
)


class RAG:
    """
    Main ragchatbot interface.

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
        if llm == "gemini":
            from ragchatbot.llm.gemini import GeminiLLM
            return GeminiLLM(**kwargs)
        elif llm == "ollama":
            from ragchatbot.llm.ollama import OllamaLLM
            return OllamaLLM(**kwargs)
        elif llm == "openai":
            from ragchatbot.llm.openai import OpenAILLM
            return OpenAILLM(**kwargs)
        else:
            raise ValueError(
                f"❌ Unknown LLM: '{llm}'\n"
                f"   Supported: gemini, openai, ollama"
            )

    def index(self) -> None:
        """Index all .md, .txt, .pdf files. Skips unchanged. Deletes stale."""

        # guard: docs folder must exist
        if not os.path.exists(self.docs):
            raise FileNotFoundError(
                f"❌ Docs folder not found: '{self.docs}'\n"
                f"   Create it and add your files, or set RAGCHATBOT_DOCS in .env"
            )

        current_files = {
            f for f in os.listdir(self.docs)
            if f.endswith((".md", ".txt", ".pdf",".docx"))
        }

        # guard: at least one doc
        if not current_files:
            raise ValueError(
                f"❌ No docs found in '{self.docs}'\n"
                f"   Add .md, .txt, or .pdf files and try again."
            )

        from ragchatbot.store import get_indexed_files
        indexed_files = get_indexed_files(self.db_path)
        stale_files = indexed_files - current_files

        for filename in stale_files:
            filepath = os.path.join(self.docs, filename)
            delete_file_chunks(filepath, self.db_path)
            print(f"Deleted stale chunks for {filename}")

        for filename in current_files:
            filepath = os.path.join(self.docs, filename)
            file_hash = hash_file(filepath)

            if is_file_indexed(filepath, file_hash, self.db_path):
                print(f"Skipping {filename} — unchanged")
                continue

            print(f"Indexing {filename}...")
            try:
                text = parse_file(filepath)
                chunks = chunk_text(text)
                embeddings = embed_chunks(chunks)
                add_chunks(filepath, chunks, embeddings, file_hash, self.db_path)
            except Exception as e:
                print(f"⚠️  Skipping {filename} — {str(e)}")
                continue

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
            "ragchatbot.server:app",
            host=host,
            port=port,
            reload=reload
        )